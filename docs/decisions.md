# DentalOS — Journal des décisions

> **Template** : chaque entrée suit le format défini dans CLAUDE.md § Decision Log Template.
> **Statuts** : `résolu` | `ouvert` | `à arbitrer session 1` | `bloquant`

---

## 2026-05-02 — Priorisation des use cases outbound

**Contexte** :
Le scoring Vapi Playbook (Ch. 7) classe le suivi de devis non retournés comme P2 Strategic Bet (Feasibility ~3.5 / Impact ~4), pas comme P1 Flagship. Le Playbook avertit explicitement : « Starting with a P2 is how pilots stall. » Un P1 plus simple (ex : confirmation de RDV, Feasibility ~5.0 / Impact ~4.5) pourrait servir de stepping stone.

**Options considérées** :
- A. Démarrer par UC1 confirmation de RDV (P1 Flagship) puis enchaîner sur suivi de devis en v2
- B. Démarrer directement par le suivi de devis (P2 Strategic Bet) avec guardrails renforcés
- C. Exécuter les deux en parallèle (thin slice pour chaque)

**Choix recommandé** :
B — démarrer par le suivi de devis (P2), en acceptant le risque de complexité plus élevé, car c'est le use case à plus forte valeur business (revenue leak structurel). Les guardrails doivent être dimensionnés en conséquence.

**Décision validée** :
À valider session 1. La justification P2-first doit être documentée : pourquoi aucun P1 n'est retenu comme stepping stone (pas de volume suffisant en confirmation RDV ? pas de connecteur agenda ? priorité business du cabinet pilote ?).

**Justification** :
- Le revenue leak sur les devis non signés est identifié comme le principal pain point par le cabinet pilote
- La confirmation de RDV (P1) est un use case plus simple mais à impact moins direct sur le revenue
- Le risque du P2 est mitigé par : thin slice strict (6 étapes, capability Level 2), guardrails renforcés, volume pilote limité

**Risques** :
- Complexité technique plus élevée (lookup backend multi-step) → risque de retard pilote
- Si le pilote échoue, on n'a pas de P1 déjà validé en fallback
- Le Playbook recommande de commencer par un P1 pour construire la confiance organisationnelle

**Questions ouvertes** :
- Le cabinet pilote a-t-il un volume suffisant de confirmations de RDV pour justifier un P1 stepping stone ?
- Existe-t-il un connecteur agenda prêt qui rendrait le P1 trivial ?

**Sources** :
- RAG `vapi_book` : Ch. 7 Priority Matrix, « Common scoring mistakes »
- RAG `vapi_book` : Ch. 8 « Planning the expansion path »
- `docs/rag-validation/q1-vapi-coherence.md` — Gap #1

**Statut** : `à arbitrer session 1`

---

## 2026-05-02 — Compliance outbound France (Bloctel + décret 2022-1313)

