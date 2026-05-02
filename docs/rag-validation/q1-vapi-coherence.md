# Q1 — Cohérence CLAUDE.md vs Vapi Playbook

Date : 2026-05-01
Source RAG : `search_livekit_kb(source_type: "vapi_book")` — 9 chapitres Vapi Playbook

## Sources Notion

| Partie | URL |
|--------|-----|
| Part 1 Strategy | https://www.notion.so/352bd1f88e0e8003acd6e866ba01116b |
| Part 2 Discovery | https://www.notion.so/352bd1f88e0e80d2a5eeeb923440a036 |
| Part 3 Design | https://www.notion.so/352bd1f88e0e80809c5cd5f16691d113 |
| Part 4 Build | https://www.notion.so/352bd1f88e0e8089bd48d517598d7a7c |
| Part 5 Test | https://www.notion.so/352bd1f88e0e80b68fd5fe4f64196d75 |
| Part 6 Launch | https://www.notion.so/352bd1f88e0e8020aa5ed19fbe3bff88 |
| Part 7 Operate | https://www.notion.so/352bd1f88e0e8055b079c3919af7049f |
| Part 8 Improve | https://www.notion.so/352bd1f88e0e805d96bcee87f6712b85 |
| Part 9 Scale | https://www.notion.so/352bd1f88e0e8050a9e4f3473f0f7a73 |

---

## (a) Règles que CLAUDE.md respecte

| # | Règle Vapi Playbook | Implémentation CLAUDE.md | Source |
|---|----------------------|--------------------------|--------|
| 1 | **Un seul goal primaire** — "when two priorities conflict, you need to know which one wins" (Ch. 3) | Goal = revenue (conversion devis → traitement). Secondary metrics explicitement "à ne PAS optimiser au détriment de la conversion." | Part 1 Strategy |
| 2 | **Scoring 4 dimensions + Priority Matrix** (Ch. 7) | Scoring explicite : Feasibility ~3.5, Impact ~4, placement P2 Strategic Bet. Référence au framework. | Part 2 Discovery |
| 3 | **Thin slice v1 : 3-7 supported intents** (Ch. 8) | 6 étapes séquentielles (annonce → identité → mutuelle → intention → dispos → clôture). Périmètre étroit. | Part 2 Discovery |
| 4 | **Unsupported intents définis explicitement** (Ch. 8) | Sections "L'agent ne doit pas" + "Out Of Scope V1" avec handling gracieux (reconnaître → ne pas traiter → rediriger cabinet). | Part 2 Discovery |
| 5 | **Hard boundaries + escalation immédiate** (Ch. 13) | Urgences vitales → interruption + phrase auditée 15/112. Hostilité / demande humain → serve. Identity fail × 2 → raccrochage poli. | Part 3 Design |
| 6 | **Guardrails par tour** (Ch. 13) | "Les guardrails doivent tourner à chaque tour de conversation, pas seulement au premier message." | Part 3 Design |
| 7 | **Primary + secondary + guardrail metrics** (Ch. 8) | Trois tiers explicites. Guardrail metrics = minimum absolu. Plus strict que le Playbook (qui ne formalise que primary + secondary). | Part 2 Discovery |
| 8 | **One flagship / portfolio strategy** (Ch. 8) | Un seul use case v1. Pas de dispersion. | Part 2 Discovery |
| 9 | **Handle or escalate, pas d'undefined behavior** (Ch. 13) | Tout hors-scope → acknowledge + redirect cabinet + log motif. | Part 3 Design |
| 10 | **Compliance by design** (Ch. 11 Design, Ch. 18 Build) | RGPD + HDS intégrés dès la conception, pas en afterthought. DPA, résidence UE, rétention minimale, registre sous-traitants. | Part 3 Design, Part 4 Build |
| 11 | **Error recovery / attempt ceiling** (Ch. 11) | 2 tentatives identité puis raccrochage poli. Playbook dit 3, choix de 2 est plus conservateur — cohérent pour un contexte santé. | Part 3 Design |
| 12 | **Confirmation récapitulative** (progressive confirmation, Ch. 11) | Étape 6 : récapituler ce qui est noté avant clôture. | Part 3 Design |
| 13 | **Outbound opening : identify + state purpose** (Ch. 11) | Étape 1 : cabinet + enregistrement + motif (catégorie + praticien). | Part 3 Design |
| 14 | **Baseline humaine à mesurer avant launch** (Ch. 8) | Listé comme critère Session 1 : "baseline humaine à mesurer définie." | Part 2 Discovery |
| 15 | **Ne pas écrire de code avant décision validée** (Ch. 8) | "Pas de code avant validation de decisions.md et v1-scope.md." | Part 2 Discovery |

