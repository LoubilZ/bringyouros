"""DentalOS Voice Agent — Démo J1 : annonce seule.

Implémente la config de docs/demo-stack.md § 5.3.
Objectif : joindre une room, dire l'annonce intégrale, écouter une réponse, la loguer.
"""

import logging

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    AgentServer,
    JobContext,
    JobProcess,
    TurnHandlingOptions,
    cli,
    inference,
    room_io,
    text_transforms,
)
from livekit.plugins import silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

load_dotenv()

logger = logging.getLogger("dental-agent")
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# Mocks J1 — valeurs hardcodées, remplacées par le backend en J2+
# ---------------------------------------------------------------------------
NOM_CABINET = "Cabinet Dentaire des Lilas"
PRATICIEN = "Dr Martin"
CATEGORIE = "orthodontie"
DATE_DEVIS = "le quinze avril"

# ---------------------------------------------------------------------------
# System prompt — annonce uniquement (J1)
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = f"""\
Tu es l'assistant vocal du {NOM_CABINET}.

Règles absolues :
- Parle en français, ton calme et professionnel.
- Réponses courtes : deux phrases maximum.
- Pas de markdown, pas de listes, pas d'emoji. Épelle les chiffres en lettres.
- Tu ne donnes aucun conseil médical ni estimation de remboursement.
- Si le patient pose une question, redirige-le vers le cabinet.

Ta première prise de parole doit être exactement :
« Bonjour, je vous appelle de la part du {NOM_CABINET}. \
Cet appel est enregistré. \
Vous avez reçu {DATE_DEVIS} un devis du Docteur Martin \
pour un traitement d'{CATEGORIE}. »

Après cette annonce, écoute la réponse du patient et accuse réception brièvement.
"""

# ---------------------------------------------------------------------------
# Server + prewarm
# ---------------------------------------------------------------------------
server = AgentServer()


def prewarm(proc: JobProcess) -> None:
    proc.userdata["vad"] = silero.VAD.load(
        activation_threshold=0.5,
        min_silence_duration=0.6,
        min_speech_duration=0.05,
        prefix_padding_duration=0.5,
        sample_rate=16000,
    )


server.setup_fnc = prewarm


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------
class DentalAgent(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)

    async def on_enter(self) -> None:
        # Annonce intégrale, non-interruptible (§ 5.B — allow_interruptions)
        await self.session.generate_reply(allow_interruptions=False)


# ---------------------------------------------------------------------------
# Entrypoint — config § 5.3
# ---------------------------------------------------------------------------
@server.rtc_session()
async def entrypoint(ctx: JobContext) -> None:
    dental_replacements = text_transforms.replace(
        {"RDV": "rendez-vous", "Dr ": "Docteur ", "Dr.": "Docteur"},
        case_sensitive=False,
    )

    session = AgentSession(
        # --- STT (§ 1) ---
        stt=inference.STT(model="deepgram/nova-3-general", language="fr"),
        # --- LLM (§ 3) ---
        llm=inference.LLM(
            model="openai/gpt-4.1-mini",
            extra_kwargs={"temperature": 0.0},
        ),
        # --- TTS (§ 2) ---
        tts=inference.TTS(
            "cartesia/sonic-3",
            voice="a8a1eb38-5f15-4c1d-8722-7ac0f329727d",  # Calm French Woman
            language="fr",
        ),
        # --- VAD (§ 4) ---
        vad=ctx.proc.userdata["vad"],
        # --- Turn handling (§ 4 + § 5) ---
        turn_handling=TurnHandlingOptions(
            turn_detection=MultilingualModel(),
            endpointing={
                "mode": "dynamic",
                "min_delay": 0.7,
                "max_delay": 4.0,
                "alpha": 0.85,
            },
            interruption={
                "mode": "adaptive",
                "min_duration": 0.6,
                "min_words": 0,
                "resume_false_interruption": True,
                "false_interruption_timeout": 2.5,
            },
            preemptive_generation={
                "enabled": True,
                "preemptive_tts": False,
                "max_speech_duration": 10.0,
                "max_retries": 3,
            },
        ),
        # --- Text transforms (§ 5.A) ---
        tts_text_transforms=[
            "filter_emoji",
            "filter_markdown",
            dental_replacements,
        ],
        # --- Session params (§ 5) ---
        aec_warmup_duration=3.0,
        user_away_timeout=30.0,
        max_tool_steps=3,
    )

    await session.start(
        agent=DentalAgent(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=None,
                sample_rate=24000,
                num_channels=1,
            ),
            audio_output=room_io.AudioOutputOptions(
                sample_rate=24000,
                num_channels=1,
            ),
        ),
    )

    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
