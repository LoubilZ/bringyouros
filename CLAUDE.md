# DentalOS Voice Agent — CLAUDE.md

## Mission

Tu m'aides à construire DentalOS : un voice agent en français pour cabinets dentaires en France.

Use case prioritaire v1 : **suivi de devis non retournés** (outbound). L'agent appelle un patient ayant reçu un devis non signé pour vérifier son identité, capter où il en est avec sa mutuelle, son intention de procéder au traitement, et collecter ses disponibilités si oui — puis handoff au cabinet pour finalisation. **Aucune validation engageante côté voice.**

Volume cible pilote : ~5000 appels/mois, à valider.

Note de scoring (Vapi framework) : par rapport à un simple UC1 confirmation de RDV (Feasibility 5.0 / Impact 4.5), ce use case est un peu plus exigeant : Feasibility ~3.5 (lookup backend + multi-step flow), Impact ~4 (devis non signés = revenue leak majeur en dentisterie). C'est un **P2 Strategic Bet** dans la matrice Vapi, pas un P1 Flagship pur. Choix business assumé : à pondérer dans `decisions.md` avec les guardrails ad-hoc.

## Strategic Goal

Objectif principal : récupérer du revenue sur les devis émis mais jamais signés/retournés (revenue leak structurel en dentisterie).

**Métrique principale** : taux de conversion devis émis → traitement démarré, mesuré sur N jours après émission, avant/après déploiement.

**Seuil de succès pilote** (à fixer avant le premier appel) : le pilote réussit si le taux de conversion devis → traitement atteint X% (baseline humaine actuelle : Y%, à mesurer). Échec si < Z%. Les valeurs X, Y, Z doivent être documentées dans `docs/decisions.md` avant go-live.

**Comparison methodology** : before/after sur le cabinet pilote (A/B impraticable avec un seul cabinet). Période de référence pré-agent ≥ 3 mois. Contrôler les facteurs externes (saisonnalité, changement de praticien, campagne marketing).

**Secondary metrics** (à surveiller, à ne PAS optimiser au détriment de la qualité de la conversion) :
- taux d'identification réussie du patient
- taux de joignabilité (% appels aboutis)
- taux d'intention "oui je veux procéder"
- taux de collecte de disponibilités
- taux de handoff cabinet réussi
- handle time
- transfer rate

**Guardrail metrics** (à minimiser absolument) :
- intentions mal capturées (patient pensait dire non, marqué oui ou inverse)
- patients ayant ressenti une pression commerciale (proxy : opt-out, plaintes)
- réponses agent perçues comme un conseil médical
- estimations de remboursement mutuelle (interdites — voir Safety Rules)
- patients demandant un humain non servis
- opt-out / refus d'enregistrement
- incidents PHI/logging
- échecs d'identité (faux match → action sur le mauvais patient)

## Scope V1

V1 = **suivi outbound de devis non retournés uniquement**.

**Coverage scope v1** :
- Canal : téléphone uniquement
- Langue : français uniquement
- Horaires d'appel : lundi-vendredi 10h-13h / 14h-20h (décret 2022-1313)
- Backup humain : disponible pendant les horaires d'appel (secrétariat cabinet)
- Volume pilote : ~250 appels/jour ouvré (5000/mois)

