# DentalOS — Cadrage Stack Démo

| Champ | Valeur |
|-------|--------|
| Date | 2026-05-02 |
| Statut | **ready for review** |
| Mission | Valider le pipeline voix end-to-end (STT → LLM → TTS) sur un appel simulé en français, dans une room LiveKit Cloud, avant tout déploiement SIP/téléphonie. |

Sections prévues :
1. **STT** ✅
2. **TTS** ✅
3. **LLM** ✅
4. **Turn Detection & VAD** ✅
5. **Hyperparameters & Audio Config** ✅
6. **Anti-patterns & Checklist démo** ✅

---

## 1. STT — Speech-to-Text

### Contraintes use case

| Contrainte | Détail |
|------------|--------|
| Langue | Français métropolitain exclusivement (v1) |
| Audio source | Téléphone (8kHz PCMU narrowband en prod, micro navigateur 16kHz+ en démo) |
| Durée appel | 2-4 min, 6 étapes courtes |
| Vocabulaire critique | Noms propres patients (Dupont, Nguyen, El-Mansouri…), dates de naissance (JJ/MM/AAAA), catégories dentaires (orthodontie, implant, couronne, parodontie, blanchiment), noms de praticiens |
| Latence cible | STT < 300ms (budget TTFT global < 800ms, voir v1-scope.md § S9) |
| Architecture HDS | Option B — le STT reçoit de l'audio brut **sans métadonnée patient** (pas de caller ID, pas de devis_id). Le patient peut dire son nom (étape 2). Cf. `decisions.md` |

### Comparatif providers

#### Deepgram Nova-3

| Critère | Évaluation |
|---------|------------|
| **WER français** | ~5-7% (audio propre). Amélioration de 14,26% relatif vs Nova-2 sur le français. Pas de WER isolé publié sur audio téléphonique FR. |
| **Modèle téléphonie** | ✅ `phonecall` dédié, optimisé 8kHz narrowband. G.711 n'ajoute que +0.6 WER absolu (mesuré en anglais). **Seul provider avec un modèle téléphonie dédié.** |
| **Latence streaming** | < 300ms P50. P99 ~1,9s. Dans le budget STT. |
| **Keyterm prompting** | ✅ Jusqu'à 200 termes. Préserve casse et ponctuation. Critique pour noms propres + vocabulaire dentaire. |
| **EU data residency** | ✅ GA. Endpoint : `api.eu.deepgram.com` (AWS EU). Pas de waitlist. Clés API existantes fonctionnent. |
| **DPA** | ✅ Disponible avec EU SCCs. SOC 2 Type II. HIPAA eligible. |
| **LiveKit intégration** | ✅ Plugin natif `livekit-plugins-deepgram` + **LiveKit Inference** (`inference.STT(model="deepgram/nova-3-general", language="fr")`). Pas besoin de clé API séparée via Inference. |
| **Prix** | $0.0077/min pay-as-you-go ($0.0065/min Growth). ~**$115-190/mois** pour 5000 appels × 3-5 min. |
| **Retours forum LiveKit** | Provider STT le plus utilisé dans la communauté LiveKit. Un report de dégradation sur mots courts en mode `multi` pour le portugais (romance language risk). **Recommandation : utiliser le mode monolingue `language="fr"`, pas `multi`.** |
| **Vapi Playbook** | Cité comme référence dans le budget latence (Ch. 15) : STT cible 200ms, providers varient de 150ms à 400ms. |

#### AssemblyAI Universal-3 Pro Streaming

| Critère | Évaluation |
|---------|------------|
| **WER français** | ~5-7% estimé (pas de WER FR isolé publié). 5,6% mean WER cross-langue sur 26 datasets real-world. Le streaming multilingue (dont FR) lancé en octobre 2025 — plus récent que Deepgram. |
| **Modèle téléphonie** | ❌ Pas de modèle `phonecall` dédié. Modèle universel. |
| **Latence streaming** | **307ms P50** (mesuré dans contexte LiveKit). P99 ~1,0s. Revendique 41% plus rapide que Deepgram en émission de mots (307ms vs 516ms). |
| **Keyterm prompting** | ✅ Jusqu'à 200 termes. |
| **EU data residency** | ✅ Endpoint : `api.eu.assemblyai.com` (AWS Dublin). Self-serve. |
| **DPA** | ✅ Public (assemblyai.com/legal/data-processing-addendum). ISO 27001. SOC 2 Type II. AES-256 + TLS 1.3. |
| **LiveKit intégration** | ✅ Plugin natif `livekit-plugins-assemblyai` + **LiveKit Inference** (`inference.STT(model="assemblyai/u3-rt-pro", language="fr")`). Neural turn detection intégré. |
| **Prix** | **$0.0025/min** base — le moins cher. ~**$37-63/mois** pour 5000 appels. Attention : add-ons (diarization, language detection) peuvent 3-4× le prix de base. |
| **Retours forum LiveKit** | Peu de retours spécifiques au français dans le corpus forum. Moins de signal communautaire que Deepgram. |
| **Vapi Playbook** | Non mentionné spécifiquement. |

#### Whisper large-v3-turbo (OpenAI)

| Critère | Évaluation |
|---------|------------|
| **WER français** | ~3-8% (audio propre, haute ressource). Bonne précision brute. |
| **Modèle téléphonie** | ❌ Aucune optimisation 8kHz. Performance dégradée sur audio téléphonique bruyant (5% studio → 15-20% mobile). |
| **Latence streaming** | ❌ **Non streaming**. API batch uniquement. Pseudo-streaming par chunks = 3-8s de latence. **Éliminatoire pour un voice agent temps réel.** Self-hosted faster-whisper : sub-100ms TTFT sur H100 (1300× real-time) mais nécessite GPU. |
| **Keyterm prompting** | ❌ Pas de keyword boosting. Paramètre `prompt` limité. |
| **EU data residency** | ✅ Depuis février 2025 (`eu.api.openai.com`). Zero data retention avec EU residency. Uniquement sur nouveaux projets. |
| **DPA** | ✅ Disponible avec EU SCCs. |
| **LiveKit intégration** | ❌ Pas de plugin streaming natif pour Whisper API. Le plugin OpenAI cible GPT-4o Realtime, pas Whisper STT. Self-hosted : adapter custom nécessaire. |
| **Prix** | $0.006/min (batch). Self-hosted : coût GPU uniquement (~136€/mois sur OVH L4). |
| **Verdict** | **Éliminé pour la démo et la prod** en tant qu'API. Seul intérêt : self-hosted dans le fallback option A (HDS bout en bout). |

#### Speechmatics

| Critère | Évaluation |
|---------|------------|
| **WER français** | ~4-8,3% (audio YouTube real-world). Revendique « jusqu'à 96% word accuracy ». **Différenciateur : multi-dialecte français** (métropolitain, québécois, belge, suisse, africain). |
| **Modèle téléphonie** | ⚠️ Pas de modèle dédié mais robuste au bruit revendiqué. Déploiement on-premise possible pour edge telephony. |
| **Latence streaming** | < 1s revendiqué. Pas de P50/P99 publié. Turn detection ML (mode `SMART_TURN`). |
| **Keyterm prompting** | ✅ Custom vocabulary. |
| **EU data residency** | ⚠️ Partiel. DPA avec SCCs. On-premise pour souveraineté totale. Cloud : vérifier le déploiement spécifique. |
| **DPA** | ✅ Disponible. SOC 2 Type II. |
| **LiveKit intégration** | ✅ Plugin natif `livekit-plugins-speechmatics`. STT + TTS. Turn detection avancé (ADAPTIVE/SMART_TURN/FIXED). |
| **Prix** | ~$0.004/min ($0.24/hr). ~**$60-100/mois**. Plus cher que AssemblyAI, moins que Deepgram. |
| **Retours forum LiveKit** | Aucun retour spécifique trouvé dans le corpus forum. |
| **Note** | Intéressant pour le multi-dialecte FR et l'option on-premise (HDS fallback A). À benchmarker. |

#### Azure Speech Services

| Critère | Évaluation |
|---------|------------|
| **WER français** | ~8%+. Pas de WER FR-spécifique publié par Microsoft. Custom speech models disponibles pour tuning domaine. |
| **Modèle téléphonie** | ✅ Forte héritage téléphonie (Nuance). Support codec téléphonique. Custom acoustic models sur audio 8kHz. |
| **Latence streaming** | ❌ **Problématique.** Forum LiveKit : 1,3s EOU seul (« non-configurable buffers »). Une équipe a abandonné Azure pour cette raison. Cold start documenté (keep-alive toutes les 5-10 min nécessaire). |
| **Keyterm prompting** | ✅ Phrase list + custom speech models (tuning domaine). |
| **EU data residency** | ✅ **Forte.** France Central, West Europe, Switzerland North. EU Data Boundary engagement Microsoft. |
| **DPA** | ✅ Microsoft OST/DPA. ISO 27001. SOC 1/2/3. Posture compliance la plus mature. |
| **LiveKit intégration** | ✅ Plugin natif `livekit-plugins-azure`. Plugin Python uniquement. |
| **Prix** | **$0.0167/min** — le plus cher. ~**$250-420/mois**. |
| **Verdict** | **Éliminé pour la démo.** Latence rédhibitoire (1,3s EOU > budget STT 300ms). Coût le plus élevé. Seul intérêt : compliance posture si l'écosystème Microsoft est déjà en place. |

#### Google Cloud Speech-to-Text v2 (Chirp 3)

| Critère | Évaluation |
|---------|------------|
| **WER français** | ~7-10%. Chirp : 4-7% sur audio propre anglais, 10-15% sur audio bruyant/accentué. Pas de WER FR-spécifique. |
| **Modèle téléphonie** | ⚠️ Adaptation `phone_call` disponible mais WER se dégrade à 10-15% sur audio bruyant. |
| **Latence streaming** | 300-600ms. Plus élevée que Deepgram/AssemblyAI. `ENDPOINTING_SENSITIVITY_SUPERSHORT` pour latence minimale. |
| **Keyterm prompting** | ✅ Phrase hints + class tokens (adresses, dates). Speech adaptation. |
| **EU data residency** | ✅ Régions EU multiples (Belgium, Netherlands). Service entièrement régionalisé en v2. |
| **DPA** | ✅ Google Cloud DPA. ISO 27001. SOC 1/2/3. |
| **LiveKit intégration** | ✅ Plugin natif `livekit-plugins-google`. Python uniquement. |
| **Prix** | **$0.016/min** — deuxième plus cher. ~**$240-400/mois**. |
| **Verdict** | **Éliminé.** Latence trop haute pour notre budget, prix élevé, WER FR non compétitif. |

#### Mention notable : Gladia (FR)

| Critère | Évaluation |
|---------|------------|
| **Origine** | Société française (Paris). |
| **FR support** | Conçu pour le français. Utilisé dans la recette officielle LiveKit « TTS Translator » pour le français. Code-switching FR/EN natif. |
| **LiveKit** | Plugin `livekit-plugins-gladia`. Pas via LiveKit Inference (clé API séparée requise). |
| **EU residency** | Très probable (siège FR). À confirmer formellement. |
| **Note** | Intéressant mais peu de données de benchmark comparatif. À inclure dans le bench test. |

---

### Tableau synthétique

| | Deepgram Nova-3 | AssemblyAI U3-Pro | Speechmatics | Gladia |
|---|---|---|---|---|
| **WER FR (est.)** | ~5-7% | ~5-7% | ~4-8% | Non publié |
| **Modèle 8kHz** | ✅ `phonecall` | ❌ | ⚠️ Robuste bruit | Non publié |
| **Latence P50** | < 300ms | 307ms | < 1s (revendiqué) | Non publié |
| **Keyterms** | ✅ 200 termes | ✅ 200 termes | ✅ Custom vocab | ❌ |
| **EU endpoint** | ✅ GA | ✅ Dublin | ⚠️ Partiel | ✅ Probable (FR) |
| **DPA** | ✅ | ✅ Public | ✅ | À vérifier |
| **LiveKit Inference** | ✅ | ✅ | ❌ Plugin only | ❌ Plugin only |
| **Coût 5000 appels/mois** | ~$115-190 | ~$37-63 | ~$60-100 | Non publié |
| **Signal communauté** | 🟢 Fort | 🟡 Modéré | 🟡 Faible | 🟡 Faible |

**Éliminés** : Whisper API (non streaming), Azure (latence 1,3s EOU), Google Chirp (latence + prix).

---

### Recommandation

**Choix principal : Deepgram Nova-3** (`language="fr"`, mode monolingue)

Justification chiffrée :

1. **Seul provider avec un modèle `phonecall` dédié** optimisé pour le narrowband 8kHz. En prod, nos appels passent par un trunk SIP PCMU/8kHz. La dégradation G.711 est mesurée à +0.6 WER absolu (le plus faible documenté). Les autres providers utilisent des modèles universels sans optimisation téléphonie.

2. **Keyterm prompting** (200 termes) : critique pour notre use case. Les noms propres français multi-origines (Dupont, Nguyen, El-Mansouri, Mbappé), les dates de naissance, et le vocabulaire dentaire (orthodontie, parodontie, couronne) sont des mots rares pour un STT généraliste. Le keyterm boosting réduit significativement les erreurs sur ces termes.

3. **Latence** : < 300ms P50, dans notre budget STT de 300ms (budget global TTFT < 800ms).

4. **LiveKit Inference** : intégration zero-config (`inference.STT(model="deepgram/nova-3-general", language="fr")`), pas de clé API séparée à gérer, billing unifié LiveKit.

5. **EU endpoint GA** : `api.eu.deepgram.com`, DPA avec SCCs, compatible architecture Option B.

6. **Signal communauté** : provider STT le plus utilisé dans l'écosystème LiveKit. Volume de retours et de résolutions de bugs le plus élevé dans le forum.

**Risque identifié** : le mode `multi` (multilingual) dégrade les mots courts en langues romanes (documenté pour le portugais, risque transposable au français). **Mitigation** : utiliser exclusivement le mode monolingue `language="fr"`. Notre v1 est français uniquement, le mode `multi` n'a pas d'utilité.

**Coût estimé** : ~$150/mois (5000 appels × 4 min avg × $0.0077/min). Acceptable pour le pilote.

