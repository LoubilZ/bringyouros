# SDK livekit-agents 1.5.7 — Reality Check vs demo-stack.md § 5.3

Date : 2026-05-02
Méthode : RAG `search_livekit_kb` (docs + forum) + docs.livekit.io + GitHub source

## Tableau de correspondance

| Param § 5.3 | Nom réel SDK 1.5.7 | Classe | Statut | Source |
|---|---|---|---|---|
| `inference.LLM(temperature=0.0)` | `inference.LLM(extra_kwargs={"temperature": 0.0})` | `inference.LLM` | **RENOMMÉ** — `temperature` n'est pas un kwarg direct, passe par `extra_kwargs` | [docs.livekit.io/reference/agents/inference-llm-parameters/](https://docs.livekit.io/reference/agents/inference-llm-parameters/) |
| `AudioInputOptions(audio_sample_rate=24000)` | `AudioInputOptions(sample_rate=24000)` | `room_io.AudioInputOptions` | **RENOMMÉ** — la classe unifiée utilise `sample_rate`, pas `audio_sample_rate` | [GitHub room_io/types.py](https://github.com/livekit/agents/blob/main/livekit-agents/livekit/agents/voice/room_io/types.py) |
| `AudioInputOptions(audio_num_channels=1)` | `AudioInputOptions(num_channels=1)` | `room_io.AudioInputOptions` | **RENOMMÉ** — `num_channels`, pas `audio_num_channels` | idem |
| `AudioOutputOptions(audio_sample_rate=24000)` | `AudioOutputOptions(sample_rate=24000)` | `room_io.AudioOutputOptions` | **RENOMMÉ** | idem |
| `AudioOutputOptions(audio_num_channels=1)` | `AudioOutputOptions(num_channels=1)` | `room_io.AudioOutputOptions` | **RENOMMÉ** | idem |
| `TurnHandlingOptions(endpointing={...})` | idem | `TurnHandlingOptions` (TypedDict) | **OK** — dict syntax valide | [docs.livekit.io/reference/agents/turn-handling-options/](https://docs.livekit.io/reference/agents/turn-handling-options/) |
| `TurnHandlingOptions(interruption={...})` | idem | `TurnHandlingOptions` (TypedDict) | **OK** — dict syntax valide | idem |
| `TurnHandlingOptions(preemptive_generation={...})` | idem | `TurnHandlingOptions` (TypedDict) | **OK** — dict syntax valide | idem |
| `inference.STT(model=, language=)` | idem | `inference.STT` | **OK** | [docs.livekit.io/agents/models/stt/](https://docs.livekit.io/agents/models/stt/) |
| `inference.TTS(model, voice=, language=)` | idem | `inference.TTS` | **OK** | [docs.livekit.io/agents/models/tts/](https://docs.livekit.io/agents/models/tts/) |
| `silero.VAD.load(activation_threshold, min_silence_duration, min_speech_duration, prefix_padding_duration, sample_rate)` | idem | `silero.VAD` | **OK** — tous les 5 params confirmés | [docs.livekit.io/agents/logic/turns/vad/](https://docs.livekit.io/agents/logic/turns/vad/) |
| `MultilingualModel()` | idem, no-arg | `livekit.plugins.turn_detector.multilingual` | **OK** | [docs.livekit.io/agents/logic/turns/turn-detector/](https://docs.livekit.io/agents/logic/turns/turn-detector/) |
| `AgentSession(aec_warmup_duration=3.0)` | idem, `float \| None`, default `3.0` | `AgentSession` | **OK** | [Python reference](https://docs.livekit.io/reference/python/livekit/agents/) |
| `AgentSession(user_away_timeout=30.0)` | idem, `float \| None`, default `15.0` | `AgentSession` | **OK** | idem |
| `AgentSession(max_tool_steps=3)` | idem, `int`, default `3` | `AgentSession` | **OK** | idem |
| `AgentSession(tts_text_transforms=[...])` | idem | `AgentSession` | **OK** | idem |
| `AgentSession(min_consecutive_speech_delay=0.0)` | idem, `float`, default `0.0` | `AgentSession` | **OK** | idem |
| `AgentSession(ivr_detection=False)` | idem, `bool`, default `False` | `AgentSession` | **OK** | idem |
| `text_transforms.replace({...}, case_sensitive=False)` | idem | `livekit.agents.text_transforms` | **OK** | [docs.livekit.io/agents/multimodality/text/](https://docs.livekit.io/agents/multimodality/text/) |
| `generate_reply(allow_interruptions=False)` | idem | `AgentSession.generate_reply` | **OK** | [Python reference](https://docs.livekit.io/reference/python/livekit/agents/) |
| `@server.rtc_session()` + `cli.run_app(server)` | idem | `AgentServer` | **OK** | [Reference recipes](https://docs.livekit.io/reference/recipes/answer_call) |

## Signatures complètes vérifiées

### EndpointingOptions (TypedDict, total=False)

```python
mode: Literal["fixed", "dynamic"]  # default "fixed"
min_delay: float                   # default 0.5
max_delay: float                   # default 3.0
alpha: float                       # default 0.9
```

### InterruptionOptions (TypedDict, total=False)

```python
enabled: bool                              # default True
mode: Literal["adaptive", "vad"]           # default auto-detect
discard_audio_if_uninterruptible: bool     # default True
min_duration: float                        # default 0.5
min_words: int                             # default 0
resume_false_interruption: bool            # default True
false_interruption_timeout: float | None   # default 2.0
backchannel_boundary: float | tuple[float, float] | None  # default (1.0, 3.5)
```

### PreemptiveGenerationOptions (TypedDict, total=False)

```python
enabled: bool              # default True
preemptive_tts: bool       # default False
max_speech_duration: float # default 10.0
max_retries: int           # default 3
```

### room_io.AudioInputOptions (dataclass)

```python
sample_rate: int = 24000
num_channels: int = 1
frame_size_ms: int = 50
noise_cancellation: ... | None = None
auto_gain_control: bool = True
pre_connect_audio: bool = True
pre_connect_audio_timeout: float = 3.0
```

### room_io.AudioOutputOptions (dataclass)

```python
sample_rate: int = 24000
num_channels: int = 1
track_publish_options: rtc.TrackPublishOptions = ...
track_name: NotGivenOr[str] = NOT_GIVEN
```

### inference.LLM

```python
def __init__(
    self,
    model: LLMModels | str,
    *,
    provider: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
    api_secret: str | None = None,
    inference_class: InferenceClass | None = None,
    extra_kwargs: ChatCompletionOptions | dict[str, Any] | None = None,
)
```

`temperature`, `max_completion_tokens`, etc. passent dans `extra_kwargs`.

## Note legacy

`RoomInputOptions` (ancienne classe, encore exportée) utilise les noms longs `audio_sample_rate`, `audio_num_channels`. La classe unifiée `AudioInputOptions` (dans `room_io.RoomOptions`) utilise les noms courts `sample_rate`, `num_channels`. Ne pas confondre.
