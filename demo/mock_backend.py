"""Mock backend — 3 patients synthétiques pour démo J2."""

PATIENTS = {
    "1": {"name": "Jean", "surname": "Dupont", "dob": "1972-03-15"},
    "2": {"name": "Marie", "surname": "Lefevre", "dob": "1985-07-22"},
    "3": {"name": "Pierre", "surname": "Martin", "dob": "1968-11-03"},
}


async def verify_patient_identity(
    name: str,
    surname: str,
    dob: str,
    devis_id: str,
) -> dict:
    """Vérifie l'identité patient contre la base mock.

    Match : case-insensitive sur nom/prénom, format ISO sur DOB.
    Retourne {"match": True} ou {"match": False, "reason": "no_match"}.
    """
    patient = PATIENTS.get(devis_id)
    if patient is None:
        return {"match": False, "reason": "no_match"}

    if (
        patient["name"].lower() == name.strip().lower()
        and patient["surname"].lower() == surname.strip().lower()
        and patient["dob"] == dob.strip()
    ):
        return {"match": True}

    return {"match": False, "reason": "no_match"}