---

## (b) Règles que CLAUDE.md contredit ou ignore

| # | Règle Vapi Playbook | Problème | Source |
|---|----------------------|----------|--------|
| 1 | **"Starting with a P2 is how pilots stall"** (Ch. 7) | CLAUDE.md assume P2 comme point de départ. Le Playbook dit explicitement : "A high-impact use case with low feasibility is a P2, not a starting point. It's a roadmap item." Le doc note "choix business assumé" mais sans justifier pourquoi aucun P1 plus simple n'existe (ex: confirmation RDV = Feasibility 5.0). | Part 2 Discovery — "Common scoring mistakes" |
| 2 | **Feasibility = (API Readiness + Complexity + Risk) / 3** (Ch. 7) | CLAUDE.md donne un Feasibility ~3.5 global sans décomposer les 3 sous-scores. Le Playbook exige un scoring par dimension avec rationale écrite. | Part 2 Discovery — "Calculating Feasibility and Impact" |
| 3 | **V1 success threshold numérique avant launch** (Ch. 8, 21) | CLAUDE.md définit la métrique principale mais aucun seuil numérique ("le pilote réussit si conversion atteint X%"). Le Playbook : "The threshold was written down before the pilot started. No one could argue later that 19% was 'close enough'." | Part 2 Discovery — "Defining success criteria by goal", Part 5 Test — "Defining the question" |
| 4 | **Comparison methodology choisie avant launch** (Ch. 8) | CLAUDE.md dit "baseline humaine à mesurer" mais ne spécifie pas A/B, before/after, ou matched cohorts. | Part 2 Discovery — "Setting baselines and comparison methodology" |
| 5 | **Coverage scope** (canal, langue, horaires, backup humain) (Ch. 8) | Absent. Le Playbook exige : "Phone channel only. English only. Business hours 8am to 6pm, with human backup available." Pas d'équivalent pour les horaires d'appel ni la disponibilité backup humain. | Part 2 Discovery — "Scoping the v1 thin slice" |
| 6 | **Voicemail strategy** (Ch. 11 Design) | Totalement absent. "A significant percentage of outbound calls reach voicemail. You need a strategy. Leave or retry? Decide in advance." | Part 3 Design — "Voicemail" |
| 7 | **Blended scenario : outbound → inbound callback** (Ch. 11) | CLAUDE.md exclut l'inbound, mais ne traite pas le cas où le patient rappelle le numéro sortant. Le Playbook avertit : "Drivers started calling back the number... The inbound agent had no idea why they were calling." | Part 3 Design — "Blended scenarios" |
| 8 | **Number reputation + warm-up + STIR/SHAKEN** (Ch. 17) | Absent. Le Playbook y consacre un chapitre entier. "Answer rates can drop from 45% to 10% in a week if numbers get flagged as spam." Critique pour 5000 appels/mois outbound. | Part 4 Build — "Number reputation", Ch. 17 "Telephony Setup" |
| 9 | **"Ask permission" dans les 10 premières secondes outbound** (Ch. 11) | L'étape 1 a identify + purpose + recording disclosure, mais pas de question de permission explicite ("Est-ce un bon moment ?"). Le Playbook : "Identify, state purpose, ask permission. Three elements, in that order. Skip any of them and you sound like a robocall." | Part 3 Design — "Outbound design" |
| 10 | **Monitoring trois couches** (Ch. 26) | Absent du cadrage. Le Playbook exige : system health, leading indicators, business outcomes. "Most teams only build the bottom one." | Part 7 Operate — "Three layers" |
| 11 | **Rollout stages avec gates** (Ch. 8, 22) | Pas de plan de déploiement progressif. Le Playbook exige : beachhead → adjacencies → program, avec critères explicites par stage. | Part 2 Discovery — "Planning the expansion path", Part 6 Launch — "One location at a time" |
| 12 | **Expansion path esquissé (mais pas construit)** (Ch. 8) | Le Playbook dit : "Plan the expansion path, but don't build it yet. Know where v2 goes so v1 architecture supports it." CLAUDE.md n'a pas d'expansion path, même esquissé. | Part 2 Discovery — "Planning the expansion path" |
| 13 | **Calling hours / réglementation démarchage** (Ch. 11, 17) | Le Playbook avertit sur TCPA et timezone. En France : Bloctel, Code de la consommation art. L223-1 et suivants, horaires autorisés (lundi-vendredi 10h-13h / 14h-20h depuis le décret 2022-1313). Non adressé. | Part 3 Design — "Compliance", Part 4 Build — "International considerations" |

---

## (c) Ajouts recommandés

### Priorité haute (bloquants ou risques structurels)

