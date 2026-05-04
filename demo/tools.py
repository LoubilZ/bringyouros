"""Call outcome recording and structured logging — démo inbound RDV."""

import json
import logging
from dataclasses import asdict, dataclass

logger = logging.getLogger("dental-agent")


@dataclass
class CallOutcome:
    """Bilan structuré d'un appel de prise de RDV."""

    call_id: str
    patient_name: str = "inconnu"
    motif: str = "non_collecte"
    rdv_id: str = "aucun"
    rdv_date: str = "non_collecte"
    rdv_heure: str = "non_collecte"
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
    """Log le CallOutcome complet en JSON structuré."""
    logger.info(
        json.dumps(
            {"event": "call_outcome", **asdict(outcome)},
            ensure_ascii=False,
        )
    )
