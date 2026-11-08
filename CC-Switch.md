# CC-Switch: провайдеры для DeepSeek Harness

Конфиги провайдеров CC Switch для DeepSeek Harness (`apiKeyEnv: CC_SWITCH_DSH_CC_SWITCH_VLLM`),
по одному на vLLM-скрипт. Раньше они лежали отдельными `.json` рядом со скриптами в `vllm/`.

Общее для всех: сервер на `http://127.0.0.1:1234/v1`, ID модели `Qwen3.8-27B-NVFP4` (первое имя в
`--served-model-name`), `contextWindow 229376` + `maxTokens 32768` = 262144 = `--max-model-len`.
Почему сумма не должна превышать окно, см. раздел «Claude Code как клиент этих серверов» в `CLAUDE.md`.

## vllm/gittensor-qwen38-27-nvfp4-vllm-rtx5060-no-reasoning-test2.bat

Рассуждения выключены: `reasoning: false`, `reasoningEfforts: false`.

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

## vllm/gittensor-qwen38-27-nvfp4-vllm-rtx5060-reasoning-test2.bat

Рассуждения включены, уровень выбирает harness: `reasoning: true`,
`reasoningEfforts: ["low","medium","high"]`. Как шаблон нормализует уровень, см. `BAT_NOTES.md`.

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
        "high"
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
