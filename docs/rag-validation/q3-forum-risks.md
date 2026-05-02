# Q3 — Top 10 risques techniques outbound LiveKit (forum community)

Date : 2026-05-01
Source RAG : `search_livekit_kb(source_type: "forum")` — 696 threads community.livekit.io
Queries : outbound SIP call issues, SIP trunking provider problems, barge-in interruption, interruption handling latency, reconnect SIP call, voicemail detection outbound, agent dispatch outbound, outbound call rate limit

---

## Top 10 risques techniques — Voice agents outbound LiveKit

### 1. Media timeout → déconnexion automatique à ~33 secondes

**Symptôme** : L'appel outbound se connecte (SIP 200 OK, PCMU/8000 négocié), l'agent et/ou le patient entendent du silence, puis l'appel se coupe automatiquement après 30-33 secondes avec erreur `media-timeout`.

**Cause racine** : Le provider SIP (telco) est derrière un NAT et annonce une **IP privée** dans le header SIP `Contact` au lieu de l'IP publique. L'ACK de LiveKit est envoyé à l'IP privée → inatteignable → le telco retransmet le 200 OK 11 fois (RFC 3261 Timer G/H) pendant ~32s puis envoie un BYE.

**Solution communautaire** : Le provider SIP doit configurer `external_media_address` / `external_signaling_address` (PJSIP) ou `externaddr` + `nat=force_rport,comedia` (chan_sip) pour annoncer l'IP publique.

