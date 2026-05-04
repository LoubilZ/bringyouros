"""DentalOS Calendar Backend — Mock V1.

Fournit les créneaux libres du praticien pour une période donnée.
En V1 : données mock statiques.
En V2 : connexion DB DentalOS réelle.

Stubs pour les opérations futures (create, cancel, update) — non activés.
"""

from datetime import date, datetime, timedelta

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


async def check_calendar(
    praticien: str,
    date_debut: str,
    date_fin: str,
) -> dict:
    """Retourne les créneaux libres du praticien entre date_debut et date_fin.

    Args:
        praticien: Nom du praticien (ex: "Dr Martin").
        date_debut: Date de début au format AAAA-MM-JJ.
        date_fin: Date de fin au format AAAA-MM-JJ.

    Returns:
        Dict avec praticien et liste de créneaux disponibles.
    """
    try:
        d_debut = date.fromisoformat(date_debut)
        d_fin = date.fromisoformat(date_fin)
    except ValueError:
        return {"praticien": praticien, "creneaux": [], "erreur": "format_date_invalide"}

    creneaux = [
        slot for slot in _MOCK_SLOTS
        if d_debut <= date.fromisoformat(slot["date"]) <= d_fin
    ]

    return {
        "praticien": praticien,
        "creneaux": creneaux[:5],  # max 5 créneaux proposés
    }


# ---------------------------------------------------------------------------
# Stubs V2 — non activés, interface définie pour le mock
# ---------------------------------------------------------------------------

async def create_rdv(
    praticien: str,
    patient_id: str,
    rdv_date: str,
    heure: str,
    duree_min: int = 60,
    motif: str = "",
) -> dict:
    """Crée un RDV dans l'agenda. STUB — non implémenté."""
    raise NotImplementedError("create_rdv sera implémenté en V2")


async def cancel_rdv(rdv_id: str) -> dict:
    """Annule un RDV existant. STUB — non implémenté."""
    raise NotImplementedError("cancel_rdv sera implémenté en V2")


async def update_rdv(
    rdv_id: str,
    new_date: str | None = None,
    new_heure: str | None = None,
) -> dict:
    """Modifie un RDV existant. STUB — non implémenté."""
    raise NotImplementedError("update_rdv sera implémenté en V2")
