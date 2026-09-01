# llama.cpp — локальный сервер Qwen 3.8 27B (CUDA 12/13, Windows x64)

Набор скриптов запуска **llama.cpp** (`llama-server.exe`) для Windows x64 с
аппаратным ускорением **NVIDIA CUDA** — для инференса `Qwen3.8-27B` (гибридная
Transformer + SSM модель) в режиме локального OpenAI-совместимого API-сервера.

Репозиторий содержит **только конфигурацию**: сами бинарники llama.cpp и файлы
моделей лежат вне репозитория (см. [Внешние зависимости](#-внешние-зависимости)).

---

## 📦 Состав репозитория

```text
├── cuda12/                     # Скрипты запуска против сборки llama.cpp под CUDA 12.x
│   ├── qwen-qwen38-27-4km.bat      # lmstudio-community Q4_K_M
│   ├── unsloth-qwen38-27-3kxl.bat  # unsloth UD-Q3_K_XL
│   ├── unsloth-qwen38-27-4km.bat   # unsloth UD-Q4_K_M
│   ├── unsloth-qwen38-27-5km.bat   # unsloth UD-Q5_K_M
│   └── unsloth-qwen38-27-6km.bat   # unsloth UD-Q6_K_M
├── cuda13/                     # Те же 5 конфигов против сборки под CUDA 13.x
│   └── … (те же имена файлов)
├── qwen38.jinja                # Jinja-шаблон чата (--chat-template-file)
├── CALCULATE.md                # Методика расчёта бюджета VRAM и выгрузки слоёв
└── README.md
```

`cuda12/` и `cuda13/` — **параллельные наборы**: одни и те же конфиги,
отличающиеся лишь тем, на какую сборку `llama-server.exe` они указывают
(`c:\Llamacpp\cuda12\` или `c:\Llamacpp\cuda13\`). Выбирайте набор под
установленный драйвер NVIDIA / версию CUDA-рантайма.

### Отличия между скриптами внутри набора

Общие параметры у всех скриптов одинаковы (`-ngl 99`, `-sm layer`, `-fa on`,
`-kvu`, `-np 1`, `-b 1024`, `-ub 256`, `--spec-type draft-mtp`, `-t 16`,
`--threads-batch 16`, DRY-штрафы, `--chat-template-file .\qwen38.jinja`,
сервер на `127.0.0.1:1234`). Различаются модель и параметры под бюджет VRAM:

| Скрипт | Модель (GGUF) | `-c` | `-ts` | `-ctk`/`-ctv` | `--temp` |
| :----- | :------------ | ---: | :---- | :------------ | :------- |
| `qwen-qwen38-27-4km.bat`      | lmstudio-community `Qwen3.8-27B-Q4_K_M.gguf`   | 262144 | 17,13 | q8_0 / q8_0 | 0.15 |
| `unsloth-qwen38-27-3kxl.bat`  | unsloth `Qwen3.8-27B-UD-Q3_K_XL.gguf`          | 229376 | 17,13 | f16 / f16   | 0.15 |
| `unsloth-qwen38-27-4km.bat`   | unsloth `Qwen3.8-27B-UD-Q4_K_M.gguf`           | 180224 | 17,13 | f16 / f16   | 0.15 |
| `unsloth-qwen38-27-5km.bat`   | unsloth `Qwen3.8-27B-UD-Q5_K_M.gguf`           | 262144 | 16,14 | q8_0 / q4_0 | 0.15 |
| `unsloth-qwen38-27-6km.bat`   | unsloth `Qwen3.8-27B-UD-Q6_K_M.gguf`           | 65336  | 17,13 | f16 / f16   | 0.6  |

Значения `-c`, `-ts`, `-ctk`/`-ctv`, `-ub` подобраны под тестовый стенд
2× RTX 5060 Ti 16 ГБ (см. ниже) так, чтобы **вся модель и весь KV-кэш были в
VRAM, без выгрузки слоёв на CPU**. Расчёт и обоснование — в [CALCULATE.md](CALCULATE.md).

---

## 🚀 Ключевые особенности конфигурации

- **CUDA Acceleration:** cuBLAS / cuBLASLt, наборы `cuda12` и `cuda13` под
  соответствующие рантаймы (`cudart64_12/13.dll`, `cublas64_12/13.dll` и т. д.).
- **Flash Attention (`-fa on`):** ускорение инференса и снижение VRAM на длинном
  контексте; убирает член compute-буфера `∝ n_ctx · n_head`.
- **Квантование KV-кэша (`-ctk`/`-ctv`):** `q8_0` — near-lossless
  (< 0.1 % perplexity), `q4_0` по V — для более тяжёлых квантов весов
  (см. `unsloth-qwen38-27-5km.bat`).
- **Multi-GPU / Tensor Split (`-sm layer -ts a,b`):** распределение слоёв между
  двумя картами. `-ts` намеренно смещён на GPU0 (шина 1), т. к. KV-кэш, кэш
  SSM-состояния и compute-буферы pipeline parallelism оседают на старшей карте —
  равный `-ts` даёт перекос ~3 ГБ.
- **MTP / Speculative Decoding (`--spec-type draft-mtp`):** Multi-Token
  Prediction без отдельной draft-модели (`--spec-draft-n-max 6`,
  `--spec-draft-p-min 0.5`).
- **Гибридная архитектура модели (Transformer + SSM):** полное внимание с
  KV-кэшем — только в каждом 4-м слое; остальные слои держат SSM-состояние
  фиксированного размера, не растущее с длиной контекста. Нативный лимит
  контекста — **262144** токена. Приоритет ужимания при нехватке VRAM (сохраняя
  `-ngl ≥ L+1`): `-c` ↓ → `-ctv` грубее → `-ctk` грубее → `-ub` ↓ → `-ngl` ↓.
- **Кастомный шаблон чата (`qwen38.jinja`):** форматирование сообщений,
  системных инструкций и vision-заглушек.
- **Совместимость с OpenAI API:** `/v1/chat/completions`, `/v1/models`,
  `/v1/completions`, Web UI, `/health` — интеграция с Open WebUI, SillyTavern,
  Continue, cline, Cursor и др.

---

## ⚡ Быстрый старт

1. Установите сборку `llama.cpp` в `c:\Llamacpp\cuda12\` и/или `c:\Llamacpp\cuda13\`
   (`llama-server.exe` + сопутствующие DLL).
2. Скачайте нужную `.gguf`-модель в кэш LM Studio по пути, прописанному в скрипте
   (`c:\Users\<user>\.lmstudio\models\...`), либо поправьте `-m` под свой путь.
3. Запустите нужный скрипт из проводника (двойной клик) или из консоли:

   ```bat
   cuda13\unsloth-qwen38-27-4km.bat
   ```

   Скрипт делает `cd /d "%~dp0.."` (переходит в корень репозитория), поэтому
   `--chat-template-file ".\qwen38.jinja"` резолвится относительно корня.

После запуска сервер доступен по адресу:

- **Web UI & API:** `http://127.0.0.1:1234`
- **OpenAI Endpoint:** `http://127.0.0.1:1234/v1/chat/completions`
- **Health Check:** `http://127.0.0.1:1234/health`

Лог сервера пишется в `c:\Llamacpp\cuda12\llama-server.log` (или `cuda13\`).

---

## 🔗 Внешние зависимости

Прописаны в каждом `.bat` жёстко, **в репозитории их нет**:

| Что | Путь |
| :-- | :--- |
| Бинарники llama.cpp | `c:\Llamacpp\cuda12\`, `c:\Llamacpp\cuda13\` |
| Модели GGUF | `c:\Users\viktor\.lmstudio\models\...` (кэш LM Studio) |
| Лог сервера | `c:\Llamacpp\cuda1X\llama-server.log` |

Скрипты также выставляют `CUDA_DEVICE_ORDER=PCI_BUS_ID` и
`CUDA_VISIBLE_DEVICES=0,1`.

---

## 🛠️ Вспомогательные утилиты

Из директории установки (`c:\Llamacpp\cuda13\` и т. п.):

- **`llama-cli.exe`** — интерактивный терминальный чат:
  ```cmd
  llama-cli.exe -m <model.gguf> -ngl 99 -c 8192 -p "Привет! Расскажи о себе."
  ```
- **`llama-bench.exe`** — замер скорости prompt processing / генерации:
  ```cmd
  llama-bench.exe -m <model.gguf> -ngl 99 -n 128 -p 512
  ```
- **`llama-quantize.exe`** — квантование GGUF (Q4_K_M, Q5_K_M, Q8_0 и др.):
  ```cmd
  llama-quantize.exe model-f16.gguf model-Q4_K_M.gguf Q4_K_M
  ```

---

## 💻 Конфигурация тестового стенда

Все значения `-ts`, `-t` / `--threads-batch`, `-c`, `-ub`, `-ctk`/`-ctv`
подобраны и проверены на этом железе:

| Компонент   | Значение                                                                 |
| :---------- | :----------------------------------------------------------------------- |
| **CPU**     | AMD Ryzen 9 9950X (16 ядер / 32 потока)                                  |
| **RAM**     | 64 ГБ DDR5-5600                                                          |
| **GPU**     | 2× NVIDIA GeForce RTX 5060 Ti 16GB (32 ГБ VRAM суммарно, без NVLink/P2P) |
| **ОС**      | Windows 11 Pro x64                                                       |
| **Драйвер** | Актуальный драйвер NVIDIA с поддержкой CUDA 12.x / 13.x                  |

> `-ts 17,13` намеренно смещает слои на GPU0 (PCI-шина 1). Значение подбирается
> по факту — сверяйте занятость карт в `nvidia-smi` после старта и двигайте на
> ±1. Если в `llama-server.log` появляется `retrying without pipeline
> parallelism` или `cudaMalloc failed` — VRAM не хватает: понижайте `-c` по
> ступеням либо ослабляйте KV (`-ctv q4_0`). Полная диагностика и формулы —
> в [CALCULATE.md](CALCULATE.md) §4.

При другой конфигурации (иное число ядер CPU, другой объём/распределение VRAM)
значения `-ts`, `-t`, `--threads-batch` и `-c` нужно пересчитать под своё железо.

### Минимальные требования

- **ОС:** Windows 10 / 11 (x64)
- **GPU:** NVIDIA (Pascal и новее: RTX 20xx/30xx/40xx/50xx)
- **Драйвер:** актуальный, с поддержкой CUDA 12.x или 13.x

---

## 🔗 Полезные ссылки

- [Официальный репозиторий llama.cpp](https://github.com/ggml-org/llama.cpp)
- [Релизы llama.cpp](https://github.com/ggml-org/llama.cpp/releases)
- [Модели GGUF на Hugging Face](https://huggingface.co/models?search=gguf)
