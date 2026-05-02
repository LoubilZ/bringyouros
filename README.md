# DentalOS Voice Agent

Voice agent en français pour cabinets dentaires en France.
Use case prioritaire v1 : **suivi de devis non retournés** (outbound). L'agent appelle les patients ayant reçu un devis non signé, vérifie leur identité, capte où ils en sont avec leur mutuelle et leur intention de procéder au traitement, et collecte leurs disponibilités pour un handoff au cabinet.

## État du projet
**Session 1 — Cadrage stack & produit** (en cours)

Avant tout code, valider :
- `docs/decisions.md` — choix de stack documentés et sourcés
- `docs/v1-scope.md` — thin slice spec

## Démarrage
1. Lire `CLAUDE.md` (brief permanent du projet)
2. Lancer `claude` dans ce dossier
3. Suivre le process Session 1 décrit dans CLAUDE.md

## Compliance
RGPD + HDS. Voir `docs/dpa-registry.md` pour le registre des sous-traitants.
