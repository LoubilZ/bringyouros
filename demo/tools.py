"""Call outcome recording and structured logging — démo J2."""

import json
import logging
from dataclasses import asdict, dataclass

logger = logging.getLogger("dental-agent")


@dataclass
class CallOutcome:
    """Bilan structuré d'un appel de suivi de devis."""

    call_id: str
    devis_id: str
    identity_verified: bool
    identity_attempts: int
    mutuelle_status: str = "non_collecte"
    intention: str = "non_collecte"
    disponibilites: str = "non_collecte"
    escalade_motif: str = "aucun"


def log_slot(
    call_id: str,
    slot_name: str,
    value: str | bool | int | dict,
) -> None:
    """Log un slot capturé en JSON structuré."""
    logger.info(
        json.dumps(
            {
                "event": "slot_captured",
                "call_id": call_id,
                "slot": slot_name,
                "value": value,
            },
            ensure_ascii=False,
        )
    )


def log_call_outcome(outcome: CallOutcome) -> None:
    """Log le CallOutcome complet en JSON structur��."""
    logger.info(
        json.dumps(
            {"event": "call_outcome", **asdict(outcome)},
            ensure_ascii=False,
        )
    )