**Benchmark à faire** : AssemblyAI Universal-3 Pro comme challenger (307ms P50, prix 3× moins cher, EU Dublin). Si le bench test sur audio téléphonique FR montre une précision comparable sur les noms propres, AssemblyAI pourrait être un fallback économique. Gladia (société française) à inclure dans le bench si la confirmation EU/DPA est obtenue.

**Configuration démo** :

```python
from livekit.agents import inference

stt = inference.STT(
    model="deepgram/nova-3-general",
    language="fr",
)

# En prod, ajouter keyterms pour le vocabulaire dentaire + noms praticiens :
# stt = deepgram.STT(
#     model="nova-3",
#     language="fr",
#     keyterms=["orthodontie", "parodontie", "couronne", "implant", "blanchiment",
#               "Dr Martin", "Dr Nguyen", ...],
# )
```

[À VALIDER SESSION 1] : bench test Deepgram vs AssemblyAI vs Gladia sur 50 utterances FR téléphoniques (noms propres + dates + vocabulaire dentaire) avant go-live.

---

## 2. TTS — Text-to-Speech + Voice

### Contraintes use case

| Contrainte | Détail |
|------------|--------|
| Langue | Français métropolitain, registre « vous » |
| Ton | Consultatif, neutre, professionnel. Ni « vendeuse » ni « robotique ». Cf. CLAUDE.md : « L'agent informe, capture, redirige. Il ne vend pas. » |
| Genre voix | Féminine (choix par défaut secteur santé FR — à valider avec cabinet pilote) |
| Dates et chiffres | Prononciation correcte en français (« le quinze avril deux mille vingt-six », pas « fifteen april ») |
| TTFB cible | < 200ms (budget TTFT global < 800ms, STT ~300ms + LLM ~300ms laisse ~200ms pour TTS) |
| Architecture HDS | Option B — le TTS reçoit le texte de réponse de l'agent. Ce texte ne contient JAMAIS d'identité patient ni de catégorie de traitement (zero-content par design). Risque HDS faible pour ce composant. |
| Annonce étape 1 | Audio pré-synthétisé (template fixe avec catégorie + praticien). **Pas généré par le LLM en temps réel.** Le TTS live ne prononce jamais la catégorie. |

### Cadre Vapi Playbook — Persona Voice (Ch. 11)

Le Vapi Playbook définit 4 dimensions de persona et 3 niveaux d'intensité. Application au use case DentalOS :

**4 dimensions :**

| Dimension | Spectre | Position DentalOS | Justification |
|-----------|---------|-------------------|---------------|
| **Warmth** | Amical ↔ Neutre | Modéré-chaud | Empathique mais pas familier. Registre « vous ». Le patient doit se sentir respecté, pas démarché. |
| **Formality** | Casual ↔ Professionnel | Professionnel | Contexte cabinet dentaire, suivi de devis = document formel. |
| **Pace** | Détendu ↔ Efficace | Modéré-détendu | Le patient peut être âgé, distrait, ou surpris par l'appel. Le Playbook cite un cas santé : « patients said 'yes' because they didn't want to slow down the call, not because they understood → 15% higher no-show rates. » |
| **Assertiveness** | Suggestif ↔ Directif | Bas | Capture d'intention, pas de vente. « Non » et « je réfléchis » = fin de conversation (règle anti-pression). |

**Niveau d'intensité : MOYEN** — interaction de service où la confiance compte. Le patient doit avoir confiance que ses réponses sont correctement comprises. Warmth + confirmation progressive.

**Profil cible de voix :** féminine, calme, posée, chaleureuse sans excès, professionnelle, rythme naturel (pas accéléré), bonne articulation des dates et noms propres.

### Comparatif providers

#### Cartesia Sonic-3

| Critère | Évaluation |
|---------|------------|
| **Voix françaises disponibles** | 7 voix FR dédiées (4 féminines, 3 masculines). |
| **Voix recommandée** | **« Calm French Woman »** — `a8a1eb38-5f15-4c1d-8722-7ac0f329727d`. Description : « Soft and calm, suited for soothing conversations. » Match direct avec le profil persona (chaleur modérée, assertivité basse, pace posé). |
| **Alternative** | « Helpful French Lady » — `65b25c5d-ff07-4687-a04c-da2f43ef6fa9`. Plus dynamique, ton « customer support ». |
| **Naturalité** | 4,7/5 en évaluation indépendante. Préféré à ElevenLabs Flash v2 par 61,4% des auditeurs en test aveugle (toutes langues confondues). |
| **TTFB** | ✅ **~40-90ms** (inference seule) — **le plus rapide de tous les providers**. Sonic Turbo : ~40ms, Sonic Standard : ~90ms. |
| **Pénalité non-anglais** | ⚠️ Benchmark espagnol : +300-500ms au TTFT total vs anglais. **Pas de mesure FR publiée.** Risque : TTFB réel FR pourrait être ~200-400ms. À tester. |
| **Contrôle** | Paramètres `emotion` (beta), `speed`, `volume`. Prononciation custom via notation IPA (`<<l\|aj\|v\|cʰ\|ɪ\|t\|>>`). |
| **EU data residency** | ⚠️ GDPR compliant + SOC 2 Type II + HIPAA. **Mais : aucun endpoint EU documenté.** Le DPA existe mais les lieux de traitement ne sont pas publiés. **Risque à clarifier avec Cartesia.** |
| **LiveKit intégration** | ✅ Plugin `livekit-plugins-cartesia` (Python + Node.js) + **LiveKit Inference** (`inference.TTS("cartesia/sonic-3", voice="...", language="fr")`). ⚠️ Voices custom/clonées : plugin uniquement (pas via Inference). |
| **Prix** | ~$0.06/min agent. Plan Scale ($239/mois) = 8M crédits. Estimé **~$300-450/mois** à 5000 appels. |
| **Dates/chiffres FR** | Revendique « best-in-class pronunciations » pour le FR. Pas de benchmark indépendant. IPA disponible comme fallback. |
| **Forum LiveKit** | « Cartesia with cloned voice — Good quality TTS. » « For best results, many developers use Cartesia TTS with Deepgram STT for phone call use cases. » |

**Voix FR féminines identifiées :**

| Nom | Voice ID | Description | Match persona |
|-----|----------|-------------|---------------|
| Calm French Woman | `a8a1eb38-5f15-4c1d-8722-7ac0f329727d` | Douce et calme, conversations apaisantes | ✅ **Best match** |
| Helpful French Lady | `65b25c5d-ff07-4687-a04c-da2f43ef6fa9` | Serviable et enjouée, ton conversationnel | ⚠️ Trop dynamique ? |
| French Narrator Lady | `8832a0b5-47b2-4751-bb22-6a8e2149303d` | Veloutée et neutre, style narration | ⚠️ Trop « lecture » |
| French Conversational Lady | `a249eaff-1e96-4d2c-b23b-12efa4f66f41` | Registre conversationnel | ✅ Challenger |

#### ElevenLabs Flash v2.5 / Multilingual v2

| Critère | Évaluation |
|---------|------------|
| **Voix françaises disponibles** | **70+ voix féminines FR** dans la voice library. Catalogue le plus large de tous les providers. |
| **Voix recommandée** | **« Lise - Mediation Coach »** — `sEk5ftjVl91hHjtOlmK1`. Description : « Clear, smooth and soothing French female voice. » Contexte médiation/care = aligné secteur santé consultatif. |
| **Alternatives secteur santé** | Voir tableau ci-dessous. |
| **Naturalité** | Flash v2.5 : « strongest prosody control and expressive clarity » (plus haut Elo score). Multilingual v2 : « most lifelike and emotionally rich ». Langues européennes (FR, ES, DE) notées « close behind English ». ⚠️ Un reviewer 2025 qualifie les langues non-anglaises de « problematic » sur MLv2. |
| **TTFB** | Flash v2.5 : **~75ms** (inference). End-to-end avec WebSocket streaming EU : ~150-200ms. MLv2 : ~250-300ms. |
| **Pénalité non-anglais** | « Processing time can vary depending on the language used. » Pas de chiffre FR précis. |
| **Contrôle** | Pronunciation dictionaries disponibles (custom dictionnaire pour termes dentaires). Pas de paramètre `emotion` natif — le contrôle passe par le choix de voix. |
| **EU data residency** | ⚠️ Endpoint EU : `api.eu.residency.elevenlabs.io` — **Enterprise uniquement**. Plans standard = traitement US. Zero Retention Mode combiné à EU endpoint pour restreindre le traitement. **Risque : EU residency paywall Enterprise.** |
| **DPA** | ✅ Public (elevenlabs.io/dpa). SOC 2. HIPAA Enterprise. |
| **LiveKit intégration** | ✅ Plugin `livekit-plugins-elevenlabs` (Python + Node.js). ⚠️ **Pas via LiveKit Inference** pour custom/community voices. Clé API séparée requise. |
| **Prix** | Flash : $0.06/1K caractères. MLv2 : $0.12/1K caractères. Estimé **~$450/mois** (Flash) à 5000 appels. Plus cher que Cartesia. |
| **Dates/chiffres FR** | Pronunciation dictionaries permettent de forcer la prononciation. Utile pour normaliser les dates et termes dentaires. |
| **Forum LiveKit** | ⚠️ « Multilanguage with ElevenLabs not working » (mars 2026). « ElevenLabs other voice ID broken » (fév 2026). Intégration multilingue fragile sur certaines versions. |

**Voix FR féminines shortlistées (profil santé consultatif) :**

| Nom | Voice ID | Description | Match persona |
|-----|----------|-------------|---------------|
| Lise - Mediation Coach | `sEk5ftjVl91hHjtOlmK1` | Claire, douce, apaisante. Médiation/care. | ✅ **Best match** |
| Cecile - Virtual Assistant | `DOqLhiOMs8JmafdomNTP` | Apaisante et abordable. | ✅ Forte |
| Amelie - Warm and Gentle | `39BbQfJTexvpWtOQZ4Xr` | Chaude, calme, douce. | ✅ Forte |
| Helene - Neutral | `imRmmzTqlLHt9Do1HufF` | « Voix de femme française, apaisante et agréable. » | ✅ Forte |
| Isabelle - Mature Narrator | `8h85Kr2hDfqe0CKeh7Bq` | Mature, chaleureuse, profonde. Confiance. | ✅ Si population patiente plus âgée |
| Emilie - Customer Service | `fBpCO0Kf0krKLYGOu65w` | Chaleureuse, naturelle, rassurante. | ⚠️ Trop « service client » ? |
| Delphine - Clear and Professional | `7VoxpuBC4ZIcnW14yi9m` | Professionnelle et chaleureuse. | ✅ Tone match |
| Lea - Calm and Pedagogical | `ICk609TItINMseDpChFt` | Calme, pédagogique. | ✅ Bonne articulation |

#### Azure Neural TTS

| Critère | Évaluation |
|---------|------------|
| **Voix FR** | 17 voix fr-FR (9F, 8M). **DeniseNeural** : modulation de style (cheerful, excited, sad, whispering). **VivienneMultilingualNeural** : dernière génération. |
| **Voix recommandée** | `fr-FR-DeniseNeural` (style neutre/calm par défaut). |
| **Naturalité** | Bonne avec contrôle de style. HD V2 (février 2025) = dernière génération. |
| **TTFB** | ❌ **Problématique.** Forum LiveKit : 1,3s EOU seul avec « non-configurable buffers ». Une équipe a abandonné Azure au profit de Cartesia pour cette raison. General range : 200-400ms mais reports contradictoires. Cold start documenté. |
| **SSML** | ✅ **Support complet**. Contrôle précis des dates (« \<say-as interpret-as="date"\> »), nombres, emphasis, breaks. **Avantage unique** pour la prononciation FR des dates de naissance et chiffres. |
| **EU data residency** | ✅ **La plus forte.** France Central. EU Data Boundary engagement Microsoft. **HDS certifié** — seul provider TTS avec certification HDS. |
| **LiveKit intégration** | ✅ Plugin `livekit-plugins-azure`. Python uniquement. |
| **Prix** | ✅ **Le moins cher.** Neural standard : ~$16/1M chars. HD V2 : ~$30/1M chars. Estimé **~$120-225/mois** à 5000 appels. |
| **Verdict** | Excellent profil compliance (HDS !) et prix. **Éliminé pour la démo** (latence rédhibitoire pour un voice agent temps réel). Pertinent si le fallback A (full HDS) est activé. |

#### Google Chirp 3 HD

| Critère | Évaluation |
|---------|------------|
| **Voix FR** | 8 voix fr-FR (4F, 4M). Noms abstraits : Aoede, Kore, Leda, Zephyr (F). |
| **Naturalité** | « Major leap » vs WaveNet. Disfluences humaines (um, uh). 30 styles par voix. |
| **TTFB** | Streaming disponible. Pas de TTFB publié. Anciennes voix Neural2/WaveNet : ~200-300ms. |
| **EU data residency** | ✅ Endpoints régionaux EU. Service entièrement régionalisé en v2. |
| **Prix** | $30/1M chars (Chirp 3 HD). ~$225/mois. Free tier : 1M chars/mois. |
| **Verdict** | Profil intéressant mais trop peu de données FR-spécifiques. Pas de signal communauté dans l'écosystème LiveKit. **Non retenu pour la démo.** À benchmarker si Cartesia/ElevenLabs déçoivent. |

#### Rime Arcana V3

| Critère | Évaluation |
|---------|------------|
| **Voix FR** | FR supporté via Arcana V3 (10 langues). ~35 voix multilingues (noms abstraits : estelle, vespera…). Pas de voix FR-spécifiques. |
| **TTFB** | Mist v2 : sub-100ms on-prem, sub-200ms cloud. Arcana : plus lent (expressif). |
| **EU data residency** | ❌ **Non documenté.** Société US. Pas d'endpoint EU. Pas de DPA public. |
| **Verdict** | **Éliminé.** Pas de voix FR dédiées, pas de compliance EU documentée. |

### Tableau synthétique

