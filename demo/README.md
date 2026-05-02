# DentalOS Voice Agent — Démo J1

Agent minimal : annonce cabinet + enregistrement + motif, puis écoute une réponse patient.

## Prérequis

- Python 3.11+
- Compte LiveKit Cloud avec API key/secret

## Installation

```bash
cd demo
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Le fichier `.env` doit contenir :

```
LIVEKIT_URL=wss://xxx.livekit.cloud
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
```

## Lancement

```bash
python agent.py dev
```

## Test via Playground

1. Ouvrir https://cloud.livekit.io/playground
2. L'agent apparaît automatiquement — cliquer "Connect"
3. Activer le micro
4. L'agent dit l'annonce intégrale puis écoute la réponse

## Spec de référence

Tous les paramètres sont documentés dans `docs/demo-stack.md` § 5.3.
