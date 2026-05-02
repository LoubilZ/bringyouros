# Q2 — Validation des décisions techniques CLAUDE.md contre les docs LiveKit

Date : 2026-05-01
Source RAG : `search_livekit_kb(source_type: "docs")` — 521 pages docs.livekit.io

## Légende

| Statut | Signification |
|--------|---------------|
| ✓ | Sourcé — la décision est directement supportée par les docs LiveKit |
| ⚠ | Sous-sourcé — concept présent dans les docs mais la décision CLAUDE.md va plus loin ou manque de détail d'implémentation LiveKit |
| ✗ | Contredit — les docs LiveKit proposent un pattern différent |
| ❓ | Pas dans les docs — décision propre au projet, pas couvert par LiveKit |

---

## Architecture & State

| # | Décision CLAUDE.md | Statut | Source / Note |
|---|-------------------|--------|---------------|
| 1 | Provider voix traité comme **stateless** | ⚠ | LiveKit `AgentSession` gère l'état de la session (lifecycle: initializing → idle → listening → thinking → speaking). Le session *est* stateful côté SDK. Le provider SIP/telephony lui-même est stateless (trunk = config), mais dire "provider voix stateless" est une simplification. L'état vit dans `AgentSession`, pas dans un `CallState` custom séparé. [docs.livekit.io/agents/logic/sessions/](https://docs.livekit.io/agents/logic/sessions/) |
| 2 | État conversationnel dans un **`CallState` sérialisable côté backend** | ⚠ | LiveKit gère l'état conversation via `ChatContext` (historique messages) et `AgentSession` (lifecycle). Il n'y a pas de concept natif `CallState` sérialisable dans le SDK — c'est un pattern custom. LiveKit offre `state synchronization` et `participant attributes` pour partager de l'état, mais pas de persistence backend intégrée. La décision est valide architecturalement mais ne correspond à aucune primitive LiveKit. [docs.livekit.io/frontends/build/agent-state/](https://docs.livekit.io/frontends/build/agent-state/), [docs.livekit.io/transport/data/state/](https://docs.livekit.io/transport/data/state/) |
| 3 | Fallback mémoire acceptable en **dev uniquement** | ❓ | Pas dans les docs LiveKit. Décision d'architecture interne au projet. LiveKit ne prescrit pas de state store. |
| 4 | Chaque appel crée un **`CallLog` dès le début** | ⚠ | LiveKit a un système d'observabilité intégré (Insights) avec recording, transcripts, traces, logs. Les logs sont émis automatiquement avec job ID et worker ID. `ctx.log_context_fields` permet d'ajouter des champs custom. Mais le concept de `CallLog` applicatif créé proactivement est custom — LiveKit logge nativement mais à sa manière. [docs.livekit.io/agents/server/job/](https://docs.livekit.io/agents/server/job/), [docs.livekit.io/deploy/observability/insights/](https://docs.livekit.io/deploy/observability/insights/) |
| 5 | **Outbox transactionnelle** vers le cabinet | ❓ | Pas dans les docs LiveKit. Pattern d'intégration externe (CRM/secrétariat). Entièrement custom. |

## Runtime Rules

| # | Décision CLAUDE.md | Statut | Source / Note |
|---|-------------------|--------|---------------|
| 6 | **Température 0.0** par défaut | ✓ | Les docs montrent que `temperature` est configurable via `extra_kwargs` dans `inference.LLM()`. Le SDK supporte nativement le paramètre. La valeur 0.0 est un choix applicatif valide. [docs.livekit.io/reference/agents/inference-llm-parameters/](https://docs.livekit.io/reference/agents/inference-llm-parameters/) |
| 7 | **Prompts versionnés** | ⚠ | LiveKit `Agent` prend un paramètre `instructions` (string ou `Instructions` object). Le SDK ne fournit pas de système de versioning de prompts intégré — c'est un pattern applicatif à implémenter. Le Vapi Playbook (Ch. 25) recommande de traiter les prompts comme du code versionné, mais ce n'est pas une feature LiveKit. [docs.livekit.io/agents/start/prompting](https://docs.livekit.io/agents/start/prompting) |
| 8 | **Réponses courtes et naturelles en français** | ⚠ | Le SDK supporte le français via STT multilingue (Deepgram Nova-3 multi, ElevenLabs Scribe v2, Cartesia Ink Whisper) et TTS multilingue (Cartesia, ElevenLabs). La longueur/style des réponses est contrôlée par le prompt, pas par le SDK. Le français est supporté mais les docs ne détaillent pas les best practices pour le français spécifiquement. [docs.livekit.io/agents/models/stt/](https://docs.livekit.io/agents/models/stt/), [docs.livekit.io/reference/recipes/changing_language](https://docs.livekit.io/reference/recipes/changing_language) |

## Code Style & Stack

| # | Décision CLAUDE.md | Statut | Source / Note |
|---|-------------------|--------|---------------|
| 9 | **Python 3.11+** | ✓ | Le SDK LiveKit Agents est disponible en Python et Node.js. Le SDK Python utilise async/await natif, type hints, Pydantic. Python 3.11+ est compatible. [docs.livekit.io/agents/logic/sessions/](https://docs.livekit.io/agents/logic/sessions/) |
| 10 | **Async/await natif** | ✓ | Le SDK LiveKit Agents Python est entièrement async. `AgentSession.start()` est `await`, les function tools sont `async def`, les handlers sont async. C'est le pattern natif du SDK. [docs.livekit.io/agents/logic/sessions/](https://docs.livekit.io/agents/logic/sessions/) |
| 11 | **Pydantic pour inputs structurés (function tools)** | ✓ | Le SDK LiveKit utilise Pydantic nativement. Les events (`AgentStateChangedEvent`, `FunctionCallOutput`, `SpeechCreatedEvent`, etc.) sont des `BaseModel` Pydantic. Les function tools acceptent des paramètres typés. [docs.livekit.io/reference/python/livekit/agents/](https://docs.livekit.io/reference/python/livekit/agents/) |
| 12 | **Tests pytest** | ✓ | LiveKit a un framework de test intégré conçu pour pytest. `AgentSession` supporte `session.run(user_input=...)` pour les tests unitaires, avec assertions `expect.next_event().is_message().judge()`. [docs.livekit.io/agents/start/testing/](https://docs.livekit.io/agents/start/testing/) |
| 13 | **Evals conversationnelles séparées des unit tests** | ✓ | Les docs LiveKit distinguent les unit tests (comportement attendu) des evals (jugement LLM). Le framework `judge()` permet des evals basées sur l'intent. Des exemples multi-turn existent. [docs.livekit.io/agents/start/testing/test-framework/](https://docs.livekit.io/agents/start/testing/test-framework/) |
| 14 | **Logs structurés JSON, correlation ID / call ID** | ✓ | LiveKit émet des logs JSON natifs avec job ID, worker ID, process ID, transcript. `ctx.log_context_fields` permet d'ajouter des champs custom (ex: call ID). Support Splunk, log drains, OpenTelemetry. [docs.livekit.io/agents/server/job/](https://docs.livekit.io/agents/server/job/), [docs.livekit.io/deploy/observability/data/](https://docs.livekit.io/deploy/observability/data/), [docs.livekit.io/deploy/agents/log-drains/](https://docs.livekit.io/deploy/agents/log-drains/) |
| 15 | **Type hints partout** | ✓ | Le SDK Python LiveKit est entièrement typé. Les classes, events, et function tools utilisent des type hints, Literal types, et Pydantic models. [docs.livekit.io/reference/python/livekit/agents/](https://docs.livekit.io/reference/python/livekit/agents/) |

## Function Tools & Flow

| # | Décision CLAUDE.md | Statut | Source / Note |
|---|-------------------|--------|---------------|
| 16 | **Function tool `verify_patient_identity(name, surname, dob, devis_id)`** | ✓ | LiveKit supporte nativement les function tools via `@function_tool` decorator. Les tools acceptent des paramètres typés et retournent des strings. Le pattern `RunContext` donne accès au session et userdata. L'implémentation custom (appel backend) est straightforward. [docs.livekit.io/agents/logic/tools/definition/](https://docs.livekit.io/agents/logic/tools/definition/) |
| 17 | **2 tentatives identité max puis raccrochage** | ⚠ | LiveKit supporte le pattern retry dans les function tools (cf. recipe company-directory avec boucle retry). Le `EndCallTool` prebuilt permet de raccrocher. Mais le plafond à 2 tentatives est un choix applicatif — les docs LiveKit montrent des exemples à 3 tentatives et le Vapi Playbook recommande 3. [docs.livekit.io/reference/recipes/company-directory](https://docs.livekit.io/reference/recipes/company-directory) |
| 18 | **Guardrails à chaque tour de conversation** | ✓ | LiveKit supporte le pattern via `llm_node` override (anciennement `before_llm_cb`). Un LLM modérateur séparé peut évaluer chaque réponse avant envoi au TTS. Les recipes "LLM-Powered Content Filter" et "Simple Content Filter" montrent exactement ce pattern. [docs.livekit.io/reference/recipes/llm_powered_content_filter](https://docs.livekit.io/reference/recipes/llm_powered_content_filter) |
| 19 | **Mocks isolés dans `tests/` ou `adapters/dev`** | ⚠ | Le framework de test LiveKit supporte le mocking de tools via `mock_tools` dans le test setup. Mais l'organisation en `tests/` vs `adapters/dev` est un choix de structure projet, pas prescrit par LiveKit. [docs.livekit.io/agents/start/testing/test-framework/](https://docs.livekit.io/agents/start/testing/test-framework/) |

## Telephony & SIP

| # | Décision CLAUDE.md | Statut | Source / Note |
|---|-------------------|--------|---------------|
| 20 | **SIP outbound calling** (implicite : appels sortants vers patients) | ✓ | LiveKit a un support SIP natif complet pour l'outbound. `CreateSIPParticipant` initie un appel, `SIPOutboundTrunkInfo` configure le trunk, multiple providers supportés (Twilio, Plivo, Telnyx, etc.). [docs.livekit.io/telephony/making-calls/outbound-calls/](https://docs.livekit.io/telephony/making-calls/outbound-calls/), [docs.livekit.io/telephony/making-calls/outbound-trunk/](https://docs.livekit.io/telephony/making-calls/outbound-trunk/) |
| 21 | **Stack SIP provider TBD** | ✓ | Cohérent — LiveKit supporte multiple providers SIP. Le choix reste à faire. Providers documentés : Twilio, Plivo, Telnyx, Vonage, SignalWire, BandWidth. [docs.livekit.io/telephony/start/providers/](https://docs.livekit.io/telephony/start/providers/) |
| 22 | **Handoff cabinet pour finalisation** | ✓ | LiveKit supporte les transfers chaud (warm) et froid (cold). `WarmTransferTask` prebuilt gère : hold, consultation room, context handoff, connection. `TransferSIPParticipant` pour cold transfer. Le handoff vers le cabinet est implémentable. [docs.livekit.io/telephony/features/transfers/warm](https://docs.livekit.io/telephony/features/transfers/warm), [docs.livekit.io/telephony/features/transfers/cold](https://docs.livekit.io/telephony/features/transfers/cold) |

## Sujets NON MENTIONNÉS dans CLAUDE.md mais critiques selon les docs LiveKit

| # | Sujet manquant | Statut | Source / Note |
|---|----------------|--------|---------------|
| 23 | **Answering Machine Detection (AMD)** | ✗ Non adressé | LiveKit a un AMD natif (`AMD` class) qui classifie : `human`, `machine-ivr`, `machine-vm`, `machine-unavailable`, `uncertain`. Utilise un LLM pour la classification. Pattern async context manager. **Critique pour l'outbound à 5000 appels/mois** — CLAUDE.md n'en parle pas du tout. [docs.livekit.io/reference/python/livekit/agents/ (class AMD)](https://docs.livekit.io/reference/python/livekit/agents/), [docs.livekit.io/telephony/making-calls/outbound-calls/](https://docs.livekit.io/telephony/making-calls/outbound-calls/) |
| 24 | **Voicemail handling** (laisser message / raccrocher) | ✗ Non adressé | Les docs montrent un pattern `detected_answering_machine` function tool qui laisse un voicemail puis raccroche. Intégré au flow outbound. CLAUDE.md n'a aucune stratégie voicemail. [docs.livekit.io/telephony/making-calls/outbound-calls/](https://docs.livekit.io/telephony/making-calls/outbound-calls/) |
| 25 | **Turn detection / VAD** | ✗ Non adressé | LiveKit a un système de turn detection sophistiqué : Silero VAD, turn detector model multilingue, adaptive interruption handling, endpointing configurable (`min_endpointing_delay`, `max_endpointing_delay`). CLAUDE.md ne mentionne ni VAD ni turn detection ni interruptions. **Critique pour le français** (le modèle multilingue est recommandé). [docs.livekit.io/agents/logic/turns/](https://docs.livekit.io/agents/logic/turns/), [docs.livekit.io/agents/logic/turns/vad/](https://docs.livekit.io/agents/logic/turns/vad/) |
| 26 | **Interruption handling** | ✗ Non adressé | LiveKit supporte : interruptions adaptatives (barge-in model vs VAD), `allow_interruptions` par speech handle, `false_interruption_timeout`, `min_words`, `min_duration`. Crucial pour un flow séquentiel (identité → mutuelle → intention). CLAUDE.md ne mentionne pas comment gérer les interruptions patient. [docs.livekit.io/agents/logic/turns/adaptive-interruption-handling/](https://docs.livekit.io/agents/logic/turns/adaptive-interruption-handling/) |
| 27 | **Recording / annonce d'enregistrement** | ⚠ Partiellement adressé | CLAUDE.md mentionne "annoncer l'enregistrement" (étape 1) mais ne spécifie pas l'implémentation. LiveKit a un recording intégré (`record=True/False` sur `session.start()`), Egress pour export vers S3/GCP, contrôle granulaire (audio, transcript, traces, logs). La configuration recording n'est pas documentée dans CLAUDE.md. [docs.livekit.io/deploy/observability/insights/](https://docs.livekit.io/deploy/observability/insights/), [docs.livekit.io/deploy/observability/data/](https://docs.livekit.io/deploy/observability/data/) |
| 28 | **Metrics / observabilité** | ✗ Non adressé | LiveKit émet des métriques par composant : STT (TTFB, duration), LLM (tokens, latency), TTS (TTFB, audio length), VAD (idle time, inference count). Support OpenTelemetry. Session usage tracking. CLAUDE.md ne mentionne pas l'utilisation de ces métriques LiveKit natives. [docs.livekit.io/deploy/observability/data/](https://docs.livekit.io/deploy/observability/data/) |
| 29 | **Hosting EU / data residency** | ⚠ Partiellement adressé | CLAUDE.md exige "résidence des données en UE". LiveKit Cloud offre `eu-central` (Frankfurt) comme région de déploiement. Le self-hosting est aussi documenté (VM, Kubernetes, multi-region). Mais CLAUDE.md ne fait pas le lien avec les options LiveKit spécifiques. [docs.livekit.io/deploy/admin/regions/agent-deployment](https://docs.livekit.io/deploy/admin/regions/agent-deployment), [docs.livekit.io/transport/self-hosting/](https://docs.livekit.io/transport/self-hosting/) |
| 30 | **Noise cancellation** | ✗ Non adressé | LiveKit a un plugin `noise_cancellation.BVC()` (Background Voice Cancellation) intégré au `RoomOptions`. Important pour les appels téléphoniques (bruit ambiant patient). Non mentionné dans CLAUDE.md. [docs.livekit.io/agents/logic/sessions/](https://docs.livekit.io/agents/logic/sessions/) |
| 31 | **`AgentSession` + `Agent` pattern** | ⚠ Sous-sourcé | CLAUDE.md mentionne `agents/` avec "AgentSession definitions" dans la structure repo. Le pattern LiveKit v1.0 sépare `AgentSession` (orchestrateur) et `Agent` (logique AI : instructions, tools). CLAUDE.md ne distingue pas clairement les deux concepts. [docs.livekit.io/agents/logic/sessions/](https://docs.livekit.io/agents/logic/sessions/) |

## Résumé

| Statut | Count | Détail |
|--------|-------|--------|
| ✓ Sourcé | 12 | Température, Python, async, Pydantic, pytest, evals, logs JSON, type hints, function tools, SIP outbound, handoff, SIP TBD |
| ⚠ Sous-sourcé | 9 | Provider stateless, CallState, CallLog, prompts versionnés, français, 2 tentatives, mocks, recording, hosting EU |
| ✗ Contredit / Non adressé | 6 | AMD/voicemail, turn detection/VAD, interruption handling, metrics/observabilité, noise cancellation |
| ❓ Pas dans les docs | 2 | Fallback mémoire dev, outbox transactionnelle |

## Recommandations prioritaires

### Ajouts critiques au CLAUDE.md (bloquants pour l'implémentation LiveKit)

1. **AMD (Answering Machine Detection)** — Ajouter une section sur la stratégie AMD. LiveKit a une classe `AMD` native avec classification LLM. Décider : si machine → laisser voicemail ? raccrocher ? retry ? C'est une primitive du SDK, pas un nice-to-have.

2. **Turn detection + VAD** — Documenter le choix de turn detection. Pour le français : `MultilingualModel()` recommandé par LiveKit. Silero VAD obligatoire. Paramètres endpointing à calibrer pour le flow séquentiel (questions fermées = silence plus court acceptable).

3. **Interruption handling** — Définir la politique d'interruption par étape du flow. Suggestion : `allow_interruptions=False` pendant les questions critiques (identité, récapitulatif), `adaptive` interruption sinon.

4. **Noise cancellation** — Ajouter `noise_cancellation.BVC()` au `RoomOptions`. Les appels téléphoniques outbound ont souvent du bruit ambiant.

### Corrections au CLAUDE.md

5. **"Provider voix stateless"** — Reformuler. En LiveKit, le **trunk SIP** est stateless, mais l'`AgentSession` est stateful. L'état conversationnel vit dans `ChatContext` + `Agent` state, pas dans un `CallState` custom. Si tu veux un state store externe pour la persistence/recovery, c'est un ajout custom au-dessus du SDK.

6. **Pattern `AgentSession` + `Agent`** — Clarifier la distinction dans la structure repo. `AgentSession` = orchestrateur (STT, LLM, TTS, VAD, turn handling). `Agent` = logique métier (instructions, tools, `on_enter`, `llm_node`). Ce sont deux concepts distincts dans le SDK v1.0.

### Informations à documenter pour la décision stack (Session 1)

7. **STT français** — Options sourcées : Deepgram Nova-3 (45 langues mono, ou `multi`), Cartesia Ink Whisper (100 langues), ElevenLabs Scribe v2 (190 langues). À benchmarker sur le français parlé téléphonique.

8. **TTS français** — Options sourcées : Cartesia Sonic-3 (multilingue, paramètre `language`), ElevenLabs (multilingue), Deepgram Aura-2. Choix de voix française à valider.

9. **Recording config** — `session.start(record=True)` active tout (audio, transcript, traces, logs). Contrôle granulaire possible. À croiser avec les contraintes RGPD/HDS sur la rétention.

10. **Observabilité** — LiveKit émet des métriques par composant (STT, LLM, TTS, VAD) + session usage. Support OpenTelemetry natif. À intégrer dans le monitoring 3 couches recommandé par le Vapi Playbook.