| | Cartesia Sonic-3 | ElevenLabs Flash v2.5 | Azure DeniseNeural | Google Chirp 3 HD |
|---|---|---|---|---|
| **Voix FR féminines** | 4 dédiées | 70+ | 9 | 4 |
| **Best voice ID** | `a8a1eb38…` (Calm) | `sEk5ft…` (Lise) | `fr-FR-DeniseNeural` | `fr-FR-Chirp3-HD-Kore` |
| **TTFB (inference)** | ✅ **40-90ms** | ✅ ~75ms | ❌ 200-1300ms | ⚠️ ~200-300ms |
| **Pénalité FR** | ⚠️ +300-500ms (est.) | ⚠️ Variable | Inconnue | Inconnue |
| **Naturalité FR** | 4,7/5 (général) | « Close to EN » | Bonne + style control | « Major leap » vs WaveNet |
| **SSML dates/chiffres** | ❌ (IPA custom) | ❌ (pronunciation dict) | ✅ Complet | ✅ Complet |
| **EU endpoint** | ⚠️ Non documenté | ⚠️ Enterprise only | ✅ France Central, HDS | ✅ EU régions |
| **LiveKit Inference** | ✅ | ❌ (plugin only) | ❌ (plugin only) | ❌ (plugin only) |
| **Coût/mois (5000 appels)** | ~$300-450 | ~$450 | ✅ ~$120-225 | ~$225 |
| **Signal communauté LK** | 🟢 Fort | 🟡 Modéré + bugs FR | 🔴 Abandonné (latence) | 🟡 Faible |