Le système connaît au moment de l'appel :
- le cabinet
- l'identifiant opaque du devis
- la date d'émission du devis
- la **catégorie de traitement** (label court contrôlé, défini par le cabinet à l'émission du devis : ex `orthodontie`, `implant`, `couronne`, `blanchiment`, `parodontie`). **Pas** de codes d'actes, **pas** de montants.
- le **nom du praticien** émetteur (ex "Dr Martin")
- le numéro à appeler
- une référence patient interne (id opaque)

L'agent doit, dans cet ordre :

1. **Annonce** : se présenter, mentionner le cabinet, annoncer l'enregistrement, motif de l'appel en utilisant catégorie + praticien **une seule fois** ("vous avez reçu le X un devis du Dr Martin pour un traitement d'orthodontie"). Ne pas redire la catégorie ni le nom à chaque tour.
2. **Vérification d'identité** : demander nom, prénom, date de naissance ; faire un appel backend `verify_patient_identity(name, surname, dob, devis_id)` qui retourne match/no-match. **Pas plus de 2 tentatives**, sinon raccrochage poli avec rappel cabinet proposé.
3. **Question mutuelle** : "Avez-vous eu un retour de votre mutuelle ?" → enregistrer **oui / non / je ne sais pas**. Ne rien estimer, ne rien interpréter.
4. **Question intention** : "Souhaitez-vous procéder au traitement ?" → enregistrer **oui / non / je réfléchis encore**.
5. **Si oui** : "Quelles sont vos disponibilités ?" → collecter 1-3 créneaux préférés en texte structuré (ex : "matins en semaine", "mardi 11h ou jeudi 16h"). Pas de booking côté voice : juste capture + handoff.
6. **Clôture** : récapituler ce qui est noté, indiquer que le cabinet rappelle pour finaliser, remercier, raccrocher.

**Confirmation progressive** : chaque slot critique reçoit un **echo immédiat** au moment de la collecte (pas seulement au récap final). Slots critiques : (1) résultat identité, (2) réponse mutuelle, (3) intention de traitement, (4) disponibilités. L'étape 6 (récap) complète la confirmation progressive, elle ne la remplace pas. Handle time n'est JAMAIS optimisé au détriment de la précision des slots.

Côté outputs : produire un `CallOutcome` structuré contenant identité vérifiée (oui/non), réponse mutuelle, intention, disponibilités, et tag d'escalade éventuel. Pousser dans une outbox transactionnelle vers le cabinet (CRM/secrétariat).

L'agent ne doit pas :
- expliquer ou commenter le contenu du devis (actes, montants)
- estimer un remboursement mutuelle
- conseiller sur l'opportunité du traitement
- modifier le devis, négocier un tarif, proposer une alternative
- prendre/modifier/annuler un RDV de manière autonome (juste collecter intentions/disponibilités → handoff)
- gérer un inbound généraliste
- faire du triage clinique
- répondre à une question médicale
- créer un nouveau patient
- collecter des données non nécessaires au flow ci-dessus

## Out Of Scope V1

Exclusions explicites :
- Tout flow non lié au suivi de devis (RDV confirmation, prise de RDV, annulation, urgence, etc. — peuvent revenir en v2+)
- E-signature engageante côté voice (eIDAS hors scope v1)
- Estimation de remboursement mutuelle
- Conseil clinique sur le traitement
- Négociation tarifaire ou modification du devis
- Lecture du contenu du devis (actes, montants détaillés) à voix haute
- Inbound généraliste
- Triage clinique
- Vérification assurance/CPAM côté voice (rester sur déclaratif patient)

Si le patient demande autre chose que ce qui est dans le flow :
- reconnaître brièvement la demande
- ne pas traiter au fond
- proposer rappel cabinet ou message au secrétariat
- journaliser le motif hors-scope

## Non-Negotiable Safety Rules

L'agent ne doit JAMAIS :
- diagnostiquer
- recommander un médicament
- interpréter un symptôme
- dire qu'un symptôme est "normal"
- rassurer médicalement
- décider d'une urgence
- donner une consigne clinique personnalisée

**Spécifique au use case devis (v1)**, l'agent ne doit JAMAIS non plus :
- conseiller le patient sur l'opportunité ou la qualité du traitement proposé
- expliquer un acte du devis ("c'est nécessaire", "c'est la meilleure option", etc.)
- estimer ou commenter le remboursement de la mutuelle ("vous serez remboursé à X%")
- exercer de pression commerciale ("c'est urgent", "ne tardez pas", "vous perdez votre place")
- rassurer sur le coût ou comparer à d'autres options
- lire à voix haute le contenu détaillé du devis (actes, montants par acte)
- **extrapoler à partir de la catégorie ou du nom du praticien** : la catégorie est un label de référence, pas un sujet de discussion. Exemples interdits : "l'orthodontie dure généralement X mois", "Dr Martin est très bon pour ça", "les implants sont souvent remboursés", etc. Si le patient pose une question sur la catégorie ou le praticien : redirection cabinet.

Le ton doit rester **consultatif et neutre**. L'agent informe, capture, redirige. Il ne vend pas.

**Règle anti-pression** : les réponses « non » et « je réfléchis encore » à l'étape intention sont des **fins de conversation**, pas des débuts de persuasion. L'agent enregistre la réponse, passe directement au récap, et clôture. Interdiction de : reformuler la question intention, ajouter un argument, mentionner une deadline ou une urgence, utiliser un vocabulaire de rareté (« dernières places », « offre limitée »). Guardrail metric : nombre de tours agent après un « non » ou « je réfléchis » → cible 0 (récap + clôture uniquement).

**Règle zero-content redirect** : tout sujet hors-scope reçoit un acknowledge + redirect **sans contenu informatif intermédiaire**. Format strict : « Je comprends votre question. Pour cela, je vous invite à contacter directement le cabinet [nom] au [numéro]. Ils pourront vous renseigner. » Le LLM ne doit JAMAIS tenter une réponse partielle, une estimation, ou un « en général... » sur un sujet hors scope.

**Si le patient mentionne** : urgence vitale, difficulté à respirer ou avaler, saignement important, perte de connaissance, fièvre avec gonflement, ou douleur insupportable :
- interrompre le flow immédiatement
- utiliser une phrase auditée de redirection vers 15/112 (ou cabinet selon règle validée)
- ne pas improviser la formulation
- marquer l'appel comme `escalade_securite`

Les guardrails doivent tourner à **chaque tour** de conversation, pas seulement au premier message.

## Compliance — RGPD + HDS

Contraintes non négociables :
- RGPD applicable dès le pilote
- HDS à valider pour tout hébergement ou traitement de données de santé identifiantes
- Aucun vendor ne reçoit de données patient identifiantes sans validation explicite
- DPA RGPD requis pour les sous-traitants
- Résidence des données en UE à vérifier pour STT/TTS/LLM/SIP/hosting
- Rétention minimale, documentée
- Logs sans PHI en clair
- Registre sous-traitants dans `docs/dpa-registry.md`

**Important** : EU residency ≠ HDS ≠ conformité suffisante. Pour chaque vendor candidat, vérifier explicitement :
- docs officielles à jour
- DPA
- résidence des données
- sous-traitants
- politique de rétention
- chiffrement
- statut HDS ou justification d'architecture sans données de santé identifiantes

## Outbound Telephony Rules

**Calling hours** : appels outbound uniquement lundi-vendredi 10h-13h / 14h-20h (décret 2022-1313, art. 3). Aucun appel le week-end, les jours fériés, ou hors de ces plages. Vérification Bloctel : le numéro du patient doit être vérifié contre la liste Bloctel avant appel. Exception potentielle : « relation contractuelle préexistante » (patient ayant reçu un devis du cabinet). À valider juridiquement en Session 1 et documenter dans `docs/decisions.md`.

**Permission question** : dans les 10 premières secondes, après identification + motif + annonce d'enregistrement, l'agent demande : « Est-ce un bon moment pour en parler ? ». Si « non » → proposition de rappel + collecte créneau préféré → clôture. Si hostilité (« arrêtez de m'appeler ») → exit gracieux immédiat, marquage opt-out.

**AMD / Voicemail strategy** : utiliser la détection AMD (Answering Machine Detection) native LiveKit pour classifier chaque appel (human / machine-vm / machine-ivr / machine-unavailable). Si répondeur détecté :
- Laisser un **message vocal fixe audité** (template versionné dans `prompts/voicemail_template.txt`) : nom du cabinet + « nous avons essayé de vous joindre » + numéro de rappel. **Durée < 15 secondes.**
- **JAMAIS** de catégorie de traitement, de nom de praticien, ou de mention du mot « devis » dans le message vocal (PHI potentiel sur répondeur partagé).
- Le message est un template fixe, **non généré par le LLM**.
- Retry policy : max 2 tentatives espacées de 24h minimum, puis abandon avec tag `patient_injoignable`.

**Callback scenario** : le numéro outbound ne doit PAS être configuré avec un agent inbound conversationnel en v1. Un message vocal fixe redirige vers le cabinet : « Vous avez été contacté par le cabinet [nom]. Merci de les rappeler au [numéro du cabinet]. » Toute demande de handler inbound = scope v2, documentée dans `docs/backlog-v2.md`.

**Number reputation** : warm-up progressif (50 appels/jour → montée sur 2 semaines), CNAM/caller-ID configuré au nom du cabinet, monitoring des spam flags. À intégrer dans la checklist telephony de `docs/v1-scope.md`.

**Attente media path** : ne JAMAIS déclencher de speech (`on_enter`, `session.say()`, `generate_reply()`) avant confirmation que `sip.callStatus == 'active'` dans les participant attributes ET stabilisation du media path. Risques documentés : agent parle avant décrochage (Q3 #2), greeting perdu (Q3 #10).

## Data Minimization

Le voice agent ne reçoit que les champs nécessaires au flow de suivi de devis.

**Inputs système autorisés** (pré-chargés au démarrage de l'appel) :
- identifiant opaque du devis
- date d'émission du devis
- catégorie de traitement (label court contrôlé : `orthodontie`, `implant`, `couronne`, `blanchiment`, `parodontie`, etc.)
- nom du praticien émetteur (ex "Dr Martin")
- numéro à appeler (hashé en stockage, jamais loggé en clair)
- nom du cabinet
- référence patient interne (id opaque)

> Note sur la catégorie + praticien : ce sont des **labels de référence** mentionnés une seule fois en annonce pour aider le patient à se rappeler de quel devis on parle. Ils ne servent pas de contexte au LLM pour raisonner sur le traitement. La catégorie doit être tirée d'une liste contrôlée (enum) côté cabinet, pas d'un texte libre.

**Inputs collectés du patient** (pendant l'appel, pour vérification d'identité) :
- nom
- prénom
- date de naissance (DOB)

> ⚠️ Le DOB est nécessaire pour la vérification d'identité avec le backend (`verify_patient_identity`). C'est une exception assumée à la règle générale "pas de DOB". Contraintes :
> - **Input-only** : jamais relu à voix haute par l'agent
> - **Pas dans les logs en clair** : seul un flag `identity_match: bool` est loggé, pas la valeur DOB
> - **Hashé en mémoire** dès que possible pour le lookup, pas conservé en clair plus longtemps que la durée du tour
> - **Pas de stockage long terme** côté infra voice : la valeur sert au lookup, n'est pas persistée

**Outputs collectés du patient** (réponses libres, à structurer) :
- statut retour mutuelle : `oui` / `non` / `je ne sais pas`
- intention de traitement : `oui` / `non` / `je réfléchis`
- disponibilités préférées (texte libre court, ex : "matins en semaine")

**Champs interdits sans validation explicite** :
- contenu détaillé du devis (actes, montants par acte) — l'agent ne doit pas le recevoir
- motif clinique du traitement
- historique patient / notes praticien
- NIR
- numéro/identifiant assurance ou mutuelle
- adresse postale complète
- documents médicaux ou pièces jointes
- contenu médical libre

**Règles transverses** :
- Les données patient sont **input-only** : ne jamais relire à voix haute une donnée identifiante (sauf prénom dans la salutation, validé)
- Les champs sensibles sont chiffrés au repos
- Les numéros de téléphone sont hashés avec salt pour les lookup caller-ID, jamais loggés en clair
- Tous les logs applicatifs passent par un middleware de redaction PHI

**Processus d'ajout de champ** : les listes ci-dessus sont un **contrat fermé**. Tout ajout de champ aux inputs système, inputs patient, ou outputs collectés nécessite :
1. Justification écrite de nécessité dans `docs/decisions.md`
2. Analyse d'impact RGPD (le champ est-il une donnée de santé ? une donnée sensible ?)
3. Mise à jour du registre `docs/dpa-registry.md` si nouveau sous-traitant impliqué
4. Validation humaine explicite
Pas de collecte « nice to have ». Pas de champ ajouté « pour plus tard ».

## Stack

**Stack TBD.** Aucun choix technique structurant n'est validé au démarrage : SIP provider, voice platform, STT, TTS, LLM, hosting, state store, DB, observability, calendrier/EHR connector.

> Note importante : un RAG dev-time ciblé LiveKit (docs + forum) a été construit. Un choix de plateforme voix non-LiveKit réduirait fortement la valeur du RAG sur les questions techniques. À pondérer en session 1, sans pour autant fermer la porte si une autre option est objectivement meilleure pour les contraintes RGPD/HDS/coût/latence.

Ne pas écrire de code stack-specific avant décision documentée et validée. Toute hypothèse passe par `docs/decisions.md` avec options, choix recommandé, justification, risques, sources, points compliance ouverts.

## Knowledge Base — `search_livekit_kb`

Tu as accès à un RAG dev-time via MCP : `search_livekit_kb(query, top_k, source_type)`.

Corpus :
- `source_type: "docs"` — 521 pages docs.livekit.io
- `source_type: "forum"` — 696 threads community.livekit.io
- `source_type: "vapi_book"` — 9 chapitres Vapi Playbook (stratégie produit)

**Utilisation proactive obligatoire** :
- API/paramètre/pattern LiveKit → `docs`
- message d'erreur, bug suspect → `forum`
- décision produit/scoping/métriques → `vapi_book`
- sujet hybride → sans filtre

**Patterns de queries efficaces** :
- "How to do X with LiveKit Agents Python" → code + retours
- "Common errors with X" → forum threads avec solutions
- "Best practices for X in voice agents" → mix doc + Vapi
- "{message d'erreur exact}" → trouve souvent un thread forum avec fix

**Anti-pattern** : ne jamais inventer un nom d'API, paramètre ou comportement LiveKit sans vérification RAG. En cas de doute : search d'abord, propose ensuite.

**Limite** : le RAG est une aide technique et produit, **pas une source de vérité compliance/vendor**.

## Source Hierarchy

Hiérarchie quand des sources se contredisent :
1. Docs officielles à jour du vendor concerné
2. Documentation légale/compliance officielle du vendor
3. Docs LiveKit officielles via RAG
4. Forum LiveKit (hypothèses / debug uniquement)
5. Vapi Playbook (cadrage produit, jamais pour valider une API ou obligation légale)

Si une source contredit ce brief : flag la contradiction avant de modifier le code.

## Decision Process

Avant toute décision structurante :
1. Chercher dans le RAG si pertinent
2. Vérifier docs officielles vendor si vendor/compliance
3. Proposer options A/B/C
4. Recommander une option
5. Lister risques et inconnues
6. Attendre validation humaine
7. Seulement ensuite écrire dans `docs/decisions.md`

**Demande validation explicite avant de** :
- choisir STT/TTS/LLM/SIP/hosting/voice platform
- modifier la structure du repo
- ajouter une dépendance
- changer le scope v1
- créer un connecteur EHR/calendrier
- toucher `docs/decisions.md`, `docs/v1-scope.md`, `docs/dpa-registry.md`

## Decision Log Template

Format dans `docs/decisions.md` :

    ## YYYY-MM-DD — Titre

    **Contexte** :
    ...

    **Options considérées** :
    - A
    - B
    - C

    **Choix recommandé** :
    ...

    **Décision validée** :
    ...

    **Justification** :
    ...

    **Risques** :
    ...

    **Questions ouvertes** :
    ...

    **Sources** :
    - URL ou résultat RAG

## Session 1 Goal

Session 1 = **cadrage stack + cadrage produit**. Pas de code avant validation de `docs/decisions.md` et `docs/v1-scope.md`.

Session 1 est terminée seulement si :
- thin slice v1 décrit end-to-end
- stack candidate documentée composant par composant
- données patient manipulées inventoriées
- vendors et sous-traitants potentiels listés
- risques RGPD/HDS ouverts listés explicitement
- métriques pilote définies (principale + secondary + guardrail)
- **seuil numérique de succès fixé** (X%, Y% baseline, Z% minimum)
- **comparison methodology documentée** (before/after, période de référence)
- baseline humaine à mesurer définie
- critères d'escalade définis
- **coverage scope documenté** (canal, langue, horaires, backup humain)
- **AMD / voicemail strategy décidée** (leave/retry, template)
- **callback scenario décidé** (message fixe, pas d'inbound)
- **calling hours / Bloctel vérifié** (exception relation contractuelle validée juridiquement ou flaggée comme bloquante)
- **risques techniques outbound loggés** dans `docs/decisions.md` (top 10 Q3)
- **justification P2-first documentée** ou P1 stepping stone identifié
- questions bloquantes isolées pour validation humaine

## Architecture Principles

- Le **trunk SIP** est stateless (config). L'**`AgentSession`** LiveKit est stateful (lifecycle, ChatContext, état de la conversation). Si une persistence/recovery cross-session est nécessaire, un state store externe est un ajout custom au-dessus du SDK.
- Chaque appel crée un `CallLog` dès le début (y compris appels courts, abandonnés, échoués). LiveKit émet des logs natifs (job ID, worker ID) ; le `CallLog` applicatif est un enrichissement custom.
- Un fallback mémoire est acceptable en dev uniquement, jamais en prod ou multi-worker
- Toute action ambiguë ou sensible reste provisoire — seul un humain valide une modification de RDV, une annulation, ou une action hors confirmation simple
- Les mocks restent isolés dans `tests/` ou `adapters/dev`, jamais dans le code métier

**Verrouillage flow v1** : les 6 étapes du flow (annonce → identité → mutuelle → intention → disponibilités → clôture) sont un **contrat**, pas une suggestion. Tout ajout d'étape, d'intent, ou de capability passe par le decision process complet et est capté dans `docs/backlog-v2.md` en attendant.

**Capability level cap** : l'agent v1 est strictement **Level 2** (read-only lookup + collecte déclarative). Aucun tool de write (booking, modification, annulation) n'est exposé au LLM en v1. Toute montée Level 3+ requiert une décision documentée et une montée de version.

**Tool-first-truth** : l'agent ne confirme JAMAIS une action au patient (identité vérifiée, données transmises, cabinet prévenu) avant le retour positif du tool backend correspondant. Si le tool timeout ou échoue, l'agent ne doit pas narrer un succès. Chaque tool contract mappe explicitement ses codes d'erreur vers une réponse parlée et une action suivante.

## Runtime Rules

Pour les flows patient-facing v1 :
- température 0.0 par défaut
- prompts versionnés
- réponses courtes et naturelles en français
- pas de jargon technique
- pas de PHI dans les logs
- pas de décision clinique
- pas de scope creep conversationnel

Toute hausse de température doit être justifi��e et validée. Ne jamais optimiser latency/cost au détriment de : sécurité, conformité, exactitude du statut RDV, expérience patient.

## Turn Detection & Interruptions

**VAD** : Silero VAD obligatoire. Pour le français : `MultilingualModel()` recommandé (meilleur endpointing que le modèle anglais par défaut).

**Politique d'interruption par étape** :
- Annonce d'enregistrement (début étape 1) : `allow_interruptions=False` — l'annonce légale doit être entendue en entier
- Questions fermées (identité, mutuelle, intention) : adaptive interruption si disponible, sinon VAD avec `min_words=1`, `min_duration=0.5s`
- Récapitulatif (étape 6) : `allow_interruptions=False` — le patient doit entendre le récap complet pour valider

**Fallback** : si l'adaptive interruption crash (erreur documentée Q3 #4), le système doit fonctionner correctement en VAD-only. Ne pas dépendre de l'adaptive pour la correction du flow. Paramètres fallback : `min_endpointing_delay=0.5s`, `max_endpointing_delay=1.5s`.

**Noise cancellation** : activer `noise_cancellation.BVC()` (Background Voice Cancellation) dans `RoomInputOptions`. Les appels téléphoniques outbound ont souvent du bruit ambiant côté patient.

**Latence cible** : TTFT (Time To First Token) end-to-end < 800ms. Benchmark obligatoire avant go-live.

## Code Style

- Python 3.11+ si backend Python retenu
- Type hints partout
- Async/await natif
- Pydantic pour inputs structurés (function tools)
- Logs structurés JSON en prod, redaction PHI obligatoire, correlation ID / call ID
- Tests pytest

Tests à prévoir :
- unit tests flows
- tests guardrails (chaque tour)
- tests no-PHI logs
- tests scénario confirmation
- tests escalade hors scope
- tests appels courts / erreurs / abandon
- evals conversationnelles séparées des unit tests
- **tests scope creep** : 20 questions hors-scope (assertion : zéro contenu informatif dans la réponse), 10 questions-piège catégorie/praticien (assertion : redirection cabinet uniquement), scénarios pression post-refus (assertion : 0 tour de persuasion après « non » / « je réfléchis »)
- **tests tool contracts** : preconditions machine, error taxonomy complète, tool-first-truth (pas de confirmation avant retour tool)

## Repo Structure (indicative)

À ne pas créer avant validation Session 1.

    dental-voice-agent/
    ├── CLAUDE.md
    ├── README.md
    ├── .env.example
    ├── agents/                 # AgentSession definitions, prompts
    ├── tools/                  # function tools (lookup_appointment, mark_confirmed, send_sms_link)
    ├── prompts/                # system prompts versionnés
    ├── tests/
    │   ├── unit/
    │   └── scenarios/          # eval suites end-to-end
    ├── infra/                  # config SIP, deploy
    └── docs/
        ├── decisions.md        # journal des choix + sources
        ├── v1-scope.md         # thin slice spec
        ├── dpa-registry.md     # registre RGPD sous-traitants
        └── runbooks/

La structure est indicative. Pas de fichier provider-specific avant décision documentée.

## Communication With Me

- Tutoiement, en français
- Concis sauf si je demande un raisonnement détaillé
- Quand tu hésites entre 2 options structurantes : ne devine pas, expose le tradeoff, recommande une option, demande validation
- Quand une décision n'est pas évidente : cite les sources RAG ou docs inline, distingue clairement fait / hypothèse / recommandation

En cas de doute :
1. Relis la section pertinente de `CLAUDE.md`
2. Cherche dans le RAG
3. Regarde les patterns existants du repo
4. Propose une décision si nécessaire

N'invente pas un nouveau pattern si un pattern comparable existe déjà.
