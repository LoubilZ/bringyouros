# Q4 — Risques de scope creep spécifiques au use case devis dental

Date : 2026-05-01
Source RAG : `search_livekit_kb(source_type: None)` — 3 corpus (docs, forum, vapi_book)

---

## Risques identifiés

### 1. Injection de fonctionnalités par les parties prenantes

**Mécanisme de dérive** : Lors du cadrage, chaque interlocuteur ajoute « et si l'agent pouvait aussi… ? ». Chaque suggestion est raisonnable isolément, mais la somme transforme un pilote de 6 semaines en projet de 6 mois.

**Exemple RAG** : « Within the first thirty minutes, the scope had already started expanding. Could the agent also troubleshoot installation errors? What about drivers who needed help with other apps? What if a driver asked about their insurance status? Every suggestion was reasonable. And every one of them would have turned a six-week pilot into a six-month project. » — Vapi Playbook, Part 2 Discovery ([Notion](https://www.notion.so/352bd1f88e0e80d2a5eeeb923440a036))

**Déclinaison DentalOS** : « Et si l'agent pouvait aussi confirmer le RDV ? », « Et s'il prenait le RDV directement ? », « Et s'il vérifiait la couverture mutuelle ? ». Chaque ajout est un nouveau flow, un nouveau tool contract, de nouveaux tests.

**Guardrail CLAUDE.md** :
> Toute demande d'ajout d'intent ou de capability pendant le pilote v1 est captée dans `docs/backlog-v2.md`, jamais implémentée sans passage par le decision process (options A/B/C → validation humaine). Les 6 étapes du flow v1 sont verrouillées : annonce → identité → mutuelle → intention → disponibilités → clôture. Aucun ajout d'étape sans décision documentée.

---

### 2. Escalade du capability ladder (Level 2 → Level 5)

**Mécanisme de dérive** : L'agent v1 est conçu Level 2-3 (read-only + collecte simple). La tentation est de le pousser vers Level 4-5 (workflow multi-step, suggestions proactives, rétention) pour « maximiser la conversion ».

**Exemple RAG** : « Level 5 is proactive and optimizing. The agent suggests alternatives, offers retention deals, and identifies cross-sell opportunities. Requires business rules and guardrails to prevent overreach. Start at Level 2 or 3. Prove the technology works. Build operational confidence. Then climb. » — Vapi Playbook, Part 1 Strategy ([Notion](https://www.notion.so/352bd1f88e0e8003acd6e866ba01116b))

**Déclinaison DentalOS** : L'agent passe de « capturer l'intention » à « convaincre le patient de procéder » — proposer des facilités de paiement, comparer des mutuelles, argumenter sur les bénéfices du traitement. Chaque pas vers Level 5 = pression commerciale = violation des safety rules.

**Guardrail CLAUDE.md** :
> L'agent v1 est strictement Level 2 (read-only lookup + collecte déclarative). Toute capability Level 3+ (write access, booking, modification de devis, suggestion proactive) est interdite sans décision documentée et montée de version. Le ton reste « consultatif et neutre » — jamais incitatif, jamais argumentatif.

---

### 3. Scénario blended : le patient rappelle le numéro sortant

**Mécanisme de dérive** : L'agent outbound laisse un appel manqué. Le patient rappelle. Sans handler inbound, soit l'appel tombe dans le vide, soit un mini-agent inbound est bricolé à la va-vite, élargissant le scope.

**Exemple RAG** : « Outbound becomes inbound. You call a customer, they miss it, they call back. Now your inbound agent needs to handle "I got a call from this number." Marcus discovered this gap when drivers started calling back the number that had called them. The inbound agent had no idea why they were calling. » — Vapi Playbook, Part 3 Design ([Notion](https://www.notion.so/352bd1f88e0e80809c5cd5f16691d113))

**Déclinaison DentalOS** : Le patient rappelle, tombe sur rien ou sur un agent non prévu. Solution scope-safe : message vocal fixe (« Vous avez été contacté par le cabinet X au sujet d'un devis. Merci de rappeler le cabinet au 0X.XX.XX.XX.XX »), pas un agent conversationnel inbound.

**Guardrail CLAUDE.md** :
> Le numéro outbound ne doit PAS être configuré avec un agent inbound conversationnel en v1. Un message vocal fixe redirige vers le cabinet. Toute demande de handler inbound = scope v2, documentée dans `docs/backlog-v2.md`.

---

### 4. Hallucination tool / confirmation prématurée

**Mécanisme de dérive** : Le LLM confirme une action avant que le tool backend ne la valide. Ou il invente un comportement pour combler un gap dans le tool contract (timeout, erreur non mappée).

**Exemple RAG** : « The LLM will hallucinate behavior for any gap left undefined in the tool contract. [...] Marcus pulled the logs. The SMS gateway had timed out. The API never returned a success response. But the agent had already said the link was sent. » — Vapi Playbook, Part 4 Build ([Notion](https://www.notion.so/352bd1f88e0e8089bd48d517598d7a7c)). Aussi : « Tool-first truth. Never narrate success before a tool confirms it. » — Part 3 Design.

**Déclinaison DentalOS** : L'agent dit « c'est noté, le cabinet va vous rappeler pour fixer un RDV » alors que le `CallOutcome` n'a pas été correctement poussé dans l'outbox. Ou pire : l'agent dit « votre identité est vérifiée » avant le retour de `verify_patient_identity`.

**Guardrail CLAUDE.md** :
> Règle tool-first-truth : l'agent ne confirme JAMAIS une action (identité vérifiée, données transmises au cabinet) avant le retour positif du tool correspondant. Chaque tool contract doit mapper explicitement les codes d'erreur (PATIENT_NOT_FOUND, TIMEOUT, IDENTITY_MISMATCH) vers une réponse parlée et une action suivante. Aucun gap non mappé.

---

### 5. Extrapolation à partir des métadonnées (catégorie + praticien)

**Mécanisme de dérive** : Le LLM utilise la catégorie de traitement et le nom du praticien comme contexte pour raisonner, générant des commentaires médicaux, des comparaisons, ou des informations inventées.

**Exemple RAG** : « Never invent information. If the agent doesn't know something, it should say so. "I don't have that information, but I can connect you with someone who does" is always better than a guess. » — Vapi Playbook, Part 3 Design ([Notion](https://www.notion.so/352bd1f88e0e80809c5cd5f16691d113)). Aussi : « For medical, legal, or financial topics, provide general information only and suggest consulting a qualified professional. » — LiveKit Docs, Prompting.

**Déclinaison DentalOS** : « L'orthodontie dure généralement 18 mois », « Dr Martin est spécialiste en implantologie », « les implants sont souvent bien remboursés ». Tout cela est soit faux, soit du conseil médical, soit les deux.

**Guardrail CLAUDE.md** :
> (Existe déjà, renforcer) La catégorie et le praticien sont des **tokens de référence** utilisés une seule fois en annonce. Le system prompt doit inclure une instruction explicite : « Tu ne connais RIEN sur la catégorie au-delà de son label. Tu ne connais RIEN sur le praticien au-delà de son nom. Toute question sur le contenu, la durée, le coût, la qualité → redirection cabinet. » Test obligatoire : scenario eval avec 10 questions-piège sur la catégorie.

---

### 6. Absorption FAQ / knowledge base

**Mécanisme de dérive** : Pour « améliorer l'expérience patient », on injecte des FAQ dans le contexte de l'agent (horaires du cabinet, plans d'accès, liste des praticiens, tarifs). Le contexte gonfle, la latence augmente, et l'agent commence à répondre à des questions hors scope.

**Exemple RAG** : « I've been plugging the whole FAQ knowledge into the agent context, and that was fine to start, but this has grown to a point where our context is mainly dominated by them. 300 = base, 1100 = agent, 3500 = FAQs. This obviously hurts latency. » — Forum LiveKit, [Best practice to answer FAQs](https://community.livekit.io/t/best-practice-to-answer-faqs-speed-accuracy/504)

**Déclinaison DentalOS** : Le cabinet demande « et si l'agent pouvait aussi donner les horaires ? le plan d'accès ? les tarifs des consultations ? ». Chaque FAQ ajoutée éloigne l'agent de son flow devis et gonfle le contexte LLM.

**Guardrail CLAUDE.md** :
> Zéro FAQ dans le contexte de l'agent v1. L'agent ne connaît que les données pré-chargées pour l'appel en cours (identifiant devis, catégorie, praticien, cabinet). Toute question hors flow → « Je vous invite à contacter directement le cabinet au [numéro]. » Pas de RAG patient-facing en v1.

---

### 7. Dérive revenue → pression commerciale

**Mécanisme de dérive** : L'objectif principal est « récupérer du revenue sur les devis non signés ». La tentation naturelle est d'optimiser agressivement : relancer les « je réfléchis », reformuler les refus, ajouter de l'urgence (« votre devis expire bientôt »).

**Exemple RAG** : « Should the agent spend an extra thirty seconds confirming the customer is satisfied, or move efficiently to the next call? [...] When two priorities conflict, you need to know which one wins. » — Vapi Playbook, Part 1 Strategy. « Hostile ("Stop calling me") needs a graceful exit. Respect the request and end the call. » — Part 3 Design ([Notion](https://www.notion.so/352bd1f88e0e80809c5cd5f16691d113))

**Déclinaison DentalOS** : L'agent ajoute « c'est vraiment important pour votre santé dentaire », « le devis est valable encore X jours », « beaucoup de patients regrettent d'avoir attendu ». Chaque formulation est une pression commerciale déguisée, en violation des safety rules.

**Guardrail CLAUDE.md** :
> (Renforcer l'existant) La réponse « non » ou « je réfléchis » à l'étape intention est une **fin de conversation**, pas un début de persuasion. L'agent enregistre la réponse, récapitule, propose que le cabinet reste disponible, et clôture. Interdiction de : reformuler la question intention, ajouter un argument, mentionner une deadline, utiliser un vocabulaire de rareté ou d'urgence. Guardrail metric : % d'appels où l'agent a plus d'un tour après un « non » ou « je réfléchis » → doit tendre vers 0.

---

### 8. Tool call inattendu / appel de tool fantôme

**Mécanisme de dérive** : Le LLM appelle un tool qui ne devrait pas exister dans le contexte, ou appelle un tool valide avec des paramètres hallucin és. Le tool contract est techniquement respecté mais l'action est non souhaitée.

**Exemple RAG** : « Unexpected tool calls are usually related to the prompt — ensure you have observability whenever a tool call is invoked (ask the LLM to explain why it called the tool). Using state machines for the conversation state can also eliminated unexpected tool calls. » — Forum LiveKit, [Critical: AI Agent Unexpectedly Ending Interview](https://community.livekit.io/t/critcal-ai-agent-unexpectedly-ending-interview-mid-session/626). Aussi : « The agent had a function tool to disconnect the call, and that is getting called, but the user did not say something that would cause that tool to get called. »

**Déclinaison DentalOS** : L'agent appelle `verify_patient_identity` avant d'avoir collecté les 3 champs (nom, prénom, DOB), ou appelle un tool de booking qui n'est pas censé exister en v1, ou appelle le tool d'identité une 3e fois malgré la limite de 2.

**Guardrail CLAUDE.md** :
> Chaque tool exposé au LLM a une **precondition machine** (pas seulement prompt) : `verify_patient_identity` n'est callable que si les 3 champs sont non-null. Aucun tool de write (booking, modification, annulation) n'est exposé au LLM en v1 — pas dans le prompt, pas dans la liste d'outils. Logger chaque tool call avec le motif LLM pour audit. Utiliser `ToolFlag.IGNORE_ON_ENTER` (LiveKit) pour les tools qui ne doivent pas être appelés au premier tour.

---

### 9. Expansion des données collectées

**Mécanisme de dérive** : « Pour mieux servir le patient », on collecte des données supplémentaires : adresse, numéro de mutuelle, historique médical, préférences praticien. Chaque champ ajouté augmente la surface RGPD et le risque de non-conformité HDS.

**Exemple RAG** : « Voice agents create a data surface most enterprise security teams haven't mapped. Call recordings are audio files containing spoken PII. Transcripts are searchable text versions of those recordings. LLM context windows contain the conversation history. Tool call logs record the actions taken. [...] Most teams focused on the conversation design. Sandra focused on where the data went afterward. » — Vapi Playbook, Part 4 Build ([Notion](https://www.notion.so/352bd1f88e0e8089bd48d517598d7a7c))

**Déclinaison DentalOS** : « Et si on collectait aussi le numéro de mutuelle pour accélérer ? », « Et son adresse pour la correspondance ? ». Chaque champ ajouté = nouvelle donnée à protéger, nouveau risque RGPD, nouveau point d'audit HDS.

**Guardrail CLAUDE.md** :
> (Renforcer l'existant) La section Data Minimization est un **contrat fermé**. Tout champ ajouté aux inputs ou outputs nécessite : (1) justification écrite de nécessité dans `decisions.md`, (2) analyse d'impact RGPD, (3) mise à jour du registre `dpa-registry.md`, (4) validation humaine. Pas de collecte « nice to have ».

---

### 10. Skip de la confirmation progressive

**Mécanisme de dérive** : Pour réduire le handle time, l'agent enchaîne les étapes sans confirmer les slots critiques. Le patient dit « oui » par défaut sans avoir compris la question, et l'intention est mal capturée.

**Exemple RAG** : « The agent was rushing elderly patients through the confirmation step. It spoke quickly, confirmed the date and time in one breath, and moved on before patients had processed the information. Patients said "yes" because they didn't want to slow down the call, not because they'd understood the details. » — Vapi Playbook, Part 7 Operate ([Notion](https://www.notion.so/352bd1f88e0e8055b079c3919af7049f)). Aussi : « Confirm every slot that would be expensive to get wrong. » — Part 3 Design.

**Déclinaison DentalOS** : L'intention (oui/non/je réfléchis) est le slot le plus critique. Si mal capturé, le cabinet rappelle un patient qui ne veut pas procéder, ou ne rappelle pas un patient qui veut. Damage direct sur la guardrail metric « intentions mal capturées ».

**Guardrail CLAUDE.md** :
> Les slots critiques suivants requièrent une **confirmation echo immédiate** : (1) résultat identité (« C'est bien vous, [prénom] ? »), (2) réponse mutuelle, (3) intention de traitement, (4) disponibilités. L'étape 6 (récap) ne remplace PAS la confirmation progressive — elle la complète. Handle time n'est JAMAIS optimisé au détriment de la précision des slots critiques.

---

### 11. Drift du unsupported intent handling

**Mécanisme de dérive** : L'agent est conçu pour rediriger les demandes hors scope vers le cabinet. Mais le LLM, par nature « helpful », essaie de répondre partiellement avant de rediriger — introduisant des réponses approximatives ou hors cadre.

**Exemple RAG** : « Defining [unsupported intents] explicitly prevents scope creep and anchors expectations. It doesn't mean you won't build them. It means you're not building them now. [...] Guardrails define what the agent must never do. Never make promises about service availability. Never discuss pricing or contract modifications. » — Vapi Playbook, Part 2 Discovery ([Notion](https://www.notion.so/352bd1f88e0e80d2a5eeeb923440a036))

**Déclinaison DentalOS** : Patient : « Combien coûte un implant en général ? ». Agent : « Je ne peux pas vous donner de chiffre exact, mais en général c'est entre 1000 et 3000€... Je vous invite à voir avec le cabinet. » La demi-réponse est pire que pas de réponse — elle est potentiellement fausse et constitue un avis.

**Guardrail CLAUDE.md** :
> Le handling hors-scope est **acknowledge + redirect, sans contenu intermédiaire**. Format imposé : « Je comprends votre question. Pour cela, je vous invite à contacter directement le cabinet [nom] au [numéro]. Ils pourront vous renseigner. » Le LLM ne doit JAMAIS tenter une réponse partielle sur un sujet hors scope. Test obligatoire : batterie de 20 questions hors-scope avec assertion « zéro contenu informatif dans la réponse ».

---

### 12. Voicemail content creep

**Mécanisme de dérive** : La stratégie voicemail passe de « message court standardisé » à « message personnalisé avec détails du devis » pour augmenter le taux de rappel. Le message vocal devient un mini-pitch commercial contenant des données patient.

**Exemple RAG** : « Keep it under 20 seconds. State who you are, why you're calling, and the callback number. Nothing else. Long voicemails get deleted. » — Vapi Playbook, Part 3 Design ([Notion](https://www.notion.so/352bd1f88e0e80809c5cd5f16691d113))

**Déclinaison DentalOS** : Le message voicemail évolue de « Le cabinet X a essayé de vous joindre, merci de nous rappeler au 0X » vers « Le cabinet X vous appelle au sujet de votre devis d'orthodontie du Dr Martin du 15 avril... ». Chaque détail ajouté = données de santé sur un répondeur potentiellement partagé (famille, employeur).

**Guardrail CLAUDE.md** :
> Le message voicemail est un **template fixe audité**, non généré par le LLM. Contenu maximal : nom du cabinet + « nous avons essayé de vous joindre » + numéro de rappel. JAMAIS de catégorie de traitement, de nom de praticien, ou de mention du mot « devis » dans le message vocal. Durée < 15 secondes. Le template est versionné dans `prompts/voicemail_template.txt`.

---

## Matrice de priorisation

| # | Risque | Impact si non traité | Probabilité | Où documenter |
|---|--------|---------------------|-------------|---------------|
| 1 | Injection fonctionnalités stakeholders | Pilote retardé de mois | Très haute | CLAUDE.md + decision process |
| 2 | Capability ladder Level 2→5 | Pression commerciale, plaintes | Haute | CLAUDE.md Safety Rules |
| 3 | Blended inbound callback | Patient perdu, frustration | Haute | v1-scope.md |
| 4 | Hallucination tool / confirmation prématurée | Données fausses au cabinet | Haute | v1-scope.md + tool contracts |
| 5 | Extrapolation catégorie/praticien | Conseil médical non autorisé | Haute | CLAUDE.md Safety Rules (renforcer) |
| 6 | Absorption FAQ | Latence + hors scope | Moyenne | CLAUDE.md + decision process |
| 7 | Revenue → pression commerciale | Guardrail metrics violées | Haute | CLAUDE.md Safety Rules (renforcer) |
| 8 | Tool call inattendu | Action non souhaitée | Moyenne | v1-scope.md + tool contracts |
| 9 | Expansion données collectées | Non-conformité RGPD/HDS | Haute | CLAUDE.md Data Minimization (renforcer) |
| 10 | Skip confirmation progressive | Intentions mal capturées | Moyenne | v1-scope.md |
| 11 | Drift unsupported intent handling | Réponses approximatives | Moyenne | CLAUDE.md + evals |
| 12 | Voicemail content creep | PHI sur répondeur partagé | Moyenne | v1-scope.md |

---

## Recommandations d'implémentation

### À ajouter dans CLAUDE.md

1. **Règle de verrouillage du flow v1** : les 6 étapes sont un contrat, pas une suggestion. Ajout d'étape = décision documentée.
2. **Règle tool-first-truth** : jamais confirmer avant retour tool positif.
3. **Règle zero-content redirect** : hors-scope = acknowledge + redirect, zéro contenu informatif.
4. **Règle capability level cap** : Level 2 max en v1, montée documentée.
5. **Renforcer** la section extrapolation catégorie/praticien avec instruction system prompt explicite.
6. **Renforcer** la section Data Minimization avec processus d'ajout de champ.
7. **Ajouter** guardrail metric : « tours après refus/hésitation » → cible 0.

### À ajouter dans v1-scope.md

1. **Callback scenario** : message vocal fixe, pas d'agent inbound.
2. **Voicemail template** : fixe, audité, sans PHI.
3. **Confirmation progressive** : echo immédiat sur les 4 slots critiques.
4. **Tool preconditions** : conditions machine (pas seulement prompt) pour chaque tool.
5. **Batterie de tests scope creep** : 20 questions hors-scope + 10 questions-piège catégorie.

### À créer

1. `docs/backlog-v2.md` — réceptacle formel pour toutes les demandes rejetées du v1.
2. `prompts/voicemail_template.txt` — template fixe audité.
3. `tests/scenarios/scope_creep/` — suite d'evals dédiée aux 12 risques ci-dessus.
