"""DentalOS Calendar Backend — Mock V1.

Fournit les créneaux libres du praticien et permet de booker un RDV.
En V1 : données mock.
En V2 : connexion DB DentalOS réelle.
"""

import uuid
from datetime import date

# ---------------------------------------------------------------------------
# Mock agenda — créneaux types d'un cabinet dentaire
# ---------------------------------------------------------------------------
# Plages horaires du cabinet : lun-ven 9h-12h30 / 14h-18h30
# Créneaux standard : 30min (contrôle), 60min (soin), 90min (chirurgie)

_MOCK_SLOTS = [
    {"date": "2026-05-05", "heure": "09h00", "duree_min": 60},
    {"date": "2026-05-05", "heure": "14h00", "duree_min": 60},
    {"date": "2026-05-06", "heure": "10h00", "duree_min": 60},
    {"date": "2026-05-06", "heure": "15h30", "duree_min": 60},
    {"date": "2026-05-07", "heure": "09h30", "duree_min": 60},
    {"date": "2026-05-07", "heure": "14h30", "duree_min": 60},
    {"date": "2026-05-08", "heure": "11h00", "duree_min": 60},
    {"date": "2026-05-08", "heure": "16h00", "duree_min": 60},
    {"date": "2026-05-09", "heure": "09h00", "duree_min": 60},
    {"date": "2026-05-09", "heure": "14h00", "duree_min": 60},
    {"date": "2026-05-12", "heure": "10h00", "duree_min": 60},
    {"date": "2026-05-12", "heure": "15h00", "duree_min": 60},
    {"date": "2026-05-13", "heure": "09h00", "duree_min": 60},
    {"date": "2026-05-13", "heure": "14h30", "duree_min": 60},
    {"date": "2026-05-14", "heure": "11h00", "duree_min": 60},
    {"date": "2026-05-14", "heure": "16h30", "duree_min": 60},
]

# RDV bookés pendant la session (mock in-memory)
_BOOKED: list[dict] = []


async def check_calendar(
    praticien: str,
    date_debut: str,
    date_fin: str,
) -> dict:
    """Retourne les créneaux libres du praticien entre date_debut et date_fin."""
    try:
        d_debut = date.fromisoformat(date_debut)
        d_fin = date.fromisoformat(date_fin)
    except ValueError:
        return {"praticien": praticien, "creneaux": [], "erreur": "format_date_invalide"}

    # Exclure les créneaux déjà bookés
    booked_keys = {(b["date"], b["heure"]) for b in _BOOKED}
    creneaux = [
        slot for slot in _MOCK_SLOTS
        if d_debut <= date.fromisoformat(slot["date"]) <= d_fin
        and (slot["date"], slot["heure"]) not in booked_keys
    ]

    return {
        "praticien": praticien,
        "creneaux": creneaux[:5],
    }


async def create_rdv(
    praticien: str,
    patient_name: str,
    rdv_date: str,
    heure: str,
    motif: str = "",
    duree_min: int = 60,
) -> dict:
    """Crée un RDV dans l'agenda. Retourne la confirmation."""
    rdv_id = f"RDV-{uuid.uuid4().hex[:8].upper()}"
    rdv = {
        "rdv_id": rdv_id,
        "praticien": praticien,
        "patient_name": patient_name,
        "date": rdv_date,
        "heure": heure,
        "duree_min": duree_min,
        "motif": motif,
        "status": "confirmed",
    }
    _BOOKED.append(rdv)
    return rdv


async def cancel_rdv(rdv_id: str) -> dict:
    """Annule un RDV existant."""
    for rdv in _BOOKED:
        if rdv["rdv_id"] == rdv_id:
            rdv["status"] = "cancelled"
            return {"rdv_id": rdv_id, "status": "cancelled"}
    return {"rdv_id": rdv_id, "erreur": "rdv_non_trouve"}
