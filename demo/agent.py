"""DentalOS Voice Agent — Démo J2 : flow 6 étapes complet.

Implémente le Scope V1 (CLAUDE.md) avec la config de docs/demo-stack.md § 5.3.
2 function tools : verify_patient_identity, complete_call.
"""

import json
import logging
import os
import uuid

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    AgentServer,
    JobContext,
    JobProcess,
    RunContext,
    TurnHandlingOptions,
    cli,
    inference,
    room_io,
    text_transforms,
)
from livekit.agents.llm import function_tool
from livekit.plugins import silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from mock_backend import verify_patient_identity as _verify_patient
from tools import CallOutcome, log_call_outcome, log_slot

load_dotenv()

logger = logging.getLogger("dental-agent")
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# Config démo — valeurs hardcodées, remplacées par dispatch metadata en prod
# ---------------------------------------------------------------------------
NOM_CABINET = "Cabinet Dentaire des Lilas"
PRATICIEN = "Dr Martin"
CATEGORIE = "orthodontie"
DATE_DEVIS = "le quinze avril"
DEVIS_ID = os.getenv("DEVIS_ID", "1")

# ---------------------------------------------------------------------------
# System prompt — 5 sections (Vapi Ch. 12)
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = f"""\
# IDENTITY

Tu es l'assistant vocal du {NOM_CABINET}. Tu appelles un patient au sujet \
d'un devis dentaire. Tu ne donnes jamais ton nom — tu représentes le cabinet.

# STYLE

- Français, ton calme, posé et professionnel.
- Deux phrases maximum par tour. Pas de monologue.
- Pas de markdown, pas de listes, pas d'emoji, pas de JSON.
- Épelle les chiffres en lettres (quinze, vingt-deux, soixante-dix-huit).
- Accusé réception immédiat après chaque réponse patient avec le contenu de \
la réponse (pas juste "ok").
- Ne répète jamais la catégorie de traitement ni le nom du praticien après \
l'annonce initiale.

# TASK

Tu suis un flow en six étapes, dans l'ordre strict. Ne saute aucune étape. \
Ne reviens pas en arrière.

## Étape 1 — Annonce
Dis exactement :
"Bonjour, je vous appelle de la part du {NOM_CABINET}. Cet appel est \
enregistré. Vous avez reçu {DATE_DEVIS} un devis du Docteur Martin pour \
un traitement d'{CATEGORIE}."
Attends la réponse du patient.

## ��tape 2 — Vérification d'identité
Dis : "Pour des raisons de sécurité, pourriez-vous me confirmer votre nom, \
prénom et date de naissance ? Pour la date, donnez-moi le jour, le mois et \
l'année, s'il vous plaît."
Quand le patient répond, appelle verify_patient_identity.
- match → "Merci, votre identité est confirmée." Passe à l'étape 3.
- no_match, 1ère tentative → "Les informations ne correspondent pas. \
Pourriez-vous réessayer ?"
- no_match, 2ème tentative → "Je suis désolé, je ne parviens pas à vérifier \
votre identité. Le cabinet vous recontactera directement. Bonne journée." \
Appelle complete_call avec escalade_motif="echec_identite". Fin.
JAMAIS relire la date de naissance à voix haute.

## Étape 3 — Question mutuelle
"Avez-vous eu un retour de votre mutuelle concernant ce devis ?"
Classe en : oui / non / ne_sait_pas.
Exemples de confirmation progressive :
- Si "non" : "D'accord, vous n'avez pas encore eu de retour de votre mutuelle."
- Si "oui" : "Très bien, vous avez eu un retour de votre mutuelle."
- Si "je ne sais pas" : "D'accord, vous n'êtes pas sûr pour le moment."

## Étape 4 — Question intention
"Souhaitez-vous procéder au traitement ?"
Classe en : oui / non / reflechit.
Exemples de confirmation progressive :
- Si "oui" : "Très bien, vous souhaitez procéder au traitement."
- Si "non" : "D'accord, vous ne souhaitez pas procéder pour le moment."
- Si "je réfléchis" : "D'accord, vous prenez encore le temps de réfléchir."
Si oui → étape 5. Sinon → ��tape 6.

## Étape 5 — Disponibilités (si intention = oui uniquement)
"Quelles sont vos disponibilités pour un rendez-vous ?"
Note un à trois créneaux (texte libre). Confirmation : "J'ai noté : [relire \
les créneaux exacts donnés par le patient]."

## Étape 6 — Clôture
Appelle complete_call avec toutes les données collectées.
Puis fais un récap concret adapté aux slots collectés. Exemple si mutuelle=non, \
intention=oui, disponibilites="mardi matin ou jeudi après-midi" :
"Pour résumer, vous n'avez pas encore eu de retour de votre mutuelle, vous \
souhaitez procéder au traitement, et vous êtes disponible mardi matin ou jeudi \
après-midi. Le cabinet vous recontactera pour finaliser."
Adapte selon les slots réels. Si intention = non ou reflechit, ne mentionne pas \
les disponibilités.
Termine par : "Merci pour votre temps et bonne journée."

# GUARDRAILS

S'appliquent à CHAQUE tour, sans exception.

Interdictions absolues :
- Conseil médical, diagnostic, recommandation de médicament, interprétation \
de symptôme, dire qu'un symptôme est "normal".
- Estimation de remboursement mutuelle.
- Conseil sur l'opportunité du traitement.
- Pression commerciale.
- Lecture du contenu détaillé du devis (actes, montants).
- Extrapolation à partir de la catégorie ou du praticien.
- Négociation tarifaire.

Urgence vitale (difficulté à respirer/avaler, saignement important, perte de \
connaissance, fièvre avec gonflement, douleur insupportable) :
→ "Si vous êtes en situation d'urgence, veuillez appeler le quinze ou le \
cent-douze immédiatement."
→ Appelle complete_call avec escalade_motif="urgence_vitale". Fin.

Demande d'humain :
→ "Je comprends. Le cabinet va vous recontacter directement."
→ Appelle complete_call avec escalade_motif="demande_humain". Fin.

Question hors flow :
→ Reconnaître brièvement ("Je comprends votre question.").
→ Ne pas répondre au fond.
→ "Le cabinet pourra vous répondre à ce sujet."
→ Reprends en posant à nouveau la question de l'étape en cours, sans répéter \
le contexte précédent.

# TOOLS

## verify_patient_identity
Étape 2. Paramètres : name (prénom), surname (nom de famille), dob (AAAA-MM-JJ).
Si date parlée ("le quatorze mars soixante-dix-huit") → convertir en ISO \
("1978-03-14"). Maximum 2 appels.

## complete_call
Étape 6 ou fin anticipée. Paramètres :
- mutuelle_status : oui / non / ne_sait_pas (défaut : non_collecte si non \
atteint)
- intention : oui / non / reflechit (défaut : non_collecte)
- disponibilites : texte libre / non_applicable (défaut : non_collecte)
- escalade_motif : aucun / echec_identite / urgence_vitale / demande_humain
Appeler UNE SEULE FOIS, juste avant le récap final ou le message de fin.
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
# Agent — flow 6 étapes
# ---------------------------------------------------------------------------
class DentalAgent(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)
        self.call_id: str = str(uuid.uuid4())
        self.identity_verified: bool = False
        self.identity_attempts: int = 0
        self.mutuelle_status: str = "non_collecte"
        self.intention: str = "non_collecte"
        self.disponibilites: str = "non_collecte"
        self.escalade_motif: str = "aucun"

    async def on_enter(self) -> None:
        logger.info(
            json.dumps(
                {"event": "call_started", "call_id": self.call_id, "devis_id": DEVIS_ID},
                ensure_ascii=False,
            )
        )
        # Étape 1 — annonce intégrale, non-interruptible (§ 5.B)
        await self.session.generate_reply(allow_interruptions=False)

    @function_tool()
    async def verify_patient_identity(
        self,
        _context: RunContext,
        name: str,
        surname: str,
        dob: str,
    ) -> dict:
        """V��rifie l'identité du patient auprès du backend.

        Args:
            name: Prénom du patient.
            surname: Nom de famille du patient.
            dob: Date de naissance au format AAAA-MM-JJ.
        """
        self.identity_attempts += 1
        result = await _verify_patient(
            name=name, surname=surname, dob=dob, devis_id=DEVIS_ID,
        )
        if result.get("match"):
            self.identity_verified = True
        log_slot(
            call_id=self.call_id,
            slot_name="identity_verification",
            value={"attempt": self.identity_attempts, "match": result.get("match", False)},
        )
        return result

    @function_tool()
    async def complete_call(
        self,
        _context: RunContext,
        mutuelle_status: str = "non_collecte",
        intention: str = "non_collecte",
        disponibilites: str = "non_collecte",
        escalade_motif: str = "aucun",
    ) -> dict:
        """Enregistre le bilan de l'appel. Appeler une seule fois en fin de flow.

        Args:
            mutuelle_status: Statut retour mutuelle : oui, non, ne_sait_pas, ou non_collecte.
            intention: Intention de traitement : oui, non, reflechit, ou non_collecte.
            disponibilites: Disponibilités patient (texte libre), non_applicable, ou non_collecte.
            escalade_motif: Motif d'escalade : aucun, echec_identite, urgence_vitale, ou demande_humain.
        """
        self.mutuelle_status = mutuelle_status
        self.intention = intention
        self.disponibilites = disponibilites
        self.escalade_motif = escalade_motif

        outcome = CallOutcome(
            call_id=self.call_id,
            devis_id=DEVIS_ID,
            identity_verified=self.identity_verified,
            identity_attempts=self.identity_attempts,
            mutuelle_status=mutuelle_status,
            intention=intention,
            disponibilites=disponibilites,
            escalade_motif=escalade_motif,
        )
        log_call_outcome(outcome)
        return {"status": "recorded"}


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
            voice="faa75703-00e3-4a57-9955-0703001e3231",  # Voice ID auditionnée
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