| # | Ajout | Rationale Vapi Playbook |
|---|-------|------------------------|
| 1 | **Justifier le P2-first** | Ajouter dans `decisions.md` pourquoi aucun P1 n'est disponible (pas de confirmation RDV à automatiser ? volume insuffisant ?), ou considérer un P1 comme marche d'escalier. "Starting with a P2 is how pilots stall." (Ch. 7) |
| 2 | **Seuil v1 numérique** | "Le pilote réussit si le taux de conversion devis → traitement atteint X% (baseline humaine actuelle : Y%). Échec si < Z%." À écrire avant le premier appel. (Ch. 8, 21) |
| 3 | **Calling hours + Bloctel** | Section compliance outbound France — horaires autorisés (décret 2022-1313), vérification Bloctel, consentement préalable ou exception "relation contractuelle préexistante", annonce d'enregistrement. (Ch. 11, 17) |
| 4 | **Voicemail strategy** | Décider maintenant : laisser un message (< 20s : cabinet + motif + rappel) ou retry silencieux ? Combien de retries ? À quel intervalle ? (Ch. 11) |
| 5 | **Callback scenario** | Que se passe-t-il quand le patient rappelle le numéro ? Options : message vocal fixe renvoyant au cabinet, ou mini-handler inbound "nous vous avons appelé au sujet de votre devis, le cabinet vous rappelle." (Ch. 11) |
| 6 | **Number reputation** | Warm-up protocol (50 appels/jour → ramp 2 semaines), CNAM/caller-ID au nom du cabinet, monitoring spam flags. À intégrer dans la checklist telephony du `v1-scope.md`. (Ch. 17) |

### Priorité moyenne (cadrage pilote)

| # | Ajout | Rationale Vapi Playbook |
|---|-------|------------------------|
| 7 | **Décomposer le scoring** | API Readiness = ?, Complexity = ?, Risk = ?, ROI/Impact = ?. Chaque score 1-5 avec rationale. Aujourd'hui le Feasibility ~3.5 n'est pas auditable. (Ch. 7) |
| 8 | **Comparison methodology** | Probablement before/after (A/B impraticable avec un seul cabinet pilote). Le documenter. (Ch. 8) |
| 9 | **Coverage scope** | Ajouter une section : canal (téléphone uniquement), langue (français uniquement), horaires (ex. lundi-vendredi 10h-13h / 14h-20h), backup humain disponible pendant les horaires d'appel. (Ch. 8) |
| 10 | **Pilot design** | Durée minimum (4-6 semaines), volume minimum pour significativité statistique, scorecard go/no-go à 4 composantes (primary metric, critical errors, qualitative, operational readiness). (Ch. 21) |
| 11 | **Rollout stages** | Beachhead (1 cabinet, heures ouvrées, volume limité) → Adjacencies (2-3 cabinets) → Program (scaling). Gate criteria explicites par stage. (Ch. 8, 22) |
| 12 | **Expansion path esquissé** | v2 = confirmation RDV (deepening) ? v3 = prise de RDV inbound (broadening) ? v4 = multilingue (extending) ? Juste une ligne par phase, pas de construction. (Ch. 8, 30) |

### Priorité basse (opérationnel, post-cadrage)

| # | Ajout | Rationale Vapi Playbook |
|---|-------|------------------------|
| 13 | **Monitoring trois couches** | Planifier dès maintenant les 3 layers (system health, leading indicators, business outcomes) même si implémenté plus tard. (Ch. 26) |
| 14 | **Permission question outbound** | Ajouter à l'étape 1 : "Est-ce un bon moment pour en parler ?" après le motif. Avec handling du "non" (proposition de rappel + collecte créneau). (Ch. 11) |
| 15 | **Operational readiness checklist** | Weekly review, daily automated checks, ownership assignments. "Unowned metrics don't get watched." (Ch. 25) |

---

## Verdict global

Le CLAUDE.md est **solide sur le cadrage produit** (goal unique, thin slice, guardrails, safety, compliance). Les lacunes principales sont sur :

1. **L'opérationnel outbound** — telephony (number reputation, voicemail, calling hours, callback scenario) : 4 lacunes sur 13.
2. **Le cadrage pilote** — seuil numérique, comparison methodology, rollout stages : 3 lacunes sur 13.
3. **Le point structurant** : la justification du P2-first ou l'identification d'un P1 stepping stone.

Les règles respectées (15/15) montrent une bonne maîtrise du framework Vapi sur le volet stratégie/scoping. Les manques (13 items) sont concentrés sur les volets Build, Launch, et Operate du Playbook — ce qui est cohérent avec le fait que CLAUDE.md est encore en Session 1 (cadrage).
