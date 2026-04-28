# Build Your OS — Working Doc v0.1

**Statut :** Base de travail opinionated pour aligner l'équipe. À challenger, itérer, puis verrouiller avant de coder.

---

## Thèse (en une phrase)

Dans chaque enterprise moderne, une génération d'*opérateurs augmentés* — en finance, RH, juridique, marketing — construit en silence ses propres outils, agents et workflows. Leur LinkedIn ne le montre pas. Nous, on construit le profil qui le montre.

## Why now

L'argument BlackRock : l'inertie enterprise (legal, compliance, procurement) rend l'adoption top-down de l'IA douloureusement lente. Notre flip : cette inertie est déjà en train d'être réglée bottom-up par les opérateurs individuels à l'intérieur des boîtes. À mesure que *"everyone can build"* devient réel sur les 24 prochains mois, l'écart entre ce que les gens font et ce que leur profil affiche va exploser. C'est cet écart qu'on ferme.

---

## Persona (la seule qu'on sert ce week-end)

**Maya, 28 ans, Senior Analyst dans un cabinet de conseil top 3.**
- A buildé 3 outils internes le week-end : un générateur de decks, un agent de research, un workflow de QA pour les livrables clients
- Fait gagner ~30 heures par semaine à son équipe
- Son LinkedIn dit *"Senior Associate."* C'est tout le signal disponible.
- Quand elle cherche un poste ou se pitche en interne, personne ne voit son vrai levier.

*Quentin est le prototype vivant : associate M&A avec un outil de scouting, un outil de valo, un workflow de DD, et 10 agents domaine sur des bases internes.*

## Wedge & monétisation

- **Wedge demo (B2C) :** flow consumer — Maya se connecte, son OS est révélé en moins de 90 secondes.
- **Pitch jury (B2B) :** le vrai cash, ce sont les recruteurs et enterprises qui paient pour faire émerger les builders cachés déjà à l'intérieur de leurs murs.

On entre par la démo émotionnelle B2C, on ferme avec la ligne de revenu B2B.

---

## Wow moment (le script de 5 secondes autour duquel on construit tout)

> Maya colle son LinkedIn + répond à 4 prompts rapides sur les outils qu'elle a buildés.
> Claude streame son raisonnement en live : *"Detected a reporting automation… inferring depth from frequency and criticality… mapping to Asset: Sourcing Engine."*
> Son dashboard se matérialise — 4 assets, chacun scoré, chacun avec une value statement en une ligne.
> Son titre passe de *"Senior Analyst"* à *"Senior Analyst + Operator running 4 internal tools, saving 30h/week."*

**Le wow c'est l'extraction, pas la 3D.** La trace de raisonnement visible, c'est ça le flex Claude.

---

## Architecture (3 agents, séquentiels)

1. **Agent d'ingestion** — pull LinkedIn (paste ou export PDF), GitHub via MCP, plus descriptions free-text des outils internes. Output : profil JSON structuré.
2. **Agent de scoring** — évalue chaque asset sur : temps gagné, fréquence, criticité, transférabilité, profondeur technique. Le raisonnement est streamé et visible. Output : Asset cards.
3. **UI generator** — render le dashboard. Tailwind + lucide-react + tiles CSS-isométriques.

## Stack

- Next.js (single page, App Router)
- Claude Sonnet via API, tool use activé pour MCP (GitHub minimum)
- Tailwind, lucide-react, shadcn/ui
- Grille CSS isométrique — **pas de Three.js**

---

## Out of scope (on sera tenté, on résiste)

- Intégration Pinterest
- Three.js ou tout vrai rendu 3D
- Esthétique Animal Crossing — on part *cozy fintech*, pas gaming
- Le mot *"tokenized"* nulle part dans le produit ou le pitch
- Auth / login — un user state fake suffit pour la démo
- Database — local state uniquement
- Mobile — démo desktop uniquement

---

## Definition of Done (pour la démo jury)

- 3 profils pré-loadés qui marchent end-to-end (Quentin M&A, un pote consulting, un pote juriste)
- Une création de profil live qui se complète en moins de 90 secondes
- Trace de raisonnement visible pendant la génération
- Dashboard qui rend proprement sur le laptop de démo, sans flicker
- Pitch (30s) + démo (60s) répétés au moins deux fois avant le passage

---

## Répartition des tâches (proposition — à ajuster)

- **Owner A :** Agent d'ingestion + wiring GitHub MCP + parser LinkedIn
- **Owner B :** Agent de scoring + UI streaming du raisonnement
- **Owner C :** UI dashboard + grille isométrique + asset cards
- **Owner D (Quentin) :** pitch, script de démo, 3 profils de référence, prep jury

## Timeline (non négociable)

- **H+0 → H+4 :** alignement, scaffolding, mock data qui circule à travers les 3 agents
- **H+4 :** **MID-MERGE.** Tout branché end-to-end, même moche. Bug list capturée. Non négociable.
- **H+4 → H+12 :** polish, vrais profils de démo, qualité du scoring, cleanup UI
- **H+12 → H+14 :** répéter pitch + démo. **Plus aucune feature après H+12.**

---

## Questions ouvertes à fermer dans les 30 prochaines minutes

1. Framing B2C ou B2B dans le pitch sur scène ? *(reco : wedge B2C, ligne monétisation B2B)*
2. Profils de démo — réels (nous) ou fictifs polishés ? *(reco : 2 réels + 1 fictif)*
3. Qui livre le pitch sur scène ?

---

*Si quoi que ce soit dans ce doc cloche, on le corrige maintenant — pas à H+8.*