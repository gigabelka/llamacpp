# CC-Switch: провайдеры для DeepSeek Harness

Конфиги провайдеров [CC Switch](https://github.com/farion1231/cc-switch) для DeepSeek Harness (`apiKeyEnv: CC_SWITCH_DSH_CC_SWITCH_VLLM`),
по одному на vLLM-скрипт. Раньше они лежали отдельными `.json` рядом со скриптами в `vllm/`.

Общее для всех: сервер на `http://127.0.0.1:1234/v1`, ID модели `Qwen3.8-27B-NVFP4` (первое имя в
`--served-model-name`), `contextWindow 229376` + `maxTokens 32768` = 262144 = `--max-model-len`.
Почему сумма не должна превышать окно, см. раздел «Claude Code как клиент этих серверов» в `CLAUDE.md`.

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
  "apiKeyEnv": "CC_SWITCH_DSH_CC_SWITCH_VLLM",
  "models": {
    "Qwen3.8-27B-NVFP4": {
      "name": "Qwen3.8-27B-NVFP4 (thinking)",
      "input": [
        "text"
      ],
      "id": "Qwen3.8-27B-NVFP4",
      "maxTokens": 32768,
      "reasoningEfforts": [
        "low",
        "medium",
        "xhigh"
      ],
      "contextWindow": 229376,
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