**Éliminés** : Azure (latence), Rime (pas de FR dédié / pas d'EU), Speechmatics TTS (pas de FR disponible).

### Recommandation

**Choix principal démo : Cartesia Sonic-3** — voix « Calm French Woman »

| Paramètre | Valeur |
|-----------|--------|
| Provider | Cartesia |
| Modèle | `sonic-3` |
| Voice ID | `a8a1eb38-5f15-4c1d-8722-7ac0f329727d` (Calm French Woman) |
| Langue | `fr` |
| Speed | `1.0` (ajuster après tests — potentiellement `0.95` pour un rythme plus posé) |

Justification :

1. **TTFB le plus bas** (~40-90ms inference). Avec la pénalité non-anglais estimée (+300-500ms), on resterait potentiellement dans le budget ~200-400ms. À mesurer en condition réelle FR.

2. **« Calm French Woman » aligne les 4 dimensions Vapi** : warmth modérée-chaude (« soft and calm »), formality professionnelle (pas de slang), pace posé (« soothing conversations »), assertivité basse (pas de ton directif). C'est le match le plus direct avec le profil persona DentalOS.

3. **LiveKit Inference** : `inference.TTS("cartesia/sonic-3", voice="a8a1eb38-5f15-4c1d-8722-7ac0f329727d", language="fr")`. Zéro clé API séparée, billing unifié LiveKit. Plus simple pour la démo.

4. **Cohérence stack** : Deepgram STT + Cartesia TTS est la combinaison la plus utilisée dans la communauté LiveKit pour les voice agents téléphoniques (confirmé forum).

5. **Contrôle fin** : `emotion` (beta), `speed`, `volume` + prononciation IPA pour les termes qui posent problème.

**Risques identifiés** :

- **Pénalité latence FR** : le benchmark espagnol montre +300-500ms. Si le FR est similaire, le TTFB réel pourrait être ~400-500ms → dépasse le budget de 200ms. **Test empirique obligatoire.**
- **EU data residency non confirmée** : GDPR compliant ≠ EU data residency. Pour la prod (Option B), il faut une confirmation écrite de Cartesia que les données audio sont traitées en UE. **Pour la démo** (pas de données patient réelles), c'est acceptable.
- **Prononciation dates/chiffres** : pas de SSML natif. Si les dates de naissance sont mal prononcées → fallback IPA ou template pré-synthétisé pour les phrases contenant des dates.

**Challenger production : ElevenLabs Flash v2.5** — voix « Lise - Mediation Coach »

| Paramètre | Valeur |
|-----------|--------|
| Provider | ElevenLabs |
| Modèle | `eleven_flash_v2_5` |
| Voice ID | `sEk5ftjVl91hHjtOlmK1` (Lise - Mediation Coach) |

Pourquoi challenger :
- 70+ voix FR → plus de choix pour A/B testing perceptif
- Pronunciation dictionaries pour les termes dentaires (Cartesia n'a que l'IPA)
- « Lise - Mediation Coach » est explicitement décrite pour un contexte médiation/care
- Si l'EU Enterprise endpoint est accessible → meilleure posture compliance

Pourquoi pas principal :
- Pas via LiveKit Inference (clé API séparée)
- EU endpoint = Enterprise tier (coût + négociation)
- Bugs d'intégration multilingue documentés sur le forum (mars 2026)
- ~$450/mois vs ~$300-450/mois Cartesia

**Fallback HDS (Option A) : Azure `fr-FR-DeniseNeural`**

Si le fallback full-HDS s'active (validation juridique Option B échoue), Azure est le seul TTS avec certification HDS. La latence est problématique pour un voice agent mais c'est le seul choix conforme. SSML complet = prononciation dates parfaite.

**Configuration démo :**

```python
from livekit.agents import inference

tts = inference.TTS(
    "cartesia/sonic-3",
    voice="a8a1eb38-5f15-4c1d-8722-7ac0f329727d",  # Calm French Woman
    language="fr",
)

# En prod, si Cartesia ne confirme pas EU residency, switch vers ElevenLabs :
# from livekit.plugins import elevenlabs
# tts = elevenlabs.TTS(
#     model="eleven_flash_v2_5",
#     voice_id="sEk5ftjVl91hHjtOlmK1",  # Lise - Mediation Coach
# )
```

[À VALIDER SESSION 1] :
- Bench test TTFB réel FR : Cartesia Calm French Woman vs ElevenLabs Lise sur 20 phrases type flow DentalOS (annonce, questions, récap)
- Test prononciation : dates de naissance (« le 15 avril 1987 »), noms propres multi-origines, termes dentaires
- Confirmation EU data residency avec Cartesia (email commercial ou DPA)
- Si le cabinet pilote préfère une voix masculine → tester « Friendly French Man » (Cartesia `ab7c61f5-3daa-47dd-a23b-4ac0aac5f5c3`) ou « Henri » (Azure `fr-FR-HenriNeural`)

---

## 3. LLM — Large Language Model

### Contraintes use case

| Contrainte | Détail |
|------------|--------|
| Rôle | Orchestrateur du flow 6 étapes : générer les répliques, interpréter les réponses patient, appeler les function tools, maintenir le state |
| Langue | Français métropolitain exclusivement (v1). Qualité du français généré = critère primaire (naturalité, vouvoiement, concision) |
| Script | Flow rigide en 6 étapes séquentielles — instruction-following strict > créativité. Température 0.0. |
| Function tools | `verify_patient_identity(name, surname, dob, devis_id)` → `{match: bool}`. Outil simple, un seul appel par conversation. Potentiellement `log_call_outcome(...)` en fin d'appel. |
| Latence cible | TTFT < 400ms (budget global TTFT < 800ms : STT ~300ms, **LLM ~300ms**, TTS ~200ms). Le Vapi Playbook alloue 400ms au LLM dans un budget total de 1000ms. |
| Réponses | Courtes (1-3 phrases). Pas de paragraphes. Le LLM génère du texte parlé, pas du texte écrit. |
| Guardrails | Chaque tour : vérifier que la réponse ne contient pas de conseil médical, estimation mutuelle, pression commerciale, contenu du devis. Cf. CLAUDE.md § Safety Rules. |
| Architecture HDS | Option B — le LLM reçoit le system prompt + transcription patient (anonymisée). **Pas de catégorie de traitement** dans le ChatContext (pré-synthétisée en audio). **Pas de données patient identifiantes** sauf ce que le patient dit lui-même (nom, DOB — transmis au tool, pas gardés en context). |

### Comparatif providers

#### GPT-4.1-mini (OpenAI)

| Critère | Évaluation |
|---------|------------|
| **Instruction following** | IFEval 84,1% (strict). Amélioration significative vs GPT-4o-mini (76,5%). Conçu explicitement pour les « agentic workflows with long system prompts and many tools ». |
| **Qualité français** | Bonne mais pas la meilleure. GPT-4.1 full : #2 sur WMT24 FR (derrière Claude). Mini : pas de score FR isolé, mais la famille 4.1 est forte en multilingue. |
| **TTFT** | ⚠️ **0,55-0,94s** selon les benchmarks. Médiane ~0,7s. **Dépasse le budget de 400ms.** Temps de « pensée » avant le premier token plus long que GPT-4o-mini. |
| **Function calling** | ✅ Score 0,76-0,85 (Berkeley FC benchmark). Entraîné spécifiquement pour les tool calls agentic. Parallel + sequential tool calls supportés. |
| **EU endpoint** | ✅ `eu.api.openai.com` (depuis février 2025). Zero data retention avec EU residency. Projets nouveaux uniquement. |
| **DPA** | ✅ Disponible avec EU SCCs. SOC 2 Type II. |
| **LiveKit Inference** | ✅ `inference.LLM(model="openai/gpt-4.1-mini")`. Pas de clé API séparée. Co-location infrastructure. |
| **Prix** | $0,40/M input, $1,60/M output. Estimé **~$15-30/mois** pour 5000 appels (conversations courtes ~500 tokens in / 300 tokens out). |
| **Retours LiveKit** | Un cas production allemand (agent téléphonique, flux structuré similaire au nôtre) utilise GPT-4.1-mini avec succès. « GPT-4.1-mini — this model works best for voice AI scenarios in my tests ». |
| **Vapi Playbook** | « 400ms budget for LLM. Tool calls budget separately. » Le TTFT de 4.1-mini est au-dessus de ce budget. |

#### GPT-4o-mini (OpenAI)

| Critère | Évaluation |
|---------|------------|
| **Instruction following** | IFEval 76,5% (strict). Inférieur à 4.1-mini (-7,6 points). |
| **Qualité français** | Comparable à 4.1-mini, pas de différence majeure documentée. |
| **TTFT** | ✅ **0,2-0,4s**. Nettement plus rapide que 4.1-mini. **Dans le budget 400ms.** |
| **Function calling** | ✅ Bon mais inférieur à 4.1-mini (pas de benchmark comparatif direct publié). |
| **EU endpoint** | ✅ Même infrastructure EU que 4.1-mini. |
| **LiveKit Inference** | ✅ `inference.LLM(model="openai/gpt-4o-mini")`. |
| **Prix** | ✅ **$0,15/M input, $0,60/M output** — le moins cher. ~$8-15/mois. |
| **Note** | ⚠️ **Modèle en fin de vie** — OpenAI pousse vers 4.1-mini comme successeur. Risque de dépréciation à moyen terme. |

#### Claude Haiku 4.5 (Anthropic)

| Critère | Évaluation |
|---------|------------|
| **Instruction following** | Excellent. Claude excelle sur les scripts structurés avec guardrails multiples — alignement naturel avec notre flow 6 étapes + safety rules. |
| **Qualité français** | ✅ **La meilleure de la catégorie « petit modèle ».** WMT24 FR : Claude (famille) = #1 ou #2 toutes catégories. Vouvoiement naturel, registre consultatif, concision. |
| **TTFT** | ⚠️ **0,60-0,80s**. **Dépasse le budget de 400ms.** Comparable à 4.1-mini. |
| **Function calling** | ✅ Tool use natif, bien documenté. Pas de benchmark FC comparable publié mais retours positifs. |
| **EU endpoint** | ❌ **Pas d'endpoint EU natif Anthropic.** Via AWS Bedrock eu-west-1 (Irlande) : possible, mais ajoute une couche. Via Google Vertex AI EU : aussi possible. |
| **DPA** | ✅ Anthropic Usage Policy + DPA. Bedrock : DPA AWS. |
| **LiveKit Inference** | ❌ **Pas disponible.** Claude n'est pas dans LiveKit Inference. Nécessite `livekit-plugins-anthropic` avec clé API séparée, ou passage via Bedrock/Vertex. |
| **Prix** | $1/M input, $5/M output. ~$20-40/mois. Plus cher que les GPT-mini mais reste abordable. |
| **Retours LiveKit** | Un cas production portugais (agent médical) utilise Claude Sonnet 4.6 avec un TTFT P50 de 1024ms — trop lent. Haiku serait plus rapide mais aucun retour FR spécifique trouvé. |
| **Note** | Meilleure qualité FR + meilleur alignement safety, mais handicapé par l'absence d'Inference et d'EU natif. |

#### Gemini 2.5 Flash (Google)

| Critère | Évaluation |
|---------|------------|
| **Instruction following** | Bon (pas de score IFEval isolé publié pour Flash). Famille Gemini forte sur les benchmarks multilingues. |
| **Qualité français** | Bonne mais inférieure à Claude et GPT-4.1 sur le registre formel/consultatif (pas de benchmark FR comparatif). |
| **TTFT** | ⚠️ **0,73s** (mesuré). Avec function tools : **+2-2,5s supplémentaires** (forum LiveKit). **Éliminatoire avec tools.** |
| **Function calling** | ❌ **Problématique en pratique.** Forum LiveKit : « Gemini 2.5 Flash with tools adds 2-2.5 seconds to TTFT ». Latence tool call incompatible avec un voice agent temps réel. |
| **EU endpoint** | ⚠️ Via Vertex AI uniquement (pas de Vertex dans LiveKit Inference). Régions EU disponibles. |
| **LiveKit Inference** | ✅ `inference.LLM(model="google/gemini-2.5-flash")`. Mais : tool call latency même via Inference. |
| **Prix** | $0,30/M input, $2,50/M output (thinking tokens en plus). ~$15-25/mois hors thinking. |
| **Retours LiveKit** | ⚠️ « Gemini compatibility issues » signalés. « Tool calls add significant latency. » Intégration moins mature que OpenAI. |
| **Verdict** | **Éliminé.** La latence des tool calls (+2-2,5s) est rédhibitoire pour `verify_patient_identity`. |

#### Llama 3.3 70B (Meta, via Groq/Together/Fireworks)

| Critère | Évaluation |
|---------|------------|
| **Instruction following** | ✅ **IFEval 92,1%** — le plus élevé de tous les modèles comparés. Excellent sur les scripts structurés. |
| **Qualité français** | ⚠️ Inférieure aux modèles propriétaires pour le français. Llama est entraîné principalement sur l'anglais. Le vouvoiement et le registre consultatif FR sont moins naturels. |
| **TTFT** | ✅ **~0,30s sur Groq** (inférence spécialisée LPU). Très rapide. Sur Together/Fireworks : ~0,5-0,8s. |
| **Function calling** | ⚠️ Supporté mais moins robuste que GPT-4.1-mini. Pas de benchmark FC comparable. Llama 3.3 n'a pas été entraîné spécifiquement pour le tool calling agentic. |
| **EU endpoint** | ❌ **Incertain.** Groq : pas d'endpoint EU documenté. Together : pas d'EU. Fireworks : pas d'EU. Self-hosted sur OVH HDS : possible mais nécessite GPU (L4/A100). |
| **LiveKit Inference** | ❌ Pas disponible. Nécessite un plugin custom ou `livekit-plugins-openai` avec base_url pointant vers Groq/Together. |
| **Prix** | ✅ Groq : $0,10/M input, $0,10/M output. Le moins cher si on exclut le self-hosting. ~$3-8/mois. |
| **Verdict** | IFEval impressionnant mais qualité FR insuffisante pour un agent patient-facing. Pas d'EU, pas d'Inference. **Éliminé pour la démo et la prod.** Intéressant en self-hosted HDS comme fallback extrême. |

#### Mistral Large 3 (Mistral AI)

| Critère | Évaluation |
|---------|------------|
| **Instruction following** | Bon. Mistral Large 3 conçu pour les « complex multi-step instructions ». Pas de score IFEval publié comparable. |
| **Qualité français** | ✅ **La meilleure.** Mistral = société française, modèle nativement bilingue FR/EN. Le registre formel/consultatif FR est le plus naturel de tous les modèles testés. |
| **TTFT** | ❌ **~1,10s**. Le plus lent. **Hors budget.** |
| **Function calling** | ✅ Bon. Native function calling, compatible OpenAI-style. |
| **EU endpoint** | ✅ **EU natif** (hébergé en France). `api.mistral.ai` = infra européenne. Le seul LLM nativement hébergé en UE. |
| **DPA** | ✅ DPA Mistral. RGPD natif. Pas de transfert hors UE par défaut. |
| **LiveKit Inference** | ❌ Pas disponible. Nécessite `livekit-plugins-openai` avec `base_url="https://api.mistral.ai/v1"`. |
| **Prix** | $0,50/M input, $1,50/M output. ~$15-25/mois. Raisonnable. |
| **Verdict** | **Meilleur français + meilleure posture EU.** Mais TTFT de 1,1s est éliminatoire pour un voice agent temps réel. **Candidat production si la latence baisse**, ou si on accepte un budget TTFT plus large (pipeline optimisé STT rapide + TTS rapide = marge pour un LLM plus lent). |

### Tableau synthétique

| | GPT-4.1-mini | GPT-4o-mini | Claude Haiku 4.5 | Gemini 2.5 Flash | Llama 3.3 70B | Mistral Large 3 |
|---|---|---|---|---|---|---|
| **IFEval** | 84,1% | 76,5% | N/A (excellent) | N/A (bon) | **92,1%** | N/A (bon) |
| **Qualité FR** | 🟡 Bonne | 🟡 Bonne | 🟢 **Très bonne** | 🟡 Bonne | 🔴 Faible | 🟢 **Meilleure** |
| **TTFT** | ⚠️ 0,55-0,94s | ✅ **0,2-0,4s** | ⚠️ 0,60-0,80s | ❌ 0,73s + tools | ✅ 0,30s (Groq) | ❌ ~1,10s |
| **Function tools** | ✅ 0,76-0,85 | ✅ Bon | ✅ Bon | ❌ +2-2,5s | ⚠️ Basique | ✅ Bon |
| **EU endpoint** | ✅ | ✅ | ❌ Indirect | ⚠️ Vertex only | ❌ Incertain | ✅ **Natif FR** |
| **LiveKit Inference** | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ |
| **Coût/mois** | ~$15-30 | ✅ ~$8-15 | ~$20-40 | ~$15-25 | ✅ ~$3-8 | ~$15-25 |
| **Signal communauté LK** | 🟢 Fort | 🟡 Modéré | 🟡 Faible | 🔴 Bugs tools | 🔴 Aucun | 🟡 Faible |

**Éliminés** : Gemini 2.5 Flash (tool call latency +2-2,5s), Llama 3.3 70B (qualité FR insuffisante, pas d'EU).

### Recommandation

**Choix principal démo : GPT-4.1-mini** (via LiveKit Inference)

| Paramètre | Valeur |
|-----------|--------|
| Provider | OpenAI |
| Modèle | `gpt-4.1-mini` |
| Via | LiveKit Inference |
| Température | `0.0` |

Justification :

1. **Meilleur équilibre instruction-following / function calling / intégration.** IFEval 84,1% + FC score 0,76-0,85. Conçu pour les workflows agentic avec system prompts longs — exactement notre cas (flow 6 étapes, guardrails multiples, 1 tool call).

2. **LiveKit Inference** : `inference.LLM(model="openai/gpt-4.1-mini")`. Zero config, pas de clé API séparée. Co-location avec STT Deepgram et TTS Cartesia → latence réseau minimisée.

3. **EU endpoint GA** : `eu.api.openai.com`, zero data retention. Compatible architecture Option B.

4. **Signal communauté le plus fort** : cas production allemand (agent téléphonique, flux structuré) confirmé fonctionnel.

5. **Coût négligeable** : ~$20/mois pour le pilote.

**Risque principal — TTFT** : 0,55-0,94s dépasse le budget de 400ms. Mitigations :
- Via LiveKit Inference (co-location) : le TTFT réseau est réduit vs API directe
- Le budget est une cible, pas un hard limit — si STT + TTS sont rapides (Deepgram ~300ms + Cartesia ~90ms), le budget total reste ~1,0-1,3s
- GPT-4o-mini (0,2-0,4s) comme fallback rapide si 4.1-mini est trop lent en test réel

**Challenger rapide : GPT-4o-mini**

Si le TTFT de GPT-4.1-mini est inacceptable en test réel (> 800ms mesuré end-to-end), basculer vers GPT-4o-mini :
- TTFT 0,2-0,4s ✅ dans le budget
- IFEval 76,5% — suffisant pour un script rigide en 6 étapes
- Même infrastructure Inference, switch = changer un string

Le tradeoff est clair : 4.1-mini = meilleure qualité, 4o-mini = meilleure latence. Pour la démo, tester les deux et mesurer.

**Challenger production : Mistral Large 3**

Pour la production, si la qualité FR prime sur la latence absolue :
- Meilleur français natif de tous les modèles
- EU natif (hébergé en France) — meilleure posture compliance, pas de transfert hors UE
- TTFT de ~1,1s acceptable si le pipeline est optimisé (STT Deepgram ~200ms + TTS Cartesia ~90ms → budget total ~1,4s)
- Compatible `livekit-plugins-openai` avec `base_url` custom

**Non retenu pour la démo** (pas dans Inference, TTFT trop élevé pour un premier test), mais candidat sérieux pour la prod.

**Fallback HDS : Mistral Large 3 self-hosted sur OVH HDS**

Si le fallback full-HDS s'active (Option A), Mistral est le seul LLM nativement disponible pour un déploiement EU on-premise. vLLM + Mistral Large 3 sur GPU A100/H100 OVH HDS. TTFT self-hosted potentiellement meilleur que l'API (pas de réseau).

**Configuration démo :**

```python
from livekit.agents import inference

llm = inference.LLM(
    model="openai/gpt-4.1-mini",
    temperature=0.0,
)

# Fallback rapide si TTFT trop élevé :
# llm = inference.LLM(
#     model="openai/gpt-4o-mini",
#     temperature=0.0,
# )

# Challenger prod (Mistral, hors Inference) :
# from livekit.plugins import openai
# llm = openai.LLM(
#     model="mistral-large-latest",
#     base_url="https://api.mistral.ai/v1",
#     api_key=os.environ["MISTRAL_API_KEY"],
#     temperature=0.0,
# )
```

[À VALIDER SESSION 1] :
- Bench test TTFT réel : GPT-4.1-mini vs GPT-4o-mini via Inference sur 20 prompts type flow DentalOS (system prompt complet + tool definition + conversation 3-4 tours)
- Test qualité FR : vouvoiement maintenu, pas de code-switch EN, concision des réponses, respect du script 6 étapes
- Test function calling : `verify_patient_identity` appelé au bon moment, paramètres correctement extraits du dialogue patient
- Test guardrails : injection de questions médicales, demandes de conseil, pression commerciale — le LLM doit refuser et rediriger
- Si prod Mistral envisagé : test comparatif qualité FR Mistral Large 3 vs GPT-4.1-mini sur 50 dialogues

---

## 4. Turn Detection & VAD — Détection de fin de tour

### Contraintes use case

| Contrainte | Détail |
|------------|--------|
| Langue | Français — les locuteurs FR pausent **moins souvent** mais **plus longtemps** que les anglophones (littérature linguistique). Un seuil de silence calibré pour l'anglais coupe les Français trop tôt. |
| Contexte | Outbound suivi de devis — le patient **réfléchit** (mutuelle ? intention ? disponibilités ?). Pauses de réflexion de 1-2s fréquentes et légitimes. |
| Interruptions | Peu attendues. Le patient écoute majoritairement. Les backchannels FR typiques (« d'accord », « oui oui », « mmh », « voilà ») ne doivent PAS interrompre l'agent. |
| Audio démo | Browser WebRTC 16kHz — audio plus propre que SIP 8kHz. Moins de bruit, VAD plus fiable. |
| Priorité | **Précision > vitesse**. Mieux vaut 200ms de latence en plus que de couper un patient en pleine réflexion. Le Vapi Playbook (Part 3) cite un cas santé : « patients said 'yes' because they didn't want to slow down the call, not because they understood → 15% higher no-show rates. » |

### Architecture de turn detection LiveKit

LiveKit empile 3 couches complémentaires :

```
Audio patient → [1. Silero VAD] → speech/silence → [2. Turn Detector] → EOU confidence → [3. Endpointing] → turn complete
                                                                                              ↓
                                                            [Adaptive Interruption] → barge-in réel ou backchannel ?
```

| Couche | Rôle | Modèle |
|--------|------|--------|
| **1. VAD** | Détecter quand le patient parle / se tait (niveau audio brut) | Silero VAD (CNN, ~2ms/frame, CPU) |
| **2. Turn Detector** | Prédire sémantiquement si le tour est terminé (niveau texte) | `MultilingualModel` (Qwen2.5-0.5B-Instruct, 396 MB, 50-160ms) |
| **3. Endpointing** | Décider quand déclencher la réponse (combine VAD silence + EOU confidence) | Fixed ou Dynamic (EMA des pauses) |
| **Adaptive Interruption** | Distinguer une interruption réelle d'un backchannel (niveau audio) | Modèle acoustique LiveKit (pré-entraîné sur conversations réelles) |

### MultilingualModel — Turn Detector sémantique

**Import :** `from livekit.plugins.turn_detector.multilingual import MultilingualModel`

| Propriété | Valeur |
|-----------|--------|
| Base model | Qwen2.5-0.5B-Instruct (distillation d'un teacher 7B) |
| Taille disque | 396 MB |
| RAM | < 500 MB |
| Latence par tour | ~50-160ms (CPU) |
| Langues supportées | 14 : en, es, **fr**, de, it, pt, nl, zh, ja, ko, id, tr, ru, hi |
| Paramètres constructeur | **Aucun** — tout le tuning se fait via `EndpointingOptions` |

**Fonctionnement :** le modèle reçoit une fenêtre glissante des 4 derniers tours de conversation (transcription STT). À chaque nouveau mot, il émet un score de confiance « ce tour est-il terminé ? ». Ce score **raccourcit ou allonge dynamiquement** le timeout de silence du VAD :
- Score EOU élevé → le silence court suffit → réponse rapide
- Score EOU bas → le silence est probablement une pause → on attend

**Précision par langue (v0.4.1-intl, à 99,3% True Positive Rate fixé) :**

| Langue | True Negative Rate | False Positive Rate | Amélioration vs v0.3.0 |
|--------|-------------------|--------------------|-----------------------|
| Hindi | **96,30%** | 3,70% | -31,5% |
| Korean | 94,50% | 5,50% | -30,4% |
| **French** | **88,90%** | **11,10%** | **-33,9%** |
| Dutch | 88,10% | 11,90% | -54,3% |
| Japanese | 88,80% | 11,20% | -43,2% |
| German | 87,80% | 12,20% | -47,9% |
| English | 87,00% | 13,00% | -21,7% |
| Portuguese | 87,40% | 12,60% | — |
| Italian | 85,10% | 14,90% | -25,9% |
| Spanish | 86,00% | 14,00% | — |

**Constat FR** : le français a un TNR de 88,9% — **au-dessus de l'anglais** (87,0%). Le modèle est marginalement meilleur pour détecter qu'un francophone n'a pas fini de parler. Le FPR de 11,1% signifie que dans ~1 cas sur 9 où le patient veut continuer, le modèle prédit à tort une fin de tour. C'est le rôle de l'endpointing (min_delay) de compenser.

### Silero VAD — Paramètres complets

**Import :** `from livekit.plugins import silero`

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `activation_threshold` | float | **0.5** | Seuil pour considérer un frame comme parole (0-1). Plus haut = plus conservateur (risque de rater la parole douce). |
| `deactivation_threshold` | float | **activation - 0.15** (= 0.35) | Seuil sous lequel la parole est considérée terminée. Hystérésis pour éviter les oscillations. |
| `min_silence_duration` | float | **0.55s** | Durée de silence après la parole pour déclarer fin de parole. |
| `min_speech_duration` | float | **0.05s** | Durée minimale de parole pour démarrer un speech chunk. |
| `prefix_padding_duration` | float | **0.5s** | Padding ajouté avant chaque speech chunk (capture le début de la parole). |
| `max_buffered_speech` | float | 60.0s | Buffer max. |
| `sample_rate` | 8000 \| 16000 | **16000** | 16kHz pour browser, 8kHz pour SIP. |
| `force_cpu` | bool | True | Forcer l'inférence CPU. |

### EndpointingOptions — Quand déclencher la réponse

**API actuelle** (v1.5.0+). Les anciens paramètres `min_endpointing_delay` / `max_endpointing_delay` sont **dépréciés**.

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `mode` | `"fixed"` \| `"dynamic"` | **`"fixed"`** | `"dynamic"` adapte le délai via une EMA des durées de pause de la session (Python only). |
| `min_delay` | float | **0.5s** | Délai minimum après le dernier mot détecté avant de déclarer le tour terminé. |
| `max_delay` | float | **3.0s** | Délai maximum avant de forcer la fin du tour. |
| `alpha` | float | **0.9** | Coefficient EMA pour le mode dynamic. Plus haut = plus de poids à l'historique. |

**Mode dynamic** : introduit en Agents v1.5.0. Le délai d'endpointing s'ajuste automatiquement au rythme du locuteur via une moyenne mobile exponentielle des pauses. Pour une conversation courte (2-4 min), un `alpha` légèrement plus bas que 0.9 permet une adaptation plus rapide.

### InterruptionOptions — Gestion des interruptions

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `enabled` | bool | **True** | L'agent peut-il être interrompu ? |
| `mode` | `"adaptive"` \| `"vad"` | **`"adaptive"`** (auto si turn detector + STT aligné) | `"adaptive"` = modèle acoustique qui distingue barge-in réel de backchannel. |
| `min_duration` | float | **0.5s** | Durée minimale de parole pour être considérée comme interruption. |
| `min_words` | int | **0** | Nombre minimum de mots transcrits pour déclencher l'interruption (0 = VAD seul). |
| `discard_audio_if_uninterruptible` | bool | True | Jeter l'audio buffered quand l'agent est non-interruptible. |
| `false_interruption_timeout` | float \| None | **2.0s** | Temps d'attente après interruption avant de déclarer fausse interruption. `None` = désactivé. |
| `resume_false_interruption` | bool | **True** | Reprendre la parole de l'agent après fausse interruption détectée. |

**Adaptive interruption** (v1.5.0+) : le modèle est entraîné sur de l'audio conversationnel réel. Il analyse les signaux acoustiques **avant** la transcription pour décider si le patient interrompt vraiment ou produit un backchannel. Supporte toutes les langues (« might perform better with English in some cases, but in most cases it works with any language »).

**Gotcha** : `resume_false_interruption` nécessite un audio output supportant la pause. Si l'output ne le supporte pas, un warning apparaît et la fonctionnalité se dégrade silencieusement.

### Vapi Playbook — Guidance sur le turn-taking (Part 3 Design)

Le Playbook ne donne pas de paramètres VAD (il est platform-agnostic) mais fournit des règles de design conversationnel directement applicables :

| Règle | Application DentalOS |
|-------|---------------------|
| **« Acknowledge → Act → Advance »** | Chaque tour agent : accusé réception (« D'accord. »), action (enregistrer la réponse), avance (question suivante). Ne jamais sauter l'acknowledgement — le patient se sent ignoré. |
| **« One idea, one question per turn »** | Nos 6 étapes respectent déjà cette règle. Ne jamais combiner deux questions dans un tour. |
| **« Two sentences maximum »** | Le LLM doit générer ≤ 2 phrases par tour. Les tours longs causent des interruptions et de la confusion. |
| **« Front-load the important part »** | Mettre la question en premier, pas après un contexte. Ex : « Souhaitez-vous procéder au traitement ? » pas « Compte tenu de votre devis et de ce que vous venez de me dire, est-ce que vous souhaiteriez… » |
| **« Read aloud test »** | Si on manque de souffle en lisant la réponse à voix haute, c'est trop long. |
| **Escalation triggers liés aux interruptions** | Ton frustré → baisser le seuil de transfert humain. Même question posée 3× → escalader. Confiance transcription basse → proposer transfert. Appel > durée attendue → proposer escalade. |

**Sur les interruptions spécifiquement** : le Playbook recommande de ne **jamais** laisser un comportement d'interruption non défini. Trois options : (1) l'agent yield le tour, (2) l'agent finit sa phrase puis yield, (3) l'agent ignore (backchannel). Le choix dépend du contexte — pour un agent consultatif santé, le yield immédiat sur interruption réelle est la norme (l'agent ne « résiste » jamais).

### Comparatif des approches de turn detection

| Approche | Signal | Latence détection | Précision FR | Compute | Use case |
|----------|--------|-------------------|-------------|---------|----------|
| **Silence seule (VAD)** | Audio frames | Élevée (600-800ms+ de seuil) | Faible (coupe les pauses de réflexion) | Minimal | Agents simples, faible ressource |
| **STT endpointing** | Transcript + silence | Moyenne (dépend du provider) | Moyenne | Pipeline STT | Default quand pas de turn detector |
| **MultilingualModel (LiveKit)** | Transcript sémantique | Basse (~50-160ms modèle + silence) | **88,9% TNR** | ~500 MB RAM, CPU | ✅ **Notre choix** |
| **Audio-based EOU (Pipecat Smart Turn)** | Prosodie audio | Très basse (~10-65ms) | Non publié pour FR | ~8-32 MB | Speed-critical |
| **Hybride (AssemblyAI intégré)** | Audio + texte + token spécial | Adaptive | Non publié pour FR | Intégré au STT | Précision maximale |

### Paramètres recommandés — Configuration démo DentalOS

```python
from livekit.agents import AgentSession, TurnHandlingOptions
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.plugins import silero

session = AgentSession(
    # --- VAD : Silero ---
    vad=silero.VAD.load(
        activation_threshold=0.5,      # Défaut. Browser audio = propre, pas besoin de baisser.
        min_silence_duration=0.6,      # 600ms (défaut 550ms). Légèrement relevé pour le FR :
                                       # les pauses FR sont moins fréquentes mais plus longues.
        min_speech_duration=0.05,      # Défaut 50ms.
        prefix_padding_duration=0.5,   # Défaut 500ms.
        sample_rate=16000,             # 16kHz pour audio browser.
    ),

    # --- Turn Handling ---
    turn_handling=TurnHandlingOptions(
        # Turn Detection : modèle sémantique multilingue
        turn_detection=MultilingualModel(),
        # FR : 88,9% TNR, au-dessus de l'anglais. 50-160ms latence CPU.

        # Endpointing : mode dynamique, seuils conservateurs
        endpointing={
            "mode": "dynamic",        # Adapte le délai au rythme du patient au fil de l'appel.
            "min_delay": 0.7,         # 700ms (défaut 500ms). Conservateur pour le FR santé.
                                      # Vapi recommande 0.6-0.8s pour healthcare/formal.
                                      # Compense le FPR de 11,1% du modèle sur le FR.
            "max_delay": 4.0,         # 4s (défaut 3s). Le patient peut réfléchir longtemps
                                      # sur sa mutuelle ou ses disponibilités.
            "alpha": 0.85,            # Légèrement sous le défaut (0.9) pour s'adapter plus vite
                                      # dans une conversation courte (2-4 min, ~10-15 tours).
        },

        # Interruption : adaptive, conservateur
        interruption={
            "mode": "adaptive",       # Filtre les backchannels FR : "d'accord", "oui oui",
                                      # "mmh", "voilà", "bon". Modèle acoustique pré-entraîné.
            "min_duration": 0.6,      # 600ms (défaut 500ms). Plus conservateur pour éviter
                                      # les fausses interruptions sur les fillers FR courts.
            "min_words": 0,           # VAD-based pour un barge-in réactif si le patient
                                      # veut vraiment interrompre.
            "resume_false_interruption": True,   # Reprendre si c'était un backchannel.
            "false_interruption_timeout": 2.5,   # 2,5s (défaut 2,0s). Légèrement plus long
                                                 # pour laisser le temps de confirmer.
        },

        # Preemptive generation : activée pour compenser la latence LLM
        preemptive_generation={
            "enabled": True,          # Démarre la génération LLM avant la fin confirmée du tour.
            "preemptive_tts": False,  # Pas de TTS préemptif — précision > vitesse.
        },
    ),

    stt=stt,   # Deepgram Nova-3 avec language="fr" (cf. section 1)
    llm=llm,   # GPT-4.1-mini (cf. section 3)
    tts=tts,   # Cartesia Sonic-3 (cf. section 2)
)
```

### Justification paramètre par paramètre

| Paramètre | Valeur | Défaut | Justification |
|-----------|--------|--------|---------------|
| `turn_detection` | `MultilingualModel()` | auto | 88,9% TNR FR (> anglais). Sémantique > silence seule pour les pauses de réflexion patient. |
| `endpointing.mode` | `"dynamic"` | `"fixed"` | Adapte le seuil au rythme du patient. Un patient rapide (jeune, décidé) aura des seuils plus bas ; un patient lent (âgé, hésitant) aura des seuils plus hauts — automatiquement. |
| `endpointing.min_delay` | **0.7s** | 0.5s | Vapi recommande 0.6-0.8s pour healthcare/formal. 700ms = milieu de fourchette. Le modèle a 11,1% FPR sur le FR — le min_delay compense en imposant un silence minimum même si le modèle dit « turn complete ». |
| `endpointing.max_delay` | **4.0s** | 3.0s | Le patient peut réfléchir longuement (« ma mutuelle… euh… je ne sais plus… »). 4s avant de forcer la fin du tour. Au-delà, le silence est probablement un abandon ou une déconnexion. |
| `endpointing.alpha` | **0.85** | 0.9 | Conversation courte (2-4 min) = peu de tours pour calibrer l'EMA. Un alpha plus bas donne plus de poids aux tours récents → adaptation plus rapide. |
| `interruption.mode` | `"adaptive"` | adaptive | Critique pour notre use case. Les backchannels FR (« d'accord », « mmh », « oui oui ») sont fréquents et ne doivent pas interrompre l'agent. Le modèle acoustique les filtre avant transcription. |
| `interruption.min_duration` | **0.6s** | 0.5s | +100ms vs défaut. Les fillers FR courts (« bon », « ben ») durent ~200-400ms. À 600ms, on s'assure qu'une interruption est intentionnelle (au moins un mot complet articulé). |
| `false_interruption_timeout` | **2.5s** | 2.0s | Après détection d'une fausse interruption, on attend 2,5s avant de confirmer que c'était bien un backchannel. Le patient peut enchaîner « mmh… en fait non » → l'agent doit attendre. |
| `resume_false_interruption` | **True** | True | Si le patient dit « mmh » pendant que l'agent parle, l'agent reprend sa phrase. Expérience naturelle. |
| `vad.activation_threshold` | **0.5** | 0.5 | Audio browser = propre. Défaut approprié. Baisser à 0.3 uniquement si on passe en SIP 8kHz bruyant. |
| `vad.min_silence_duration` | **0.6s** | 0.55s | +50ms. Littérature : les francophones font des pauses moins fréquentes mais plus longues. Ce paramètre est le filet de sécurité VAD quand le turn detector n'est pas encore prêt. |

### Gotchas et risques identifiés

| # | Risque | Impact | Mitigation |
|---|--------|--------|------------|
| 1 | **Code langue ISO 639-1 obligatoire** : le `MultilingualModel` attend `"fr"`, pas `"french"`. Si le STT retourne le nom complet → erreur `"Turn detector does not support language french"`. | Crash turn detector → fallback VAD seul | Configurer `language="fr"` explicitement sur le STT (déjà fait § section 1). |
| 2 | **11,1% FPR français** : dans ~1 cas sur 9, le modèle coupe le patient qui voulait continuer. | Agent répond trop tôt, patient frustré | `min_delay=0.7s` + `mode="dynamic"` compensent. Monitor `end_of_utterance_delay` en eval. |
| 3 | **Adaptive interruption peut échouer définitivement** : après 3 tentatives échouées, le système tombe en fallback VAD-based. Signalé sur Python et Node.js (avril 2026). | Backchannels non filtrés → interruptions parasites | Surveiller les logs pour `InterruptionDetectionError`. Fallback VAD acceptable pour la démo. |
| 4 | **Patient dit « oui… euh… enfin oui »** avec pause longue entre « oui » et « euh ». | Le modèle peut déclencher sur le premier « oui ». | Le modèle sémantique analyse « oui » dans le contexte de la question posée. Avec 700ms min_delay et mode dynamic, la plupart des cas sont couverts. Eval spécifique à prévoir. |
| 5 | **Patients âgés : rythme plus lent, pauses plus longues.** | `max_delay` de 3s (défaut) pourrait forcer la fin du tour prématurément. | `max_delay=4.0s` + mode dynamic adapte le seuil vers le haut. |
| 6 | **`resume_false_interruption` nécessite un audio output supportant pause.** | Si non supporté → warning silencieux, fonctionnalité inactive. | Cartesia via LiveKit Inference supporte la pause (à confirmer en test). |
| 7 | **Latence totale EOU** : VAD + transcription + turn detection + endpointing s'additionnent. Un utilisateur forum mesure ~900ms EOU avec min_delay=0.4 et Deepgram. | Notre min_delay=0.7 → EOU potentiellement ~1,0-1,2s. | Acceptable dans notre contexte (précision > vitesse). `preemptive_generation` compense en démarrant le LLM en parallèle. |
| 8 | **`AudioSource(queue_size_ms)` défaut à 1000ms** ajoute ~400ms de latence. | Latence round-trip gonflée. | Réduire à 10ms si on constate une latence excessive en démo (`AudioSource(queue_size_ms=10)`). |

### API utiles en runtime

```python
# Désactiver les interruptions pendant un segment critique (ex : phrase d'urgence 15/112)
await session.disallow_interruptions()

# Réactiver
await session.allow_interruptions()

# Mettre à jour les paramètres d'endpointing en cours de session
session.update_options(
    endpointing_opts=EndpointingOptions(
        min_delay=0.9,   # Ex : augmenter si le patient est particulièrement lent
        max_delay=5.0,
    ),
)

# Switcher du modèle sémantique au VAD seul (si problème)
session.update_options(turn_detection="vad")
```

[À VALIDER SESSION 1] :
- Test EOU delay réel : mesurer `end_of_utterance_delay` sur 20 conversations FR type DentalOS. Cible : < 1,2s P50, < 2,0s P99
- Test backchannel filtering : 10 scénarios avec « d'accord », « mmh », « oui oui », « voilà » pendant que l'agent parle → l'agent doit reprendre sans s'interrompre
- Test pauses de réflexion : 10 scénarios avec pauses 1-2s mid-utterance (« ma mutuelle… [1,5s]… non je n'ai pas encore eu de réponse ») → l'agent ne doit pas couper
- Test patient âgé : 5 scénarios avec rythme lent et pauses longues (2-3s) → vérifier que le mode dynamic adapte le seuil vers le haut
- A/B test min_delay : 0.5 vs 0.7 vs 0.9 sur taux de fausses interruptions
- Vérifier que `resume_false_interruption` fonctionne avec Cartesia via Inference

---

## 5. Hyperparameters & Audio Config — Tableau exhaustif

Cette section consolide **tous** les paramètres configurables pour la démo DentalOS, au-delà des choix de providers (sections 1-4). C'est la checklist de configuration complète.

### 5.1 Tableau master — Paramètres par catégorie

#### A. LLM & Prompt

| Paramètre | Valeur démo | Défaut LiveKit | Justification | Source |
|-----------|-------------|----------------|---------------|--------|
| `temperature` | **0.0** | Dépend du provider | Flow rigide 6 étapes, pas de créativité. CLAUDE.md : « température 0.0 par défaut ». Vapi Playbook : « Specificity is the whole game. Vague prompts produce vague agents. » | CLAUDE.md § Runtime Rules, Vapi Ch. 12 |
| `max_tool_steps` | **3** | 3 | 1 seul tool call attendu (`verify_patient_identity`), mais 3 permet un retry si le premier échoue. | docs.livekit.io/agents/logic/sessions |
| Réponses LLM | **≤ 2 phrases par tour** | N/A (prompt) | Vapi Playbook : « Keep responses to two sentences maximum. Read every response aloud. If it sounds like a paragraph, it's too long for a voice. » | Vapi Ch. 12 |
| Structure prompt | **5 sections** : identité, style, tâche, guardrails, instructions tools | N/A (prompt) | Vapi Playbook : « Structure prompts in five sections: Identity, style, task, guardrails, tool instructions. » | Vapi Ch. 12 |
| Tour agent | **Acknowledge → Act → Advance** | N/A (design) | Vapi Playbook : « Elena's first agent skipped the acknowledgement. Callers felt ignored. » | Vapi Ch. 9 |

#### B. Turn Detection & Endpointing (rappel section 4)

| Paramètre | Valeur démo | Défaut | Justification | Source |
|-----------|-------------|--------|---------------|--------|
| `turn_detection` | `MultilingualModel()` | auto | FR : 88,9% TNR. Sémantique > silence. | docs turn-detector |
| `endpointing.mode` | `"dynamic"` | `"fixed"` | Adapte au rythme patient. | docs turn-handling-options |
| `endpointing.min_delay` | **0.7s** | 0.5s | Healthcare/formal. Vapi recommande 0.6-0.8s. | Vapi config, docs |
| `endpointing.max_delay` | **4.0s** | 3.0s | Pauses de réflexion longues (mutuelle, disponibilités). | docs turn-handling-options |
| `endpointing.alpha` | **0.85** | 0.9 | Adaptation plus rapide sur conversation courte (2-4 min). | docs turn-handling-options |

#### C. Interruptions

| Paramètre | Valeur démo | Défaut | Justification | Source |
|-----------|-------------|--------|---------------|--------|
| `interruption.mode` | `"adaptive"` | adaptive (auto) | Filtre backchannels FR (« d'accord », « mmh »). | docs adaptive-interruption |
| `interruption.min_duration` | **0.6s** | 0.5s | +100ms pour éviter les fausses interruptions sur fillers FR courts. | docs turn-handling-options |
| `interruption.min_words` | **0** | 0 | VAD-based pour barge-in réactif. | docs turn-handling-options |
| `interruption.false_interruption_timeout` | **2.5s** | 2.0s | Patient peut enchaîner « mmh… en fait non ». | docs turn-handling-options |
| `interruption.resume_false_interruption` | **True** | True | Agent reprend si backchannel. | docs turn-handling-options |
| `interruption.discard_audio_if_uninterruptible` | **True** | True | Défaut. Jette l'audio buffered pendant les segments non-interruptibles. | docs turn-handling-options |

#### D. Interruptions par étape du flow

| Étape | `allow_interruptions` | Justification |
|-------|----------------------|---------------|
| **Étape 1 — Annonce** (cabinet + enregistrement + motif) | **False** | Obligation légale : l'annonce d'enregistrement doit être prononcée intégralement. Le patient ne doit pas couper avant d'avoir entendu la mention d'enregistrement. Vapi Playbook : « In two-party consent states, the agent explicitly asked for permission. » |
| **Étape 2 — Vérification identité** | **True** | Le patient répond naturellement, peut corriger. |
| **Étape 3 — Question mutuelle** | **True** | Réponse courte attendue. |
| **Étape 4 — Question intention** | **True** | Réponse courte attendue. |
| **Étape 5 — Disponibilités** | **True** | Le patient décrit ses créneaux, peut hésiter et se corriger. |
| **Étape 6 — Clôture** (récap + au revoir) | **False** | Le récapitulatif doit être entendu en entier pour confirmation implicite. Si le patient veut corriger, il parlera après la clôture et l'agent pourra traiter. |
| **Phrase urgence 15/112** | **False** | Phrase auditée de sécurité — doit être prononcée intégralement. `session.disallow_interruptions()` avant, rétablir après. |
| **Tool call `verify_patient_identity`** | **disallow** | `run_ctx.disallow_interruptions()` : le tool call doit aller à son terme (écriture état). |

**Implémentation :**
```python
# Étape 1 — Annonce non-interruptible
await self.session.generate_reply(
    instructions="...",
    allow_interruptions=False,
)

# Étapes 2-5 — Interruptible (défaut)
await self.session.generate_reply(
    instructions="...",
    # allow_interruptions=True (défaut)
)

# Étape 6 — Récap non-interruptible
await self.session.say(
    recap_text,
    allow_interruptions=False,
)

# Phrase urgence
await self.session.disallow_interruptions()
await self.session.say(EMERGENCY_PHRASE, allow_interruptions=False)
await self.session.allow_interruptions()
```

#### E. AEC & Audio Pipeline

| Paramètre | Valeur démo | Défaut | Justification | Source |
|-----------|-------------|--------|---------------|--------|
| `aec_warmup_duration` | **3.0s** | 3.0s | Défaut conservateur. Bloque les interruptions pendant 3s après que l'agent commence à parler (1ère fois) pour laisser l'AEC converger. Logs : `"aec warmup active, disabling interruptions for 3.00s"`. | docs AgentSession |
| `noise_cancellation` | **None** (démo browser) | None | Browser WebRTC a déjà `echoCancellation` + `noiseSuppression` natifs. Pas besoin de Krisp BVC pour la démo. En prod SIP : `noise_cancellation.BVCTelephony()`. | docs noise-cancellation |
| `audio_sample_rate` (input) | **24000** | 24000 | Défaut LiveKit. Browser WebRTC capture à 48kHz puis resample. | docs RoomInputOptions |
| `audio_num_channels` | **1** | 1 | Mono. Voix téléphonique = mono. | docs RoomInputOptions |
| `audio_frame_size_ms` | **50** | 50 | Défaut. Taille de frame pour le traitement audio. | docs RoomInputOptions |
| `pre_connect_audio` | **False** (outbound) | True | Pour un appel sortant, c'est l'agent qui initie — pas de micro utilisateur à capturer en amont. Pertinent uniquement en inbound. | docs RoomInputOptions |
| `pre_connect_audio_timeout` | 3.0s | 3.0s | Sans objet si `pre_connect_audio=False`. | docs RoomInputOptions |

**Noise cancellation — quand utiliser quoi :**

| Contexte | Modèle NC | Justification |
|----------|-----------|---------------|
| **Démo browser** | **Aucun** (`None`) | WebRTC intégré suffit. Audio propre. |
| **Prod SIP** | `noise_cancellation.BVCTelephony()` | Optimisé téléphonie. Filtre voix de fond + bruit. |
| **Prod SIP (trunk-level)** | `krisp_enabled=True` sur le trunk | NC standard Krisp appliqué au niveau SIP. Pas de BVC au trunk. |
| **Prod SIP + environnement bruyant** | `ai_coustics.audio_enhancement(model=EnhancerModel.QUAIL_VF_L)` | Voice Focus : isolation du locuteur. WER 117,6% → 11,8%. |

#### F. Preemptive Generation

| Paramètre | Valeur démo | Défaut | Justification | Source |
|-----------|-------------|--------|---------------|--------|
| `preemptive_generation.enabled` | **True** | True | Le LLM démarre l'inférence avant confirmation du tour → compense le TTFT de GPT-4.1-mini (0,55-0,94s). | docs turn-handling-options |
| `preemptive_generation.preemptive_tts` | **False** | False | Ne pas lancer le TTS avant confirmation. Raison : si le tour change (patient continue), le TTS aurait synthétisé du texte incorrect → gaspillage + risque de réponse incorrecte audible. Pour notre use case (précision > vitesse), on attend la confirmation. | docs preemptive-generation |
| `preemptive_generation.max_speech_duration` | **10.0s** | 10.0s | Défaut. Au-delà de 10s de parole patient, la preemptive generation est skipée (l'utterance va probablement changer). | docs preemptive-generation |
| `preemptive_generation.max_retries` | **3** | 3 | Défaut. 3 tentatives preemptive max par tour avant de revert au flow normal. | docs preemptive-generation |

#### G. TTS Text Transforms

| Paramètre | Valeur démo | Défaut | Justification | Source |
|-----------|-------------|--------|---------------|--------|
| `filter_markdown` | **Oui** (inclus) | Oui | Le LLM peut générer du markdown (`**texte**`, `- liste`). Le TTS ne doit pas prononcer les astérisques. | docs text-transforms |
| `filter_emoji` | **Oui** (inclus) | Oui | Le LLM peut générer des emoji. Le TTS ne doit pas tenter de les prononcer. | docs text-transforms |
| `text_transforms.replace(...)` | **Oui** — dictionnaire dentaire | Non (pas de custom par défaut) | Prononciation correcte des termes dentaires et abréviations. Cartesia supporte la notation IPA via `<< >>`. | docs text-transforms |

**Dictionnaire de remplacement démo :**
```python
from livekit.agents import text_transforms

dental_replacements = text_transforms.replace({
    # Abréviations courantes
    "RDV": "rendez-vous",
    "Dr ": "Docteur ",
    "Dr.": "Docteur",
    # Termes qui pourraient être mal prononcés
    "parodontie": "parodontie",        # Confirmer la prononciation Cartesia
    "devis": "devis",                   # /dəvi/ pas /dɛvis/
    # Noms de cabinet (à personnaliser par cabinet pilote)
    # "CabinetXYZ": "Cabinet X Y Z",
}, case_sensitive=False)

tts_text_transforms = [
    "filter_emoji",
    "filter_markdown",
    dental_replacements,
]
```

#### H. Greeting & Timing

| Paramètre | Valeur démo | Défaut | Justification | Source |
|-----------|-------------|--------|---------------|--------|
| Greeting pattern | **`session.generate_reply(instructions=..., allow_interruptions=False)`** | N/A | L'annonce étape 1 est générée par le LLM (pas un `session.say` statique) pour gérer les variables (cabinet, praticien, catégorie). `allow_interruptions=False` car mention d'enregistrement obligatoire. | docs audio, CLAUDE.md § Scope V1 |
| Outbound timing | **Attendre que le patient décroche et parle en premier** | N/A | Docs LiveKit : « When placing an outbound call, let the callee speak first. » En démo browser : le participant joint la room et l'agent démarre dans `on_enter`. | docs outbound-calls |
| `min_consecutive_speech_delay` | **0.0s** | 0.0s | Pas de pause artificielle entre les utterances agent. Le flow est séquentiel naturellement. | docs AgentSession |

**Pattern démo (browser, pas SIP) :**
```python
class DentalAgent(Agent):
    async def on_enter(self):
        # En démo browser : le patient est déjà dans la room.
        # En prod SIP outbound : attendre le participant SIP d'abord.
        await self.session.generate_reply(
            instructions=(
                "Annonce-toi : tu appelles de la part du cabinet [nom_cabinet]. "
                "Informe que l'appel est enregistré. "
                "Indique le motif : un devis de [catégorie] du [praticien] émis le [date]. "
                "Demande si c'est un bon moment pour en parler."
            ),
            allow_interruptions=False,
        )
```

#### I. Voicemail Detection

| Paramètre | Valeur démo | Défaut | Justification | Source |
|-----------|-------------|--------|---------------|--------|
| Voicemail detection | **Off** (pas de tool) | N/A | Démo browser uniquement — pas de répondeur. En prod SIP : ajouter un function tool `detected_answering_machine` que le LLM appelle s'il détecte un message de répondeur. LiveKit n'a pas d'AMD (Answering Machine Detection) intégré — la détection est déléguée au LLM. | docs outbound-calls |

**Pattern prod (à ajouter post-démo) :**
```python
@function_tool
async def detected_answering_machine(self):
    """Appelle cet outil si tu détectes un répondeur APRÈS avoir entendu le message d'accueil."""
    await self.session.generate_reply(
        instructions=(
            "Laisse un message vocal bref (< 20s) : "
            "le cabinet [nom], motif de l'appel, demande de rappel."
        ),
    )
    await asyncio.sleep(0.5)
    await hangup_call()
```

#### J. Session Lifecycle

| Paramètre | Valeur démo | Défaut | Justification | Source |
|-----------|-------------|--------|---------------|--------|
| `user_away_timeout` | **30.0s** | 15.0s | Patient peut poser le téléphone brièvement pour chercher un document (mutuelle, agenda). 15s trop court. 30s laisse de la marge. | docs AgentSession |
| `session_close_transcript_timeout` | **2.0s** | 2.0s | Défaut. Temps d'attente pour le transcript STT final à la fermeture. | docs AgentSession |
| `close_on_disconnect` | **True** | True | Si le patient quitte la room (raccroche), fermer la session. | docs RoomInputOptions |
| `delete_room_on_close` | **False** | False | Garder la room pour le debugging post-appel. | docs RoomInputOptions |
| `ivr_detection` | **False** | False | Pas de navigation IVR en démo browser. En prod outbound, si le patient a un standard auto : à activer. | docs AgentSession |

#### K. Observabilité & Métriques (config agent)

| Paramètre / Métrique | Valeur | Source |
|----------------------|--------|--------|
| `end_of_utterance_delay` | À monitorer — cible < 1,2s P50 | docs observability |
| `transcription_delay` | À monitorer | docs observability |
| `on_user_turn_completed_delay` | À monitorer | docs observability |
| Métrique latence | **P90 TTFT** (pas P50) | Forum : « p50 hides the spikes that bite you in voice » |
| Correlation ID | **call_id** dans tous les logs | CLAUDE.md § Code Style |

### 5.2 Vapi Playbook — First Call Quality Checklist

Le Playbook (Part 3 Design, Part 5 Test, Part 6 Launch) fournit une checklist de qualité pré-launch. Application au use case DentalOS :

#### Design Checklist (Part 3)

| # | Check | Statut DentalOS | Action |
|---|-------|----------------|--------|
| 1 | **Lis chaque tour à voix haute.** Tu manques de souffle ? Tu perds le fil ? | ⬜ À tester | Tester les 6 étapes à voix haute sur les prompts FR |
| 2 | **Compte les options par tour.** Plus de 3 choix présentés ? | ✅ | Max 3 choix : mutuelle (oui/non/sais pas), intention (oui/non/réfléchis) |
| 3 | **Trouve les slots high-stakes.** Dates, noms, montants — chacun confirmé immédiatement ? | ⚠️ Partiel | Nom + prénom + DOB confirmés par le backend (match/no-match). Disponibilités récapitulées en étape 6. |
| 4 | **Repère les questions ouvertes.** « Que souhaitez-vous faire ? » → remplacer par des choix fermés. | ✅ | Questions fermées sauf disponibilités (texte libre structuré) |
| 5 | **Vérifie les limites de retry.** Plus de 3 tentatives avant escalade ? | ✅ | 2 tentatives identité (plus strict que le Playbook qui dit 3) |
| 6 | **Trouve les URLs/références lues à voix haute** au lieu d'être poussées par SMS/email. | ✅ | Aucune URL ni référence lue. Juste la catégorie et le praticien (une seule fois). |
| 7 | **Teste la phrase d'escalade.** Gracieuse ou apologétique ? | ⬜ À tester | Vérifier le wording de la redirection cabinet |
| 8 | **Aligne avec le goal.** Si revenue → handles-tu les objections ? Si CX → es-tu patient ? | ✅ | Goal = conversion. Pas d'objection handling (consultatif, pas commercial). Patient = on ne presse pas. |

#### Enterprise Readiness — 7 Domaines (Part 6)

| # | Domaine | Items clés pour DentalOS démo | Statut |
|---|---------|-------------------------------|--------|
| 1 | **Scope & safety** | Tous les intents supportés testés ? Boundaries avec fallbacks explicites ? Retries bornés ? Tool-first truth ? | ⬜ Post-démo |
| 2 | **Tooling & integrations** | Contrats tools documentés ? Timeouts définis ? Idempotence ? Error taxonomy complète ? | ⬜ Post-démo |
| 3 | **Voice UX reliability** | Interruptions gérées ? Confirmation progressive ? Désambiguïsation ? | ✅ Section 4 + 5 |
| 4 | **Security & compliance** | Access controls, audit logging, rétention, consentement ? | ⚠️ Consentement enregistrement = étape 1. Reste à implémenter. |
| 5 | **Observabilité** | Logs structurés ? Dashboards ? Alertes ? Replay d'appel ? Rollback ? | ⬜ Post-démo |
| 6 | **Quality gates** | Suite de régression ? Tests audio bruyant ? Load tests ? Human review ? | ⬜ Post-démo |
| 7 | **Économie** | Budget pilote calculé ? | ✅ STT ~$150 + TTS ~$375 + LLM ~$20 ≈ $545/mois |

#### Test Suite Standard (Part 5)

| Catégorie | Nombre scénarios | Application DentalOS |
|-----------|-----------------|---------------------|
| Happy path | 20 | 20 conversations complètes étapes 1→6 avec variations de réponses |
| Edge cases | 20 | Interruptions, corrections, hésitations, « je ne sais pas » × 3, timeout patient |
| Adversarial | 10 | Injection prompt, demande conseil médical, pression pour un RDV, tentative d'identification frauduleuse |
| Audio réalisme | × chaque scénario | Audio propre + bruit de fond + basse qualité + 3 accents FR |
| **Total** | ~50 × 4 = **~200 runs** | Vapi : « Clean-audio-only testing misses 40% of failures » |

**5 dimensions de scoring par scénario :**

| Dimension | Critère DentalOS |
|-----------|-----------------|
| **Task completion** | Les 6 étapes complétées ? CallOutcome correct ? |
| **Policy compliance** | Aucune safety rule violée ? Pas de conseil médical, estimation mutuelle, pression ? |
| **Naturalness** | Vouvoiement maintenu ? Concis ? Pas de jargon technique ? Pas de code-switch EN ? |
| **Escalation appropriateness** | Urgence → 15/112 ? Demande humain → transfert ? Hors scope → redirection cabinet ? |
| **Persona consistency** | Ton consultatif maintenu même sous stress (patient frustré, questions hors scope) ? |

### 5.3 Configuration complète démo — Code assemblé

```python
from livekit.agents import (
    AgentSession,
    TurnHandlingOptions,
    text_transforms,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.plugins import silero
from livekit.agents import inference

# --- STT (section 1) ---
stt = inference.STT(
    model="deepgram/nova-3-general",
    language="fr",
)

# --- LLM (section 3) ---
llm = inference.LLM(
    model="openai/gpt-4.1-mini",
    temperature=0.0,
)

# --- TTS (section 2) ---
tts = inference.TTS(
    "cartesia/sonic-3",
    voice="a8a1eb38-5f15-4c1d-8722-7ac0f329727d",  # Calm French Woman
    language="fr",
)

# --- VAD (section 4) ---
vad = silero.VAD.load(
    activation_threshold=0.5,
    min_silence_duration=0.6,
    min_speech_duration=0.05,
    prefix_padding_duration=0.5,
    sample_rate=16000,
)

# --- Text transforms (section 5) ---
dental_replacements = text_transforms.replace({
    "RDV": "rendez-vous",
    "Dr ": "Docteur ",
    "Dr.": "Docteur",
}, case_sensitive=False)

# --- Session ---
session = AgentSession(
    stt=stt,
    llm=llm,
    tts=tts,
    vad=vad,

    # Turn handling (section 4 + 5)
    turn_handling=TurnHandlingOptions(
        turn_detection=MultilingualModel(),
        endpointing={
            "mode": "dynamic",
            "min_delay": 0.7,
            "max_delay": 4.0,
            "alpha": 0.85,
        },
        interruption={
            "mode": "adaptive",
            "min_duration": 0.6,
            "min_words": 0,
            "resume_false_interruption": True,
            "false_interruption_timeout": 2.5,
        },
        preemptive_generation={
            "enabled": True,
            "preemptive_tts": False,
            "max_speech_duration": 10.0,
            "max_retries": 3,
        },
    ),

    # Text transforms
    tts_text_transforms=[
        "filter_emoji",
        "filter_markdown",
        dental_replacements,
    ],

    # Session params
    aec_warmup_duration=3.0,
    user_away_timeout=30.0,
    max_tool_steps=3,
    min_consecutive_speech_delay=0.0,
    ivr_detection=False,
)
```

**RoomOptions démo (browser, pas de NC) :**
```python
from livekit.agents import room_io

room_options = room_io.RoomOptions(
    audio_input=room_io.AudioInputOptions(
        noise_cancellation=None,     # Browser WebRTC AEC/NC suffit
        pre_connect_audio=False,     # Outbound : pas de pre-connect
        audio_sample_rate=24000,
        audio_num_channels=1,
    ),
    audio_output=room_io.AudioOutputOptions(
        audio_sample_rate=24000,
        audio_num_channels=1,
    ),
)

# Start
await session.start(
    agent=DentalAgent(),
    room=ctx.room,
    room_options=room_options,
)
```

**RoomOptions prod SIP (à préparer) :**
```python
# Prod SIP : activer Krisp BVCTelephony
from livekit.plugins import noise_cancellation

room_options_prod = room_io.RoomOptions(
    audio_input=room_io.AudioInputOptions(
        noise_cancellation=noise_cancellation.BVCTelephony(),
        audio_sample_rate=24000,
        audio_num_channels=1,
    ),
)
```

### 5.4 Différences démo → prod

| Paramètre | Démo (browser) | Prod (SIP outbound) |
|-----------|---------------|---------------------|
| `noise_cancellation` | None | `BVCTelephony()` |
| `pre_connect_audio` | False | False (outbound) |
| `ivr_detection` | False | True (si standard auto patient) |
| Voicemail detection | Off | Tool LLM `detected_answering_machine` |
| `vad.sample_rate` | 16000 (browser) | 8000 ou 16000 (dépend du codec SIP) |
| STT `keyterms` | Non (Inference) | Oui (plugin Deepgram direct avec keyterms) |
| `aec_warmup_duration` | 3.0s | 3.0s (ou plus si écho SIP) |
| `user_away_timeout` | 30.0s | 20.0s (SIP = pas de recherche de document) |
| Greeting | `on_enter` immédiat | Attendre SIP participant join + premier audio |

[À VALIDER SESSION 1] :
- Test end-to-end de la configuration assemblée sur une room LiveKit Cloud avec un participant browser
- Vérifier que `filter_markdown` + `filter_emoji` + `replace` s'appliquent correctement sur les réponses GPT-4.1-mini en FR
- Vérifier que `allow_interruptions=False` fonctionne sur `generate_reply` avec Cartesia via Inference
- Tester le `user_away_timeout=30s` : le patient disparaît 25s → l'agent ne doit pas clôturer
- Run de la Design Checklist Vapi (8 items) sur les prompts FR rédigés
- Identifier les termes dentaires nécessitant un remplacement IPA dans le dictionnaire custom

---

## 6. Anti-patterns & Checklist démo

### 6.1 Anti-patterns — 12 pièges à éviter

Chaque anti-pattern est sourcé (Vapi Playbook, forum LiveKit, littérature voice AI). Pour chacun : description du piège, mitigation appliquée dans notre stack.

#### AP-1 — Dead air au décrochage (> 1s de silence)

**Piège** : le patient dit « Allo ? » et entend le silence. 23% raccrochent après 3s de dead air sur un appel sortant. Le premier mot de l'agent détermine si le patient reste ou raccroche. « The tone, timing, and message in those first five seconds decide everything. » (Sierra)

**Mitigation DentalOS** :
- `on_enter` déclenche `generate_reply(allow_interruptions=False)` immédiatement
- `preemptive_generation.enabled=True` → le LLM commence avant confirmation du tour
- En prod SIP : `wait_until_answered=True` sur le SIP participant pour ne pas parler avant le décrochage
- Cible : < 600ms entre le premier audio patient et le premier mot agent

#### AP-2 — Latence > 1,5s en cours de flow

**Piège** : au-delà de 1,5s de latence end-to-end, le patient parle par-dessus l'agent, répète sa réponse, ou raccroche. P50 en production est déjà à 1,4-1,7s sur la majorité des déploiements voice AI. « Experience degrades rapidly beyond ~1.5 seconds. » (Hamming AI)

**Mitigation DentalOS** :
- Budget TTFT cible : STT ~300ms + LLM ~400ms + TTS ~90ms = ~790ms
- `preemptive_generation.enabled=True` compense le TTFT LLM de 4.1-mini (~0,7s)
- LiveKit Inference → co-location réseau STT/LLM/TTS
- `endpointing.mode="dynamic"` → le tour se termine plus vite quand le modèle est confiant
- Monitor : P90 TTFT (pas P50) — « p50 hides the spikes that bite you in voice » (forum LiveKit)

#### AP-3 — Couper le patient pendant la collecte de la DOB

**Piège** : le patient dit « je suis né le quatorze… [pause 1,2s]… mars… [pause 0,8s]… mille neuf cent soixante-dix-huit » et l'agent coupe après « quatorze ». Le VAD seul interprète la pause de réflexion comme une fin de tour. « If a user pauses 500ms to remember a word, a basic VAD might signal the AI to start talking. » (Speechmatics)

**Mitigation DentalOS** :
- `turn_detection=MultilingualModel()` → détection sémantique (« quatorze » isolé n'est pas un tour complet)
- `endpointing.min_delay=0.7s` → même si le modèle est confiant, on attend 700ms
- `endpointing.max_delay=4.0s` → on laisse jusqu'à 4s pour une DOB longue
- `endpointing.mode="dynamic"` → le seuil s'adapte au rythme du patient

#### AP-4 — Réponses trop longues (LLM verbeux)

**Piège** : le LLM génère 3-4 phrases de contexte avant de poser sa question. Le patient oublie la question, interrompt, ou décroche. « Elena's first agent delivered paragraphs of context before asking questions. Callers forgot the question by the time she asked it. » (Vapi Ch. 9). L'attention humaine pour la parole chute après 8-10 secondes.

**Mitigation DentalOS** :
- `temperature=0.0` → pas de créativité, réponses prévisibles
- Prompt : « Réponds en 1-2 phrases maximum. Une idée, une question par tour. »
- Structure Vapi : Acknowledge → Act → Advance (chaque tour)
- `tts_text_transforms=["filter_markdown", "filter_emoji", ...]` → pas de formatting lu à voix haute
- Test : aucune utterance agent > 15 secondes de parole

#### AP-5 — LLM qui extrapole sur le médical/financier

**Piège** : le patient demande « c'est remboursé à combien ? » et le LLM improvise une estimation basée sur ses connaissances générales. Ou le patient demande « c'est vraiment nécessaire ? » et le LLM donne un avis clinique. « Anytime you let an LLM decide what to say, you're at risk. » (GrowwStacks). « Improvised error handling in voice was almost always wrong. » (Vapi Ch. 18)

**Mitigation DentalOS** :
- Guardrails par tour (CLAUDE.md § Safety Rules) — pas seulement au premier message
- Scope boundaries explicites dans le prompt : « Si le patient demande X → phrase Y → redirection cabinet »
- `temperature=0.0` → minimise la créativité
- Test adversarial : 10 scénarios d'injection (conseil médical, estimation mutuelle, pression commerciale)
- Catégorie de traitement jamais dans le ChatContext LLM (Option B HDS)

#### AP-6 — Annonce d'enregistrement manquante ou coupée

**Piège** : la loi française impose d'informer le patient que l'appel est enregistré. Si l'annonce est interruptible, le patient coupe avant d'entendre la mention légale. « This sounds basic, but it's frequently missed. » (Brilo AI). Le Playbook ajoute : « In two-party consent states, the agent explicitly asked for permission. » (Vapi Ch. 23)

**Mitigation DentalOS** :
- Étape 1 : `allow_interruptions=False` → l'annonce (cabinet + enregistrement + motif) est intégrale
- Phrase d'enregistrement auditée et fixe dans le prompt, pas improvisée par le LLM
- Test : vérifier que la mention « cet appel est enregistré » est toujours prononcée intégralement

#### AP-7 — Boucle infinie sur l'identité (doom-loop)

**Piège** : le patient donne un nom légèrement différent (nom de jeune fille vs marié, orthographe variante), le backend retourne `no-match`, et l'agent repose la même question avec une reformulation mineure. Le patient répète 6, 7, 8 fois avant de raccrocher. « Elena's original agent had no retry limit. She found call recordings in which callers repeated the same information 6, 7, or 8 times before hanging up. Adding a three-attempt ceiling with graceful escalation cut abandonment rates in half. » (Vapi Ch. 13)

**Mitigation DentalOS** :
- Maximum **2 tentatives** identité (plus strict que le Playbook qui dit 3 — choix conservateur santé)
- Tentative 1 : question standard
- Tentative 2 : reformulation + contrainte format (« Pourriez-vous me donner votre date de naissance au format jour mois année ? »)
- Après 2 échecs : « Je n'arrive pas à confirmer votre identité. Le cabinet va vous rappeler directement. » + raccrochage poli
- `run_ctx.disallow_interruptions()` pendant le tool call `verify_patient_identity`

#### AP-8 — Agent sans personnalité (ton robotique)

**Piège** : l'agent est techniquement correct mais froid et oubliable. Pas d'acknowledgement (« d'accord », « très bien »), pas de chaleur, rythme constant et mécanique. « The agent had no personality. It was correct but forgettable. Drivers had no reason to trust it, like it, or stay on the line. » (Vapi Ch. 11). Le passage de 14% à 22% de conversion après correction de persona — même flow, même logique, juste un ton différent.

**Mitigation DentalOS** :
- Voix Cartesia « Calm French Woman » — profil chaleur modérée, assertivité basse
- Prompt : structure Acknowledge → Act → Advance avec exemples FR concrets
- Acknowledgements : « D'accord. », « Très bien. », « Je comprends. » — au moins 2-3 par appel
- Persona Vapi 4 dimensions : warmth modérée, formality professionnelle, pace posé, assertivité basse
- Test : évaluation « naturalness » sur 5 dimensions Vapi (scoring humain)

#### AP-9 — TTS qui lit du markdown/JSON/emoji

**Piège** : le LLM génère `**très bien**` ou `- disponibilités :` et le TTS prononce « étoile étoile très bien étoile étoile » ou « tiret disponibilités deux-points ». « Respond in plain text only. Never use JSON, markdown, lists, tables, code, emojis, or other complex formatting. » (LiveKit prompting guide)

**Mitigation DentalOS** :
- `tts_text_transforms=["filter_emoji", "filter_markdown", dental_replacements]`
- Prompt LLM : « Réponds en texte brut uniquement. Pas de markdown, pas de listes, pas de JSON, pas d'emoji. Épelle les chiffres en lettres. »
- Test : injecter des réponses LLM avec markdown et vérifier que le TTS ne les prononce pas

#### AP-10 — Silence pendant le tool call (dead air outil)

**Piège** : le `verify_patient_identity` prend 500-800ms. Pendant ce temps, le patient n'entend rien et pense que l'appel a planté. « Silence longer than about 800 milliseconds felt broken. » (Vapi Ch. 15). Le bon filler est « Un instant… » suivi d'un silence honnête, pas d'un monologue de remplissage.

**Mitigation DentalOS** :
- Filler bref avant le tool call : « Un instant, je vérifie. » (via `session.say` ou prompt instruction)
- Durée filler < 3s — « 'Let me check,' followed by a pause, was honest and professional. » (Vapi Ch. 15)
- En prod : envisager un thinking sound (LiveKit external-data) pendant les tool calls > 500ms

#### AP-11 — Perte de contexte entre les 6 étapes

**Piège** : l'agent collecte la réponse mutuelle (étape 3), puis l'intention (étape 4), puis les disponibilités (étape 5), mais le CallOutcome final est incomplet — une donnée a été « oubliée » par le LLM entre les tours. « Each turn was handled correctly in isolation; the failure is entirely in the connective tissue between them. » (Webfuse)

**Mitigation DentalOS** :
- Prompt : « Maintiens un état interne explicite : identity_verified, mutuelle_status, intention, disponibilites, escalade_motif. »
- Vapi Playbook : « Manage conversation state explicitly. Track identity status, discovered intent, collected slots, last tool call, confirmed details, and transfer reason. Don't rely on the model to remember. » (Ch. 12)
- Étape 6 récap : relire tous les champs collectés pour confirmation implicite
- Test end-to-end : vérifier que le CallOutcome JSON contient tous les champs après 20 conversations

#### AP-12 — Confirmation batch en fin d'appel au lieu de progressive

**Piège** : l'agent collecte tout silencieusement, puis récite un bloc de 5 informations en étape 6. Le patient ne se souvient plus de ce qu'il a dit et ne peut pas vérifier. « Confirm each piece of critical information as you collect it. Don't wait until the end to read it all back at once. » (Vapi Ch. 9)

**Mitigation DentalOS** :
- Confirmation progressive : chaque réponse patient est accusée réception immédiatement
  - Étape 3 : « D'accord, vous n'avez pas encore eu de retour de votre mutuelle. »
  - Étape 4 : « Très bien, vous souhaitez procéder au traitement. »
  - Étape 5 : « J'ai noté : mardi matin ou jeudi après-midi. »
- Étape 6 : récap synthétique (pas une relecture verbatim de tout)
- Slot high-stakes (DOB) : confirmé par le backend (`verify_patient_identity`), pas relu à voix haute (RGPD)

---

### 6.2 Checklist démo qualité — 15 points

Checklist à valider avant chaque prise vidéo ou démo live. Chaque item a un critère pass/fail mesurable.

#### Audio & Latence

| # | Check | Critère pass | Critère fail |
|---|-------|-------------|-------------|
| 1 | **Premier mot agent < 600ms** après le premier audio patient | Mesuré via observability LiveKit (`end_of_utterance_delay` + LLM TTFT + TTS TTFB). Total < 600ms. | Dead air > 1s au démarrage. Le patient dit « Allo ? » et attend. |
| 2 | **Latence mid-flow < 1,5s** P90 | Aucune réponse agent ne dépasse 1,5s end-to-end sur 10 runs consécutifs. | Le patient parle par-dessus l'agent ou dit « Allo ? Vous êtes là ? » |
| 3 | **Voix naturelle dès la 1ère phrase** | La voix Cartesia « Calm French Woman » sonne naturelle, pas robotique. Le débit est posé. Les dates et noms propres sont correctement prononcés. | Voix métallique, débit trop rapide, prononciation anglicisée des mots FR. |
| 4 | **Pas de dead air pendant le tool call** | Un filler (« Un instant, je vérifie. ») comble le silence pendant `verify_patient_identity`. | Silence > 800ms sans explication pendant le tool call. |

#### Turn-taking & Interruptions

| # | Check | Critère pass | Critère fail |
|---|-------|-------------|-------------|
| 5 | **Agent ne coupe pas pendant la DOB** | Le patient dit « le quatorze… [1,2s]… mars… [0,8s]… soixante-dix-huit » sans interruption. | L'agent commence à parler après « quatorze ». |
| 6 | **Agent ne bourrine pas après un silence** | Un silence patient de 2-3s (réflexion mutuelle) n'est pas traité comme fin de conversation. L'agent attend jusqu'à `max_delay=4s`. | L'agent relance après 1s de silence avec « Vous êtes toujours là ? » |
| 7 | **Backchannels ignorés** | Le patient dit « mmh », « d'accord », « oui oui » pendant que l'agent parle → l'agent continue sans s'interrompre (adaptive interruption). | L'agent s'arrête après chaque « mmh » et tente de répondre. |
| 8 | **Interruption réelle traitée** | Le patient dit « attendez, je me suis trompé » pendant que l'agent parle → l'agent s'arrête et écoute. | L'agent continue à parler par-dessus le patient. |

#### Conversation & Contenu

| # | Check | Critère pass | Critère fail |
|---|-------|-------------|-------------|
| 9 | **Annonce d'enregistrement intégrale** | La mention « cet appel est enregistré » est prononcée en entier dans la 1ère phrase, non-interruptible. | La mention est coupée, omise, ou le patient interrompt avant de l'entendre. |
| 10 | **Transitions fluides entre 2 questions** | Chaque transition suit le pattern Acknowledge → Act → Advance. Ex : « D'accord. [pause 300ms] Et concernant le traitement, souhaitez-vous procéder ? » | L'agent enchaîne les questions sans accusé réception. Ton interrogatoire. |
| 11 | **Réponses ≤ 2 phrases** | Aucune utterance agent ne dépasse 2 phrases / 15s de parole sur l'ensemble du flow. | L'agent débite un paragraphe explicatif avant de poser sa question. |
| 12 | **Guardrail : refus médical/financier** | Le patient demande « c'est remboursé à combien ? » → l'agent redirige en 1 phrase vers le cabinet. Pas d'estimation, pas de conseil. | L'agent improvise une réponse sur le remboursement ou la nécessité du traitement. |

#### Intégrité données & Clôture

| # | Check | Critère pass | Critère fail |
|---|-------|-------------|-------------|
| 13 | **CallOutcome complet** | Après le flow complet, le CallOutcome JSON contient : `identity_verified`, `mutuelle_status`, `intention`, `disponibilites` (si oui), `escalade_motif` (si applicable). Aucun champ null inattendu. | Un champ manque ou contient une valeur incohérente avec ce que le patient a dit. |
| 14 | **Récap fidèle en clôture** | L'agent récapitule correctement ce qui a été noté. Le récap match le CallOutcome. | Le récap omet un élément ou contredit ce que le patient a dit. |
| 15 | **Sortie gracieuse sur échec identité** | Après 2 tentatives échouées, l'agent propose un rappel cabinet et raccroche poliment. Pas de boucle, pas de silence, pas d'excuse excessive. | L'agent demande une 3ème fois, ou reste silencieux, ou dit « je suis désolé, je n'y arrive pas ». |

---

### 6.3 Synthèse stack final — Récap des décisions sections 1-5

#### Pipeline voix

```
Patient (browser 16kHz) → [Silero VAD] → [Deepgram Nova-3 FR] → [MultilingualModel EOU]
                                                                         ↓
                                                              [GPT-4.1-mini @ t=0.0]
                                                                         ↓
                                                              [Cartesia Sonic-3 FR]
                                                                         ↓
                                                              Patient (audio output)
```

#### Composants — Tableau récap

| Composant | Choix démo | Via | Challenger / Fallback |
|-----------|-----------|-----|----------------------|
| **STT** | Deepgram Nova-3 (`language="fr"`) | LiveKit Inference | AssemblyAI U3-Pro (moins cher) |
| **TTS** | Cartesia Sonic-3, voix « Calm French Woman » (`a8a1eb38…`) | LiveKit Inference | ElevenLabs Flash v2.5, voix « Lise » (`sEk5ft…`) |
| **LLM** | GPT-4.1-mini (`temperature=0.0`) | LiveKit Inference | GPT-4o-mini (plus rapide), Mistral Large 3 (meilleur FR, prod) |
| **Turn Detection** | MultilingualModel (Qwen2.5-0.5B) | Plugin `turn-detector` | VAD seul (fallback auto si erreur adaptive) |
| **VAD** | Silero (`activation=0.5, min_silence=0.6s`) | Plugin `silero` | — |
| **Noise Cancellation** | None (démo browser) | — | BVCTelephony (prod SIP) |
| **Plateforme** | LiveKit Cloud | `wss://dalia-health-*.livekit.cloud` | Self-hosted LiveKit sur OVH HDS (prod Option B) |

#### Paramètres clés

| Paramètre | Valeur | Justification courte |
|-----------|--------|---------------------|
| `endpointing.mode` | `dynamic` | Adapte au rythme du patient |
| `endpointing.min_delay` | 0.7s | Healthcare/formal (Vapi 0.6-0.8s) |
| `endpointing.max_delay` | 4.0s | Pauses de réflexion longues |
| `interruption.mode` | `adaptive` | Filtre backchannels FR |
| `interruption.min_duration` | 0.6s | Évite fausses interruptions fillers FR |
| `false_interruption_timeout` | 2.5s | Laisse le temps de confirmer |
| `resume_false_interruption` | True | L'agent reprend après backchannel |
| `preemptive_generation` | True (LLM only) | Compense TTFT GPT-4.1-mini |
| `preemptive_tts` | False | Précision > vitesse |
| `aec_warmup_duration` | 3.0s | Défaut, empêche l'écho d'interrompre |
| `user_away_timeout` | 30.0s | Patient peut chercher un document |
| `tts_text_transforms` | filter_emoji + filter_markdown + replace | Prononciation propre |
| `temperature` | 0.0 | Flow rigide, pas de créativité |

#### Architecture HDS (rappel)

**Option B — Dissociation architecturale** (validée `decisions.md`) :
- **Sur HDS** (OVH ~168€/mois) : LiveKit Server, SIP, Agent Worker, Backend Identity
- **APIs externes EU** (pas de PHI) : Deepgram STT, GPT-4.1-mini, Cartesia TTS
- Catégorie de traitement : audio pré-synthétisé (ne passe jamais par le LLM)
- Identité patient : vérifiée côté backend, seul un flag `match: bool` entre dans le ChatContext

#### Budget pilote estimé

| Composant | Coût/mois (5000 appels × 4 min avg) |
|-----------|--------------------------------------|
| Deepgram STT | ~$150 |
| Cartesia TTS | ~$375 |
| GPT-4.1-mini LLM | ~$20 |
| LiveKit Cloud | ~$50-100 (estimé) |
| OVH HDS (prod) | ~$168 |
| **Total démo** | **~$595-645/mois** |
| **Total prod** | **~$760-860/mois** |

#### Prochaines étapes post-review

1. **Bench test** : Deepgram vs AssemblyAI, GPT-4.1-mini vs 4o-mini, Cartesia TTFB FR réel
2. **Prompt engineering** : rédiger le system prompt 5 sections (identité, style, tâche, guardrails, tools) en FR
3. **Code démo** : assembler `demo/agent.py` avec la config section 5.3
4. **Tests flow** : 20 happy-path + 10 edge-case + 5 adversarial (cf. Vapi test pyramid)
5. **Validation juridique** : consultation avocat RGPD/HDS pour Option B (budget ~2-5k€)