**Contexte** :
Les appels outbound commerciaux en France sont encadrés par le décret 2022-1313 (horaires d'appel) et la réglementation Bloctel (liste d'opposition au démarchage téléphonique). Le non-respect expose à des sanctions (amende jusqu'à 75 000€ personne morale par infraction).

**Options considérées** :
- A. Vérification Bloctel systématique avant chaque appel (API Bloctel)
- B. Invocation de l'exception « relation contractuelle préexistante » (le patient a reçu un devis = relation existante)
- C. Les deux : exception invoquée + vérification Bloctel en sécurité

**Choix recommandé** :
B — invoquer l'exception « relation contractuelle préexistante » (le patient a reçu un devis du cabinet, il y a donc une relation commerciale en cours). Mais cette interprétation doit être validée par un juriste avant le premier appel réel.

**Décision validée** :
Horaires validés (lun-ven 10h-13h / 14h-20h, décret 2022-1313 art. 3). Exception Bloctel à valider juridiquement.

**Justification** :
- Le décret 2022-1313 fixe les plages horaires autorisées : lundi-vendredi 10h-13h et 14h-20h. Pas de week-end, pas de jours fériés.
- L'article L223-1 du Code de la consommation prévoit une exception Bloctel pour les « sollicitations ayant un lien direct avec l'objet d'un contrat en cours ». Un devis émis par le cabinet crée ce lien.
- Cependant, un devis non signé n'est pas un contrat en cours au sens strict. L'interprétation mérite une validation juridique formelle.
- Même avec l'exception, les horaires du décret 2022-1313 restent obligatoires.

**Risques** :
- Si l'exception Bloctel n'est pas validée → obligation de vérifier chaque numéro via l'API Bloctel (coût + latence + setup)
- Risque réputationnel si des patients se sentent « démarchés » par leur cabinet dentaire
- Sanction DGCCRF en cas de non-conformité

**Questions ouvertes** :
- Validation juridique formelle de l'exception « relation contractuelle préexistante » pour un devis non signé
- Si l'exception n'est pas retenue : coût et faisabilité technique de l'intégration API Bloctel

**Sources** :
- Décret n° 2022-1313 du 13 octobre 2022
- Code de la consommation, art. L223-1 à L223-7
- `docs/rag-validation/q1-vapi-coherence.md` — Gap #13

**Statut** : `bloquant` — validation juridique requise avant premier appel

---

## 2026-05-02 — D1 : Choix de la plateforme voix

**Contexte** :
Un RAG dev-time a été construit sur LiveKit (521 pages docs, 696 threads forum). Un choix non-LiveKit réduirait fortement la valeur de ce RAG. Cependant, le choix doit être fait sur les critères objectifs : RGPD/HDS, latence, coût, support SIP outbound, maturité AMD, qualité STT français.

**Options considérées** :
- A. LiveKit Agents SDK + LiveKit Cloud
- B. LiveKit Agents SDK + self-hosted (EU)
- C. Vapi (platform-as-a-service)
- D. Retell AI
- E. Bland AI
- F. Custom (Twilio SIP + LLM + STT/TTS assemblés)

**Choix recommandé** :
À évaluer en session 1. Le RAG donne un avantage à LiveKit mais les contraintes HDS/EU residency doivent primer.

**Décision validée** :
Non résolue.

**Risques** :
- LiveKit Cloud : résidence des données US par défaut, HDS non confirmé. Self-hosted résout le problème mais ajoute de la complexité opérationnelle.
- Vapi/Retell/Bland : vendor lock-in + résidence données à vérifier + DPA à obtenir
- Custom : complexité d'intégration, pas de support AMD natif

**Questions ouvertes** :
- LiveKit Cloud propose-t-il une option EU-only ? (à vérifier docs officielles)
- Self-hosted LiveKit sur un hébergeur HDS (OVH, Scaleway) : faisable ? Complexité opérationnelle ?
- Quel est le coût comparatif par minute d'appel pour chaque option ?
- Support AMD natif dans chaque option ?

**Sources** :
- RAG `docs` : LiveKit architecture, SIP trunking
- `docs/rag-validation/q2-livekit-sourcing.md` — 31 points techniques vérifiés
- `docs/rag-validation/q3-forum-risks.md` — 10 risques outbound

**Statut** : `ouvert`

---

## 2026-05-02 — D2 : STT pour le français

**Contexte** :
La qualité du STT en français est critique pour le flow (noms propres, dates de naissance, vocabulaire dentaire dans les questions hors-scope). Le choix du STT est lié au choix de plateforme (certaines imposent leur STT).

**Options considérées** :
- A. Deepgram (Nova-2, support français)
- B. Google Cloud Speech-to-Text (V2, français)
- C. Azure Speech Services (français)
- D. Whisper (self-hosted, open-source)
- E. STT intégré à la plateforme voix retenue

**Choix recommandé** :
À évaluer en session 1 après le choix de plateforme. Critères clés : WER français < 15%, latence < 300ms, résidence UE, DPA disponible.

**Décision validée** :
Non résolue.

**Risques** :
- WER élevé sur les noms propres français → échec de vérification d'identité
- WER élevé sur les dates → DOB mal transcrit → false negative identité
- Résidence des données : certains providers traitent l'audio hors UE

**Questions ouvertes** :
- Benchmark WER comparatif sur corpus français dentaire (noms propres + dates)
- Quel provider offre la meilleure latence en streaming pour le français ?
- Résidence UE confirmée pour chaque option ?

**Sources** :
- `docs/rag-validation/q2-livekit-sourcing.md` — Points STT
- `docs/rag-validation/q3-forum-risks.md` — Risk #3 (STT français)

**Statut** : `ouvert`

---

## 2026-05-02 — D3 : TTS pour le français

**Contexte** :
Le TTS doit produire un français naturel, neutre, professionnel — pas une voix robotique. Le ton consultatif est essentiel pour ne pas être perçu comme du démarchage agressif.

**Options considérées** :
- A. ElevenLabs (Multilingual v2)
- B. Google Cloud TTS (WaveNet / Neural2, français)
- C. Azure Neural TTS (français)
- D. Cartesia (Sonic, faible latence)
- E. TTS intégré à la plateforme voix retenue

**Choix recommandé** :
À évaluer en session 1 après le choix de plateforme. Critères clés : naturalité en français, TTFB < 200ms, résidence UE, DPA disponible.

**Décision validée** :
Non résolue.

**Risques** :
- Voix perçue comme robotique → patient raccroche dès l'annonce
- Latence TTS trop élevée → TTFT global > 800ms
- Voix trop « vendeuse » ou trop « médicale » → mauvaise perception

**Questions ouvertes** :
- Test A/B perceptif sur 3-4 voix françaises avant go-live ?
- ElevenLabs : résidence UE confirmée ? DPA disponible ?
- Cartesia : maturité du français ?

**Sources** :
- `docs/rag-validation/q2-livekit-sourcing.md` — Points TTS
- `docs/rag-validation/q3-forum-risks.md` — Risk #10 (greeting perdu)

**Statut** : `ouvert`

---

## 2026-05-02 — D4 : LLM pour le raisonnement conversationnel

**Contexte** :
Le LLM pilote le raisonnement conversationnel : gestion du flow, extraction d'intent, génération des réponses, exécution des guardrails. Température 0.0 obligatoire. Le modèle doit suivre les instructions strictement (pas de scope creep).

**Options considérées** :
- A. Claude (Anthropic) — Sonnet ou Haiku pour la latence
- B. GPT-4o-mini (OpenAI)
- C. Gemini Flash (Google)
- D. Modèle open-source self-hosted (Llama, Mistral)

**Choix recommandé** :
À évaluer en session 1. Critères clés : instruction following (guardrails stricts), latence TTFT < 400ms, coût par appel, résidence UE, DPA disponible, function calling fiable.

**Décision validée** :
Non résolue.

**Risques** :
- Instruction following insuffisant → scope creep, réponses hors-scope non bloquées
- Latence trop élevée → TTFT global > 800ms
- Coût par appel trop élevé au volume pilote (5000 appels/mois)
- Résidence UE non garantie (OpenAI, Anthropic = US par défaut)

**Questions ouvertes** :
- Quel modèle respecte le mieux les guardrails « ne pas répondre » (zero-content redirect) ?
- Coût estimé par appel (tokens in + out × 6 turns × prix) pour chaque option ?
- Anthropic / OpenAI / Google : option EU-only disponible ?
- Self-hosted : faisable opérationnellement pour un pilote ?

**Sources** :
- `docs/rag-validation/q4-scope-creep.md` — 12 risques de dérive LLM
- `docs/rag-validation/q2-livekit-sourcing.md` — Points LLM

**Statut** : `ouvert`

---

## 2026-05-02 — D5 : Hébergement et résidence des données (RGPD/HDS)

**Contexte** :
Les données manipulées incluent des données de santé identifiantes (identité patient + catégorie de traitement = donnée de santé au sens RGPD). L'hébergement de ces données en France/UE est obligatoire, et la certification HDS (Hébergeur de Données de Santé) peut être requise selon l'architecture.

**Options considérées** :
- A. Hébergeur HDS certifié (OVH Healthcare, Scaleway, Clever Cloud) — self-hosted
- B. Cloud hyperscaler avec région EU (AWS eu-west, GCP europe-west, Azure France) — non HDS
- C. Architecture « zéro donnée de santé identifiante côté voix » — le voice agent ne reçoit que des identifiants opaques, la jonction se fait côté backend HDS du cabinet
- D. Vendor voix avec certification HDS intégrée (à trouver)

**Choix recommandé** :
À évaluer en session 1. L'option C (architecture de dissociation) est la plus pragmatique si aucun vendor voix n'est HDS : le voice agent ne manipule que des tokens opaques + des réponses déclaratives, la donnée de santé identifiante n'est reconstituée que côté backend HDS du cabinet.

**Décision validée** :
Non résolue.

**Risques** :
- L'architecture C nécessite de prouver que la catégorie de traitement + l'identité patient NE transitent PAS ensemble dans un même système non-HDS. Or dans le flow actuel, l'agent mentionne la catégorie en étape 1 ET vérifie l'identité en étape 2 → les deux passent par le même LLM. C'est une donnée de santé identifiante au sens de la CNIL.
- Ce point est potentiellement **bloquant** pour toute architecture non-HDS.
- Le nombre d'hébergeurs HDS est limité, et aucune plateforme voix majeure n'est certifiée HDS à ce jour.

**Questions ouvertes** :
- La CNIL considère-t-elle qu'un LLM qui reçoit séquentiellement catégorie + identité constitue un traitement de données de santé ?
- Peut-on dissocier le flow pour que la catégorie ne transite pas par le LLM (ex : audio pré-enregistré pour l'annonce) ?
- Existe-t-il un vendor voix HDS ou en cours de certification ?

**Sources** :
- `docs/rag-validation/q1-vapi-coherence.md` — Gap #10 (HDS)
- CNIL, référentiel HDS (décret 2018-137)
- Code de la santé publique, art. L1111-8

**Statut** : `bloquant` — risque structurel à évaluer en session 1

---

## 2026-05-02 — D6 : Backend d'identité patient

**Contexte** :
L'étape 2 du flow appelle `verify_patient_identity(name, surname, dob, devis_id)`. Ce backend doit être fourni ou développé. Il reçoit des données sensibles (nom + DOB) et doit répondre en < 3s.

**Options considérées** :
- A. API exposée par le logiciel de gestion du cabinet (si existant)
- B. Micro-service custom interrogeant la base patients du cabinet (via connecteur)
- C. Service intermédiaire avec cache chiffré (pour éviter les appels temps réel au cabinet)

**Choix recommandé** :
À évaluer en session 1 avec le cabinet pilote. Dépend du logiciel de gestion utilisé et de ses capacités API.

**Décision validée** :
Non résolue.

**Risques** :
- Le logiciel de gestion du cabinet n'a pas d'API → développement connecteur nécessaire
- Latence > 3s → timeout, mauvaise expérience patient
- Le backend reçoit des données sensibles (nom + DOB) → HDS potentiellement requis pour ce composant aussi
- Disponibilité du backend pendant les heures d'appel

**Questions ouvertes** :
- Quel logiciel de gestion utilise le cabinet pilote ? (Desmos, Julie, Logos, Veasy, autre ?)
- Ce logiciel expose-t-il une API REST ?
- Le backend d'identité doit-il être hébergé HDS ?

**Sources** :
- `docs/rag-validation/q4-scope-creep.md` — Risk #10 (tool-first-truth)
- CLAUDE.md § Tool contracts

**Statut** : `ouvert`

---

## 2026-05-02 — D7 : Provider SIP outbound

**Contexte** :
Le trunk SIP outbound est l'interface entre l'agent et le réseau téléphonique. Il doit supporter les appels sortants vers des numéros français, le codec PCMU/8000, le CNAM/caller-ID, et la détection AMD.

**Options considérées** :
- A. Twilio (SIP trunking)
- B. Telnyx
- C. Vonage (Nexmo)
- D. OVH Telecom (SIP trunk français)
- E. Provider SIP intégré à la plateforme voix retenue

**Choix recommandé** :
À évaluer en session 1 après le choix de plateforme. Critères clés : support numéros français géographiques, CNAM, tarification compétitive France, fiabilité, API de monitoring.

**Décision validée** :
Non résolue.

**Risques** :
- Twilio/Telnyx : société US, données vocales transitent potentiellement hors UE
- OVH Telecom : résidence UE garantie mais intégration LiveKit/autre plateforme à vérifier
- CNAM pas toujours supporté en France (dépend du réseau de l'opérateur destinataire)

**Questions ouvertes** :
- Quel provider supporte le CNAM en France de manière fiable ?
- Quel est le coût par minute pour les appels France mobile + fixe ?
- L'AMD est-elle côté SIP provider ou côté plateforme voix ?

**Sources** :
- `docs/rag-validation/q3-forum-risks.md` — Risk #2 (agent talks before pickup), Risk #5 (DTMF/codec)
- `docs/rag-validation/q1-vapi-coherence.md` — Gap #8 (number reputation)

**Statut** : `ouvert`

---

## 2026-05-02 — D8 : Seuil numérique de succès pilote

**Contexte** :
Le Vapi Playbook exige un seuil de succès écrit avant le pilote : « The threshold was written down before the pilot started. No one could argue later that 19% was 'close enough'. » (Ch. 21). La métrique principale est le taux de conversion devis → traitement démarré.

**Options considérées** :
- A. Fixer le seuil X% = baseline humaine Y% (juste égaler l'humain)
- B. Fixer X% = Y% + delta significatif (ex : +10 points de pourcentage)
- C. Fixer un seuil absolu indépendant de la baseline (ex : > 30%)

**Choix recommandé** :
B — le pilote réussit si le taux de conversion atteint baseline + delta. Le delta exact dépend de la baseline mesurée (à collecter du cabinet avant go-live).

**Décision validée** :
Non résolue. Nécessite la baseline humaine du cabinet pilote.

**Risques** :
- Pas de baseline → impossible de fixer un seuil significatif
- Baseline trop basse (ex : 5%) → même un résultat modeste semble bon
- Baseline haute (ex : 40%) → le delta à atteindre est proportionnellement difficile

**Questions ouvertes** :
- Quelle est la baseline actuelle du cabinet pilote ? (% de devis émis qui mènent à un traitement, avec et sans relance humaine)
- Quel delta est considéré comme « business significant » par le cabinet ?
- Quelle période de mesure pour la baseline ? (minimum 3 mois recommandé)

**Sources** :
- RAG `vapi_book` : Ch. 8 « Defining success criteria by goal », Ch. 21 « Defining the question »
- `docs/rag-validation/q1-vapi-coherence.md` — Gap #3

**Statut** : `bloquant` — pas de go-live sans seuil écrit

---

## 2026-05-02 — D9 : Turn detection et endpointing français

**Contexte** :
L'endpointing (détection de fin de parole) est l'un des facteurs les plus critiques pour l'expérience utilisateur. Trop court = l'agent coupe la parole. Trop long = silences gênants. Le français a des patterns prosodiques différents de l'anglais (liaisons, pauses de réflexion plus longues).

**Options considérées** :
- A. Silero VAD avec `MultilingualModel()` (recommandé LiveKit docs)
- B. Silero VAD avec modèle par défaut (anglais)
- C. Adaptive interruption (Azure-based, intégré LiveKit)
- D. A + C en combinaison (adaptive en primaire, VAD en fallback)

**Choix recommandé** :
D — adaptive interruption avec fallback VAD `MultilingualModel()`. Paramètres initiaux dans `docs/v1-scope.md` § S5, à ajuster après tests réels.

**Décision validée** :
Non résolue. Les paramètres d'endpointing doivent être testés sur des appels réels en français.

**Risques** :
- L'adaptive interruption a un bug documenté (Q3 #4) → le fallback VAD-only doit fonctionner seul
- Le `MultilingualModel()` n'est pas explicitement documenté pour le français dans le RAG → à vérifier docs officielles
- Paramètres d'endpointing trop agressifs → l'agent coupe les patients qui réfléchissent

**Questions ouvertes** :
- Le `MultilingualModel()` de LiveKit supporte-t-il le français explicitement ?
- L'adaptive interruption est-elle disponible dans toutes les régions / tous les plans ?
- Benchmark d'endpointing nécessaire sur 50 appels test avant go-live

**Sources** :
- RAG `docs` : Turn detection, Silero VAD, MultilingualModel
- `docs/rag-validation/q3-forum-risks.md` — Risk #4 (adaptive interruption crash)
- `docs/rag-validation/q2-livekit-sourcing.md` — Points turn detection

**Statut** : `ouvert`

---

## 2026-05-02 — D10 : Observabilité et monitoring

**Contexte** :
Le Vapi Playbook exige un monitoring 3 couches : system health, leading indicators, business outcomes. « Most teams only build the bottom one. » (Ch. 26). Pour le pilote, au minimum les leading indicators doivent être en place.

**Options considérées** :
- A. Monitoring intégré à la plateforme voix (dashboard natif)
- B. Stack custom : logs structurés → Datadog/Grafana → alertes
- C. Minimum viable : logs structurés + CSV export + review hebdomadaire manuelle
- D. A + B combinés

**Choix recommandé** :
C pour le pilote (pragmatisme), avec migration vers B post-validation. Le pilote doit avoir au minimum : logs structurés JSON, `CallOutcome` exportable, review hebdomadaire.

**Décision validée** :
Non résolue.

**Risques** :
- Monitoring insuffisant → on ne détecte pas les dérives (scope creep, guardrail failures) avant qu'elles n'impactent la business metric
- Pas de system health monitoring → incidents techniques non détectés (backend down, STT dégradé, numéro flaggé spam)
- Pas de leading indicators → on ne voit le problème qu'après 1 mois sur la metric principale

**Questions ouvertes** :
- Quels leading indicators monitorer en priorité ? (proposition : taux de complétion du flow, taux d'identification réussie, handle time moyen, taux d'escalade hors-scope)
- Quelle granularité d'alerting pour le pilote ? (daily digest ou alerte temps réel ?)
- Budget observabilité pour le pilote ?

**Sources** :
- RAG `vapi_book` : Ch. 26 « Three layers »
- `docs/rag-validation/q1-vapi-coherence.md` — Gap #10 (monitoring 3 couches)

**Statut** : `ouvert`

---

## Questions ouvertes transverses

Les questions ci-dessous ne sont pas liées à une décision unique mais conditionnent plusieurs choix :

| # | Question | Décisions impactées | Priorité |
|---|----------|---------------------|----------|
| Q1 | Quel logiciel de gestion utilise le cabinet pilote ? | D6, D1, S4 | Haute |
| Q2 | Le cabinet a-t-il un volume de confirmations RDV suffisant pour justifier un P1 ? | Priorisation use case | Haute |
| Q3 | Budget mensuel cible pour le pilote (infra + vendors) ? | D1, D2, D3, D4, D7, D10 | Haute |
| Q4 | Validation juridique Bloctel — exception relation contractuelle pour devis non signé ? | Compliance outbound | Bloquante |
| Q5 | La CNIL considère-t-elle le transit catégorie + identité dans un LLM comme traitement HDS ? | D5 | Bloquante |
| Q6 | Le cabinet accepte-t-il un pilote limité (250 appels/jour, 4-6 semaines) ? | Coverage, rollout | Moyenne |
| Q7 | Baseline actuelle : % de devis → traitement avec relance humaine ? | D8 | Bloquante |
