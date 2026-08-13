# K-EXAONE 2.0 — API · 추론 · `preserve_thinking`

**정본:** [Hugging Face model card](https://huggingface.co/LGAI-EXAONE/K-EXAONE-2.0-750B-A37B) · [Technical report (arXiv:2608.04505)](https://arxiv.org/abs/2608.04505)

K-EXAONE **1.0**과 **2.0**의 OpenAI 호환 API 차이, 특히 **`preserve_thinking`** 을 언제 켜고 끄는지 정리합니다. Cookbook 레이어별 적용 위치도 함께 적습니다.

---

## 1. 1.0 vs 2.0 (한눈에)

| 항목 | K-EXAONE 1.0 | K-EXAONE 2.0 |
|------|----------------|--------------|
| 예시 HF id | `LGAI-EXAONE/K-EXAONE-236B-A23B` | `LGAI-EXAONE/K-EXAONE-2.0-750B-A37B` |
| 배포 id 예 | 레거시 Friendli id | `k-exaone_v2` 등 |
| Reasoning API | `enable_thinking` | `enable_thinking` + **`preserve_thinking`** |
| Agentic 멀티턴 | reasoning이 턴 경계에서 사라지기 쉬움 | **`preserve_thinking=True`** 로 reasoning trace 유지 |

---

## 2. `chat_template_kwargs` (OpenAI 호환 `extra_body`)

```python
from openai import OpenAI

client = OpenAI(base_url="https://your-host/v1", api_key="...")

response = client.chat.completions.create(
    model="k-exaone_v2",
    messages=[{"role": "user", "content": "..."}],
    max_tokens=32768,
    temperature=1.0,
    top_p=0.95,
    extra_body={
        "chat_template_kwargs": {
            "enable_thinking": True,
            "preserve_thinking": True,  # agentic — 효과는 2.0+ 에서만
        }
    },
)
```

### 2.1 `enable_thinking` (1.0 · 2.0 공통)

| 값 | 동작 | 쓰는 곳 |
|----|------|---------|
| `True` | reasoning 모드 — `reasoning_content`와 `content` 분리 | 다단계 추론, **도구 루프 enrich** |
| `False` | non-reasoning, 저지연 | **잡담·단발 Q&A**, user simulator, JSON finalize |

Cookbook `exaone.llm.ExaoneAPIClient`는 `ExaoneGenerateOptions.enable_thinking`으로 이 값을 설정합니다.

### 2.2 `preserve_thinking` (효과는 K-EXAONE 2.0+)

| 값 | 동작 (2.0+) | 쓰는 곳 |
|----|-------------|---------|
| `False` (**API 기본**) | 턴이 끝나면 reasoning block을 컨텍스트에서 **제거** → 다음 턴 재추론 | 단발 Q&A, chitchat, latency 우선 |
| `True` | 이전 턴의 `reasoning_content`를 **유지** | **ToolAgent**, τ-bench, Harbor agentic, deep research |

**실무 규칙 (Cookbook 권장):**

| 워크플로 | `enable_thinking` | `preserve_thinking` |
|----------|-------------------|---------------------|
| 잡담 · 단발 Q&A | `False` | `False` |
| 단발 reasoning (한 턴) | `True` | `False` |
| **Agentic** (도구 루프 · 멀티턴) | `True` | **`True` (필수)** |

Agentic에서 `preserve_thinking=False`이면 턴마다 reasoning이 리셋되어 이전 결론을 다시 유도해야 하므로, **품질·토큰 모두 불리**합니다.

### 2.3 K-EXAONE 1.0 payload에 `preserve_thinking`을 넣어도 되나?

**네.** Cookbook은 모델 id를 추측하지 않고, **명시한 값을 그대로** `chat_template_kwargs`에 실습니다.

- **K-EXAONE 1.0:** 서버/템플릿이 알 수 없는 kwargs를 **무시**하는 경우가 많아, v1처럼 동작하고 preserve **효과는 없습니다**.
- **K-EXAONE 2.0+:** 위 표대로 reasoning trace 유지에 **실제로 적용**됩니다.
- **일부 게이트웨이:** 스키마 검증이 엄하면 미지원 키로 `400`이 날 수 있습니다 — 배포 문서를 확인하세요.

즉, **payload에 넣는 것**과 **런타임에 효과가 있는 것**을 구분합니다. eval glue(`eval/exaone_api_kwargs.py`)는 전자만 담당하고, 후자는 배포된 모델 세대가 결정합니다.

---

## 3. Cookbook 레이어별 적용

| 레이어 | `enable_thinking` | `preserve_thinking` |
|--------|-------------------|---------------------|
| **`exaone/`** (`ExaoneAPIClient`, `ToolAgent`) | `ExaoneGenerateOptions` · ThinkingRouter | **직접 필드 없음** — eval glue 또는 `extra_body` |
| **`recipes/`** | 노트북에서 `enable_thinking=False`로 chitchat/JSON 데모 | Track 02+ agentic은 env·glue로 `True` |
| **`eval/`** | `EXAONE_ENABLE_THINKING` (기본 on) | `EXAONE_PRESERVE_THINKING` (기본 on) — `eval/exaone_api_kwargs.py` |

```python
# eval runner / LiteLLM / Harbor subprocess 예
from eval.exaone_api_kwargs import build_extra_body

# agentic (기본 env): thinking + preserve 모두 True
extra_body = build_extra_body()

# chitchat / 단발 QA
extra_body = build_extra_body(enable_thinking=False, preserve_thinking=False)
```

---

## 4. 환경 변수 (`.env`)

```bash
EXAONE_MODEL=k-exaone_v2
EXAONE_ENABLE_THINKING=1       # agentic eval 기본 on
EXAONE_PRESERVE_THINKING=1     # agentic 기본 on — 효과는 2.0+ (1.0은 무시)
EXAONE_EVAL_AGENT_TEMPERATURE=0.7
```

단발 번역·잡담 노트북(Track 01·09)은 코드에서 `enable_thinking=False`를 **명시**하는 패턴을 따릅니다.

---

## 5. 샘플링 (HF 가이드)

| 파라미터 | 권장 |
|----------|------|
| `temperature` | **1.0** (greedy 금지) |
| `top_p` | **0.95** |
| `max_tokens` | 배포 상한까지 (2.0 output 최대 32k) |

자세한 eval·Harbor 설정은 [`eval/README.md`](../eval/README.md), 에이전트 흐름은 [`exaone/agents/README.md`](../exaone/agents/README.md)를 참고하세요.