**Forum** :
- [I'm getting a media-timeout error when doing an outbound call with LK & Twilio](https://community.livekit.io/t/im-getting-a-media-timeout-error-when-doing-an-outbound-call-with-lk-twilio/669)
- [Call ending after 33 seconds automatically - URGENT](https://community.livekit.io/t/call-ending-after-33-seconds-automatically-urgent/483)

**Impact DentalOS** : CRITIQUE. Un provider SIP français mal configuré causerait 100% d'échecs silencieux. Le patient entendrait du silence 33s puis raccrochage.

**À anticiper dans** : `v1-scope.md` (checklist telephony pre-launch), `docs/decisions.md` (critères sélection SIP provider)

---

### 2. Agent parle avant que le patient décroche (missing 180 Ringing)

**Symptôme** : L'agent commence son annonce ("Bonjour, cabinet X...") alors que le téléphone du patient est encore en train de sonner. Le patient décroche au milieu d'une phrase.

**Cause racine** : Le SIP provider n'envoie pas le signal `180 Ringing` provisoire ou le `183 Session Progress`. LiveKit considère le call comme "active" dès le 200 OK mais certains providers fast-connect avant la réponse réelle.

**Solution communautaire** : Utiliser le participant attribute `sip.callStatus` pour attendre l'état `active` avant de faire parler l'agent. Implémenter un handler `on_participant_attributes_changed` qui attend le status correct.

**Forum** :
- [Outbound SIP call: Agent speaks before callee's phone rings](https://community.livekit.io/t/outbound-sip-call-ai-agent-speaks-before-callees-phone-rings-missing-180-ringing-in-pcap/368)

**Impact DentalOS** : ÉLEVÉ. Le patient décroche et entend "...pour un traitement d'orthodontie" sans le début de la phrase. Première impression désastreuse.

**À anticiper dans** : `CLAUDE.md` (Architecture Principles — ne pas déclencher `on_enter` / `session.say()` avant confirmation `sip.callStatus == 'active'`), `v1-scope.md`

---

### 3. Voicemail indétectable au niveau SIP (200 OK pour human ET voicemail)

**Symptôme** : L'appel outbound aboutit sur un répondeur mais le SIP retourne `200 OK` et `sip.callStatus: active` — identique à un humain qui décroche. L'agent traite le répondeur comme un patient et déroule le flow identité.

**Cause racine** : Le protocole SIP ne distingue pas entre "humain a décroché" et "répondeur a décroché". Le 200 OK est identique dans les deux cas.

**Solution communautaire** : Utiliser la détection AMD (Answering Machine Detection) au niveau de l'agent. Deux approches :
- **Nouvelle** (SDK v1.5+) : classe `AMD` native avec classification LLM (human / machine-vm / machine-ivr / machine-unavailable)
- **Ancienne** : function tool `detected_answering_machine` que le LLM appelle quand il reconnaît un message de répondeur

**Forum** :
- [How to detect voicemail on outbound calls](https://community.livekit.io/t/how-to-detect-voicemail-on-outbound-calls/218)
- [How to distinguish between answered calls and voicemail for outbound calls](https://community.livekit.io/t/how-to-distinguish-between-answered-calls-and-voicemail-for-outbound-calls/184)

**Impact DentalOS** : CRITIQUE. Sans AMD, l'agent va demander nom/prénom/DOB à un répondeur vocal, gaspiller du temps agent, et potentiellement laisser des données patient en clair sur un répondeur.

**À anticiper dans** : `CLAUDE.md` (nouvelle section AMD/voicemail strategy), `v1-scope.md` (décision : laisser message court / raccrocher / retry)

---

### 4. Adaptive interruption crash → fallback VAD silencieux

**Symptôme** : L'adaptive interruption (barge-in model) plante avec `InterruptionDetectionError: failed to detect interruption after 3 attempts` ou `interruption inference timed out after 1.0s`, puis fallback silencieux vers VAD-only. L'agent continue de fonctionner mais les interruptions sont moins bien gérées (faux positifs sur "mm-hmm", toux, bruit ambiant).

**Cause racine** : Timeout du service d'inférence d'interruption LiveKit (WebSocket), incompatibilité avec certains STT providers (ElevenLabs STT signalé), ou limites de la version SDK.

**Solution communautaire** : Pas de fix clair. Upgrade SDK recommandé. Le fallback VAD est automatique mais non-optimal. Certains devs désactivent l'adaptive et restent sur VAD avec paramètres `min_words` et `min_duration` ajustés.

**Forum** :
- [Adaptive interruption disabled due to unrecoverable error](https://community.livekit.io/t/adaptive-interruption-disabled-due-to-unrecoverable-error-falling-back-to-vad-based-interruption/775)
- [Adaptive interruption error nodejs agents sdk](https://community.livekit.io/t/adaptive-interruption-error-nodejs-agents-sdk/670)
- [Interruption inference timeout: status_code=408](https://community.livekit.io/t/interruption-inference-timeout-status-code-408/700)

**Impact DentalOS** : MOYEN. Le fallback VAD fonctionne mais produira des faux positifs d'interruption (patient tousse → agent s'arrête au milieu de la question identité). Sur un flow séquentiel avec questions fermées, c'est perturbant.

**À anticiper dans** : `CLAUDE.md` (section turn detection — prévoir fallback VAD explicite, paramétrer `min_words=1` et `min_duration=0.5s`), tests scénarios avec bruit ambiant

---

### 5. Silence côté patient (one-way audio)

**Symptôme** : L'appel SIP est établi (200 OK), l'agent entend potentiellement le patient, mais le patient n'entend que du silence. Ou inversement. WebRTC fonctionne mais pas SIP.

**Cause racine** : Problèmes de codec negotiation (PCMU/8000 vs autre), NAT traversal, ou media path routing. Plus fréquent sur les trunks self-hosted ou avec des providers non-mainstream.

**Solution communautaire** : Vérifier PCAP pour identifier où le media s'arrête. S'assurer que le provider SIP supporte PCMU/8000. Vérifier les firewalls pour les ports RTP (UDP range).

**Forum** :
- [SIP Inbound Trunk - One-Way Audio Issue](https://community.livekit.io/t/sip-inbound-trunk-one-way-audio-issue/250)
- [Inbound SIP calls: caller hears silence; WebRTC works](https://community.livekit.io/t/inbound-sip-calls-caller-hears-silence-webrtc-works-project-p-mu9nuejzw03/921)

**Impact DentalOS** : CRITIQUE. Le patient entend du silence → raccroche → expérience catastrophique. Le cabinet perd un patient potentiel sans le savoir.

**À anticiper dans** : `v1-scope.md` (test audio bidirectionnel obligatoire avant go-live, monitoring one-way audio en production)

---

### 6. Agent dispatch : double agent ou agent absent

**Symptôme** : Deux agents rejoignent la même room (un explicit dispatch + un automatic dispatch), ou l'agent ne rejoint pas du tout la room après dispatch (status "pending" au lieu de "running").

**Cause racine** : Confusion entre automatic et explicit dispatch dans la config LiveKit Cloud. Ou worker en état "pending" (plan gratuit / cold start).

**Solution communautaire** : S'assurer qu'un seul mode de dispatch est actif (explicit pour outbound, désactiver l'automatic). Pour le cold start : plan Ship+ garde les workers running 24/7. Redéployer l'agent si state corrompu.

**Forum** :
- [Two agents joining the same outbound telephony room](https://community.livekit.io/t/two-agents-joining-the-same-outbound-telephony-room/214)
- [Livekit Agent Dispatch issue, hosted on livekit cloud](https://community.livekit.io/t/livekit-agent-dispatch-issue-hosted-on-livekit-cloud/811)
- [Agent is not joining the room](https://community.livekit.io/t/agent-is-not-joining-the-room/412)

**Impact DentalOS** : ÉLEVÉ. Un double agent = deux voix parlent en même temps au patient. Un agent absent = le patient décroche et entend du silence (identique au risque #5 côté UX).

**À anticiper dans** : `v1-scope.md` (architecture dispatch — explicit only, monitoring agent join latency), `docs/decisions.md` (choix plan LiveKit Cloud)

---

### 7. SIP connection timeouts en masse (1000+ échecs)

**Symptôme** : Vagues de SIP connection timeouts sur les appels. Pas d'erreur côté provider, pas d'erreur côté agent. Les appels ne s'établissent simplement pas.

**Cause racine** : Capacity issues côté LiveKit Cloud ou routing DNS. Les threads ne montrent pas de root cause publique claire — souvent résolu côté infrastructure LiveKit.

**Solution communautaire** : Signaler à LiveKit support avec les call IDs. Pas de self-service fix.

**Forum** :
- [Currently observing SIP connection timeouts on inbound calls. Currently observed over 1000 call failures](https://community.livekit.io/t/currently-observing-sip-connection-timeouts-on-inbound-calls-currently-observed-over-1000-call-failures/434)

**Impact DentalOS** : ÉLEVÉ. À 5000 appels/mois, un incident de ce type pourrait affecter des centaines de patients en une journée. Besoin d'un SLA formalisé.

**À anticiper dans** : `docs/decisions.md` (SLA LiveKit Cloud vs self-hosted), `v1-scope.md` (alerting sur taux d'échec appels, circuit breaker)

---

### 8. Latence ajoutée par l'adaptive interruption

**Symptôme** : Question de la communauté sur l'impact latence de l'adaptive interruption. Pas de benchmark public disponible. Concern sur la compatibilité avec VAD temps réel et la consommation mémoire.

**Cause racine** : L'adaptive interruption fait un appel inférence supplémentaire (WebSocket vers le service LiveKit) à chaque détection de parole. Latence additionnelle non documentée précisément.

**Solution communautaire** : LiveKit affirme que c'est gratuit et ajouté par défaut sur Cloud. Pas de mesures de latence publiées. Pour les cas sensibles à la latence : rester sur VAD-only.

**Forum** :
- [Does adaptive interruption handling add latency anywhere in the voice agent pipeline?](https://community.livekit.io/t/does-adaptive-interruption-handling-add-latency-anywhere-in-the-voice-agent-pipeline/774)

**Impact DentalOS** : MOYEN. Sur un flow séquentiel (questions fermées, réponses courtes), chaque milliseconde de latence est perceptible. Mais le bénéfice (moins de faux positifs d'interruption) peut compenser.

**À anticiper dans** : `v1-scope.md` (benchmark latence end-to-end avant go-live, critère < 800ms TTFT)

---

### 9. ICE restart loop infini sur participant SIP (self-hosted)

**Symptôme** : Le participant SIP entre dans une boucle infinie ICE restart → reconnect → ICE fail qui ne se résout jamais. L'appel reste "connecté" mais aucun media ne passe.

**Cause racine** : Problème de networking sur l'infra self-hosted (Azure AKS). Les configurations réseau Kubernetes + SIP + WebRTC sont complexes (UDP, TURN, ports range).

**Solution communautaire** : Pas de fix public. Spécifique au self-hosted. Les utilisateurs Cloud ne reportent pas ce problème.

**Forum** :
- [SIP participant stuck in infinite ICE restart loop](https://community.livekit.io/t/sip-participant-stuck-in-infinite-ice-restart-loop/897)

**Impact DentalOS** : FAIBLE si LiveKit Cloud, CRITIQUE si self-hosted. Ce risque pèse dans la décision Cloud vs self-hosted.

**À anticiper dans** : `docs/decisions.md` (argument supplémentaire pro-Cloud pour le pilote)

---

### 10. Agent greeting jamais entendu par le patient (outbound self-hosted)

**Symptôme** : L'appel outbound est établi, le patient décroche, mais n'entend jamais la phrase d'accueil de l'agent. L'agent "parle" (logs OK) mais l'audio ne sort pas vers le SIP participant.

**Cause racine** : Race condition entre le moment où le SIP participant est "connected" et le moment où le media path est réellement opérationnel. Si l'agent fait `session.say()` trop tôt, l'audio est perdu.

**Solution communautaire** : Attendre l'événement `participant_connected` + un délai de stabilisation avant le premier `say()`. Ou écouter `sip.callStatus == 'active'` dans les participant attributes.

**Forum** :
- [Outbound SIP call: agent greeting never heard by callee (self-hosted v1.9.12)](https://community.livekit.io/t/outbound-sip-call-agent-greeting-never-heard-by-callee-self-hosted-v1-9-12/642)

**Impact DentalOS** : CRITIQUE. L'annonce ("Bonjour, ici le cabinet X, cet appel est enregistré...") est la première et seule chance de cadrer l'appel. Si elle est perdue, le patient entend du silence puis une question de vérification d'identité sans contexte.

**À anticiper dans** : `CLAUDE.md` (Architecture Principles — attendre confirmation media path avant `on_enter`), code agent outbound

---

## Matrice de priorisation

| # | Risque | Sévérité | Probabilité | À documenter dans |
|---|--------|----------|-------------|-------------------|
| 1 | Media timeout 33s | CRITIQUE | Moyenne (dépend du provider) | `v1-scope.md`, `decisions.md` |
| 2 | Agent parle avant décrochage | ÉLEVÉ | Haute (provider-dépendant) | `CLAUDE.md`, `v1-scope.md` |
| 3 | Voicemail indétectable SIP | CRITIQUE | Très haute (structurel) | `CLAUDE.md`, `v1-scope.md` |
| 4 | Adaptive interruption crash | MOYEN | Moyenne (SDK-dépendant) | `CLAUDE.md`, tests scénarios |
| 5 | One-way audio / silence | CRITIQUE | Moyenne | `v1-scope.md` |
| 6 | Double agent / agent absent | ÉLEVÉ | Moyenne (config-dépendant) | `v1-scope.md`, `decisions.md` |
| 7 | SIP timeouts en masse | ÉLEVÉ | Faible (infra LiveKit) | `decisions.md` (SLA) |
| 8 | Latence adaptive interruption | MOYEN | Faible (benchmarks manquants) | `v1-scope.md` |
| 9 | ICE restart loop (self-hosted) | CRITIQUE si SH | Faible si Cloud | `decisions.md` |
| 10 | Greeting perdu | CRITIQUE | Haute (race condition connue) | `CLAUDE.md`, code agent |

## Risques à ajouter immédiatement au CLAUDE.md

Les risques **2, 3, 4, 10** nécessitent des décisions d'architecture dans CLAUDE.md :
- **#2 + #10** → Nouvelle règle Architecture Principles : "Ne jamais déclencher de speech avant confirmation `sip.callStatus == 'active'` ET stabilisation media path"
- **#3** → Nouvelle section "AMD / Voicemail Strategy" dans Scope V1
- **#4** → Section Turn Detection avec fallback VAD paramétré

## Risques à ajouter au v1-scope.md

Les risques **1, 5, 6, 7** sont des risques opérationnels à lister dans la checklist pre-launch :
- **#1 + #5** → Test audio bidirectionnel obligatoire avec le provider SIP retenu
- **#6** → Config dispatch : explicit only, monitoring agent join
- **#7** → SLA formalisé, alerting sur taux d'échec, circuit breaker

## Pas dans les docs LiveKit mais signalé implicitement

**Absence de rate limiting natif** : Aucun thread forum ne mentionne de rate limit LiveKit sur les appels outbound, mais aucune doc n'en parle non plus. Pour 5000 appels/mois (~250/jour ouvré), le volume est modeste. Mais le warm-up du numéro SIP (cf. Q1 Vapi Playbook) reste nécessaire côté provider (Twilio, Telnyx, etc.) pour éviter le spam flagging.
