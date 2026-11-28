# CC-Switch: провайдеры для DeepSeek Harness

Конфиги провайдеров [CC Switch](https://github.com/farion1231/cc-switch) для DeepSeek Harness (`apiKeyEnv: CC_SWITCH_DSH_CC_SWITCH_VLLM`),
по одному на vLLM-скрипт. Раньше они лежали отдельными `.json` рядом со скриптами в `vllm/`.

Общее для всех: сервер на `http://127.0.0.1:1234/v1`, ID модели `Qwen3.8-27B-NVFP4` (первое имя в
`--served-model-name`), `contextWindow 229376` + `maxTokens 32768` = 262144 = `--max-model-len`.
Почему сумма не должна превышать окно, см. раздел «Claude Code как клиент этих серверов» в `CLAUDE.md`.
Исключение — раздел `strata/run-iq3_s-coding-reason.bat`: там Strata на порту 8080 и другое окно.

## strata/run-iq3_s-coding-reason.bat

Strata Terminal, не vLLM: `http://127.0.0.1:8080/v1`, ID модели `qwen3.8-flash-next-iq3_s`,
окно 204800. Сумма `contextWindow 172032` + `maxTokens 32768` = 204800 — то же правило, что и выше.
Локальный доступ ключ не требует, в `apiKey` можно положить любую строку.

Рассуждения включены: конфиг задаёт уровень по умолчанию `high` (= `xhigh` шаблона) для запросов,
где harness уровень не прислал; запрос всегда побеждает. Уровни Strata:
`off`/`none`/`minimal` → размышления выключены, `low` → краткое, `medium` → без преамбулы,
`high`/`xhigh`/`max` → xhigh. Поэтому в `reasoningEfforts` у `off` стоит строка `"off"`, а **не**
`null`: `null` означает «поле не отправлено», и тогда сработает конфиг-уровень `high`, то есть
размышления останутся включёнными. Набор `off/low/medium/high` покрывает всё; `xhigh` можно
добавить отдельным пунктом — он маппится в тот же `xhigh`, что и `high`.

```json
{
  "api": "openai-completions",
  "baseURL": "http://127.0.0.1:8080/v1",
  "models": {
    "qwen3.8-flash-next-iq3_s": {
      "name": "Qwen3.8-Flash-Next IQ3_S (thinking)",
      "input": [
        "text"
      ],
      "contextWindow": 172032,
      "id": "qwen3.8-flash-next-iq3_s",
      "maxTokens": 32768,
      "reasoningEfforts": {
        "off": "off",
        "low": "low",
        "medium": "medium",
        "high": "high"
      },
      "limit": {
        "context": 172032,
        "output": 32768
      },
      "reasoning": true,
      "modalities": {
        "input": [
          "text"
        ],
        "output": [
          "text"
        ]
      }
    }
  },
  "apiKeyEnv": "CC_SWITCH_DSH_CC_SWITCH_VLLM",
  "displayName": "Qwen3.8-Flash-Next IQ3_S Strata (thinking)",
  "name": "Qwen3.8-Flash-Next IQ3_S Strata (thinking)",
  "options": {
    "baseURL": "http://127.0.0.1:8080/v1",
    "apiKey": "strata",
    "headers": {}
  }
}
```

Если harness говорит по Anthropic (`/v1/messages`), уровень приходит как `output_config.effort`,
а `thinking: {"type": "disabled"}` выключает размышления. Родной путь Strata для Claude Code —
`strata connect claude`, он пишет те же адрес/модель и `CLAUDE_CODE_MAX_CONTEXT_TOKENS` /
`CLAUDE_CODE_MAX_OUTPUT_TOKENS`; провайдер выше нужен, если хочется вести всё через CC Switch.
Подробности и замеры — `strata/README.md` §9.

## strata/run-nvfp4-coding-noreason.bat

Strata Terminal, вторая модель: `http://127.0.0.1:8080/v1`, ID модели
`qwen3.8-flash-next-nvfp4-nvfp4`, окно 262144. Сумма `contextWindow 229376` + `maxTokens 32768`
= 262144 — то же правило, что и выше (запрос с `prompt + max_tokens` больше окна Strata
отбивает). Рассуждения выключены патчем (`strata/patches/apply-no-reasoning.ps1`):
`reasoning: false`, `reasoningEfforts: false`.

Модель отвечает заметно медленнее IQ3_S (~20–26 t/s decode против ~114): эксперты не влезают в RAM
целиком, часть читается с диска (§10 в `strata/README.md`).

```json
{
  "api": "openai-completions",
  "apiKeyEnv": "CC_SWITCH_DSH_CC_SWITCH_VLLM",
  "models": {
    "qwen3.8-flash-next-nvfp4-nvfp4": {
      "name": "Qwen3.8-Flash-Next NVFP4 (no-thinking)",
      "input": [
        "text"
      ],
      "id": "qwen3.8-flash-next-nvfp4-nvfp4",
      "maxTokens": 32768,
      "reasoningEfforts": false,
      "contextWindow": 229376,
      "limit": {
        "context": 229376,
        "output": 32768
      },
      "reasoning": false,
      "modalities": {
        "input": [
          "text"
        ],
        "output": [
          "text"
        ]
      }
    }
  },
  "displayName": "Qwen3.8-Flash-Next NVFP4 Strata (no-thinking)",
  "baseURL": "http://127.0.0.1:8080/v1",
  "name": "Qwen3.8-Flash-Next NVFP4 Strata (no-thinking)",
  "options": {
    "baseURL": "http://127.0.0.1:8080/v1",
    "apiKey": "strata",
    "headers": {}
  }
}
```

## strata/run-nvfp4-coding-reason.bat

Тот же сервер и модель, рассуждения включены: конфиг задаёт уровень по умолчанию `high`
(= `xhigh` шаблона), запрос всегда побеждает; уровни и ловушка с `off`/`null` — как в разделе
`strata/run-iq3_s-coding-reason.bat` выше. Окно 262144: `contextWindow 229376` + `maxTokens 32768`.

```json
{
  "api": "openai-completions",
  "baseURL": "http://127.0.0.1:8080/v1",
  "models": {
    "qwen3.8-flash-next-nvfp4-nvfp4": {
      "name": "Qwen3.8-Flash-Next NVFP4 (thinking)",
      "input": [
        "text"
      ],
      "contextWindow": 229376,
      "id": "qwen3.8-flash-next-nvfp4-nvfp4",
      "maxTokens": 32768,
      "reasoningEfforts": {
        "off": "off",
        "low": "low",
        "medium": "medium",
        "high": "high"
      },
      "limit": {
        "context": 229376,
        "output": 32768
      },
      "reasoning": true,
      "modalities": {
        "input": [
          "text"
        ],
        "output": [
          "text"
        ]
      }
    }
  },
  "apiKeyEnv": "CC_SWITCH_DSH_CC_SWITCH_VLLM",
  "displayName": "Qwen3.8-Flash-Next NVFP4 Strata (thinking)",
  "name": "Qwen3.8-Flash-Next NVFP4 Strata (thinking)",
  "options": {
    "baseURL": "http://127.0.0.1:8080/v1",
    "apiKey": "strata",
    "headers": {}
  }
}
```

## gittensor/gittensor-qwen38-27-nvfp4-vllm-rtx5060-mtp-no-reasoning.bat

Рассуждения выключены (`--default-chat-template-kwargs {"enable_thinking":false}`):
`reasoning: false`, `reasoningEfforts: false`.

```json
{
  "api": "openai-completions",
  "apiKeyEnv": "CC_SWITCH_DSH_CC_SWITCH_VLLM",
  "models": {
    "Qwen3.8-27B-NVFP4": {
      "name": "Qwen3.8-27B-NVFP4 (no-thinking)",
      "input": [
        "text"
      ],
      "id": "Qwen3.8-27B-NVFP4",
      "maxTokens": 32768,
      "reasoningEfforts": false,
      "contextWindow": 229376,
      "limit": {
        "context": 229376,
        "output": 32768
      },
      "reasoning": false,
      "modalities": {
        "input": [
          "text"
        ],
        "output": [
          "text"
        ]
      }
    }
  },
  "displayName": "Qwen3.8-27B-NVFP4 Llamacpp",
  "baseURL": "http://127.0.0.1:1234/v1",
  "name": "Qwen3.8-27B-NVFP4 Llamacpp",
  "options": {
    "baseURL": "http://127.0.0.1:1234/v1",
    "apiKey": "lamacpp",
    "headers": {}
  }
}
```

## gittensor/gittensor-qwen38-27-nvfp4-vllm-rtx5060-mtp-reasoning.bat

Рассуждения включены (`--default-chat-template-kwargs {"enable_thinking":true,"preserve_thinking":true}`),
уровень выбирает harness: `reasoning: true`, `reasoningEfforts: ["low","medium","high"]`.
Шаблон `gittensor/chat_template-gittensor.jinja` нормализует `reasoning_effort` запроса:
`low`/`minimal` → краткое рассуждение, `medium` → без преамбулы, `high`/`max`/неизвестное/отсутствует → `xhigh`.
`none` рассуждения **не** выключает (становится `xhigh`); выключает только `chat_template_kwargs
{"enable_thinking": false}` в запросе. Подробнее — в `BAT_NOTES.md`.

```json
{
  "api": "openai-completions",
  "baseURL": "http://127.0.0.1:1234/v1",
  "models": {
    "Qwen3.8-27B-NVFP4": {
      "name": "Qwen3.8-27B-NVFP4 (thinking)",
      "input": [
        "text"
      ],
      "contextWindow": 229376,
      "id": "Qwen3.8-27B-NVFP4",
      "maxTokens": 32768,
      "reasoningEfforts": {
        "off": null,
        "low": "low",
        "medium": "medium",
        "xhigh": "xhigh"
      },
      "limit": {
        "context": 229376,
        "output": 32768
      },
      "reasoning": true,
      "modalities": {
        "input": [
          "text"
        ],
        "output": [
          "text"
        ]
      }
    }
  },
  "apiKeyEnv": "CC_SWITCH_DSH_CC_SWITCH_VLLM",
  "displayName": "Qwen3.8-27B-NVFP4 Llamacpp (thinking)",
  "name": "Qwen3.8-27B-NVFP4 Llamacpp (thinking)",
  "options": {
    "baseURL": "http://127.0.0.1:1234/v1",
    "apiKey": "lamacpp",
    "headers": {}
  }
}
```
