# Qwen3.8-Flash-Next (IQ3_S) в Strata: coding-конфиг без рассуждений

Отчёт от 2026-11-27. Модель: **Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S** (оригинал —
<https://huggingface.co/Qwen/Qwen3.8-Flash-Next>), запуск через **Strata Terminal 0.1.69**,
движок `0.1.69-windows-x86_64-cuda-cuda13`.

Цель: максимальная скорость, стабильность и повторяемость для программирования,
**без режима рассуждений**. Контекст **204800 (200k) не менялся** (родной контекст модели —
262144, но по требованию оставлен 200k). Бенч: 2× RTX 5060 Ti 16 GB, Ryzen 9 9950X, 64 GB DDR5.

## 1. Все пути

Корень данных Strata (`settings.json`): `C:\Users\viktor\AppData\Local\Strata\Strata-data`.

| что | путь |
| --- | --- |
| **Итоговый конфиг модели (source of truth)** | `C:\Users\viktor\AppData\Local\Strata\install\strata-iq3_s.json` |
| Копия итогового конфига для документации | `c:\MyProjecs\llamacpp\strata\qwen3.8-flash-next-iq3_s.coding-noreason.json` |
| Бэкап конфига до правки | `c:\MyProjecs\llamacpp\strata\backup\strata-iq3_s.json.before-final` |
| Бэкап исходного конфига | `c:\MyProjecs\llamacpp\strata\backup\strata-iq3_s.json.orig` |
| Скрипт установки/запуска | `C:\Users\viktor\AppData\Local\Strata\install\run-iq3_s.bat` |
| Конфиг запуска (пересобирается) | `C:\Users\viktor\AppData\Local\Strata\launch\iq3_s-200k.json` |
| Логи тюнера | `...\launch\iq3_s-200k.tune.json`, `...\launch\iq3_s-200k.choices.json` |
| Пресет «IQ3_S 200K» | `C:\Users\viktor\AppData\Roaming\Strata\launch-presets\iq3_s-200k.json` |
| Профиль запуска | `C:\Users\viktor\AppData\Roaming\Strata\profiles\launch-iq3_s-200k.json` |
| Профили A/B (можно удалить) | `C:\Users\viktor\AppData\Roaming\Strata\profiles\strata-ab-b0..b12.json` |
| Тюнинг-пресет | `C:\Users\viktor\AppData\Roaming\Strata\presets\d268f072c8804f2fa9d2226634754f7b.json` |
| Активный тюнинг-пресет | `C:\Users\viktor\AppData\Roaming\Strata\presets\active.json` |
| Лог сервера | `C:\Users\viktor\AppData\Local\Strata\runtime\launch-iq3_s-200k.server.log` |
| Лог движка | `C:\Users\viktor\AppData\Local\Strata\launch\iq3_s-200k.engine.log` |
| Движок | `C:\Users\viktor\AppData\Local\Strata\components\engine\0.1.69-windows-x86_64-cuda-cuda13\strata.exe` |
| Python + сервер | `C:\Users\viktor\AppData\Local\Strata\terminal\current\python\python.exe`, `...\terminal\0.1.69\serve\server.py` |
| Шаблон чата (пропатчен) | `C:\Users\viktor\AppData\Local\Strata\terminal\0.1.69\serve\chat_template.jinja` |
| Конвертеры запросов (пропатчены) | `C:\Users\viktor\AppData\Local\Strata\terminal\0.1.69\serve\frontend.py` |
| Настройки сервера | `...\serve\runconfig.py`, `...\serve\server_parts\http_api.py` |
| Модель, шард 1 | `...\Strata-data\models\IQ3_S\Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S-00001-of-00002.gguf` |
| Модель, шард 2 | `...\Strata-data\models\IQ3_S\Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S-00002-of-00002.gguf` |
| Pack + токенизатор | `...\Strata-data\packs\iq3_s\` |
| DFlash2-драфтер | `...\Strata-data\dflash2\qwen3.8-flash-next-dflash2.q4_0-selq4.pack` (+ `.ok`, `draft_vocab.bin`) |
| MTP-слой | `...\Strata-data\mtp\rt` — **отсутствует**, `--mtp` в конфиге мёртвый и вырезается при старте |
| Словари драфтера | `...\terminal\0.1.69\data\draft_vocab{,_en,_cyrillic,_latin,_fr,_arabic}.bin` |
| Патч | `c:\MyProjecs\llamacpp\strata\patches\no-reasoning.patch` |
| Скрипт патча (идемпотентный, с `-Revert`) | `c:\MyProjecs\llamacpp\strata\patches\apply-no-reasoning.ps1` |
| Бэкапы `serve\` | рядом с файлами: `...\terminal\current\serve\<file>.pre-no-reasoning` (их делает скрипт патча); исходники 0.1.69 — `c:\MyProjecs\llamacpp\strata\backup\*.orig` (история, не источник отката для новой версии) |
| Бенчмарк | `c:\MyProjecs\llamacpp\strata\bench\bench.py`, `prompts.json` |
| Конфиги A/B | `c:\MyProjecs\llamacpp\strata\bench\configs\b0..b12.json` |
| Результаты A/B | `c:\MyProjecs\llamacpp\strata\bench\results\*.json` |
| Генератор конфигов A/B | `c:\MyProjecs\llamacpp\strata\bench\make_configs.py` |
| Применение итогового конфига | `c:\MyProjecs\llamacpp\strata\apply_final_config.py` |

## 2. Что реально работало до правок

- `strata launch` уже применял **DFlash2 alone** (`--draft dflash2`, `--draft-conf 0.35`,
  окно `--spec 6`), но словарь драфтера выбирался по языку ОС — **cyrillic** (ru).
- MTP в `args` указывает на несуществующую папку (`optional_missing`), движок его вырезает.
- Контекст 204800, `--kv int8`, `--expert-cache auto` (5393 эксперта, 9.71 GiB VRAM),
  GPU 0 helper / GPU 1 main, layer split auto, один запрос за раз.
- Тюнер: 90.6 t/s decode / 1210 t/s pp4k. В логах: 120–158 t/s на коротких ответах,
  60–86 t/s на глубине ~100k, prefill 2400–2700 t/s на ~95–191k, expert cache hit 84–94%.

## 3. Итоговая конфигурация

Добавлено в `install\strata-iq3_s.json` (и продублировано в `qwen3.8-flash-next-iq3_s.coding-noreason.json`):

```json
"drafting": "dflash2",
"reasoning_effort": "none",
"sampling": {
  "temperature": 0.6, "top_p": 0.8, "top_k": 20, "min_p": 0.0,
  "presence_penalty": 0.0, "frequency_penalty": 0.0, "repetition_penalty": 1.0,
  "seed": 1
},
"user_args": [
  "--draft-conf", "0.35",
  "--mtp-draft-vocab", "C:\\Users\\viktor\\AppData\\Local\\Strata\\terminal\\0.1.69\\data\\draft_vocab_en.bin"
]
```

Почему так:

- `drafting: dflash2` — единственный рабочий драфтер (MTP не установлен); DFlash2 даёт
  **ровно ~2× decode** против запуска без драфтера (64.5 → 122 t/s, см. таблицу).
- `draft_vocab` задан **файлом** `draft_vocab_en.bin` («English and code») через
  `--mtp-draft-vocab`; запись `"draft_vocab": "en"` в конфиг ничего не переключает —
  Strata читает уже подложенный файл. `latin` и `cyrillic` в A/B не выиграли.
- `--draft-conf 0.35` — значение движка по умолчанию для двух карт; 0.5 и 0.7 в пределах шума.
- `sampling` — выбор пользователя: `0.6 + seed 1` без penalties. Penalties заданы явно нулями,
  иначе карточка модели подмешивает `presence_penalty 1.5` (для кода вредно и снижает принятие драфтов).
- Контекст, `--kv int8`, `--expert-cache auto`, окно DFlash2 и разбиение по картам не менялись.
- После старта: **1324 MiB свободно на CUDA0 и 1446 MiB на CUDA1**.

## 4. No-reasoning: что именно пропатчено

Двумя слоями, чтобы мысль не включалась ни шаблоном, ни парсером:

1. `serve\chat_template.jinja`, после проверки `messages`:
   `{%- set enable_thinking = false %}` — шаблон всегда рендерит закрытый пустой `<think></think>`.
2. `serve\frontend.py`:
   - `openai_to_messages` — перед `return`: `kwargs["enable_thinking"] = False`;
   - `anthropic_to_messages` — перед `return`: то же.
   Это важно: состояние reasoning-парсера (`server.py:5850`) считается из того же `kwargs`,
   поэтому ответ не уедет целиком в `reasoning_content` с пустым `content`.

Проверено: запрос Anthropic `/v1/messages` с `thinking: {"type":"enabled","budget_tokens":31999}`
вернул обычный `content` без thinking-блока. OpenAI-запрос — `reasoning_tokens: 0`,
`reasoning_content` отсутствует.

Ограничения:

- Патч действует на **все Qwen-модели** этого инстанса Strata (шаблон общий).
- `strata update` перезаписывает `serve\` — после обновления запустить
  `patches\apply-no-reasoning.ps1` заново (скрипт идемпотентен) и перезапустить сервер.
- Откат: `patches\apply-no-reasoning.ps1 -Revert` (восстанавливает `.pre-no-reasoning`
  рядом с файлами; `backup\*.orig` от 0.1.69 для новой версии не использовать).

### После обновления Strata

1. `strata update` — он заменяет `terminal\<новая версия>\serve\`.
2. `powershell -ExecutionPolicy Bypass -File strata\patches\apply-no-reasoning.ps1`
   — скрипт идёт через `terminal\current`, сам кладёт `.pre-no-reasoning` копии и проверяет
   якоря. `already patched` = всё на месте; ошибка `anchor not found` = шаблон в новой
   версии изменился, патч надо пересмотреть по `patches\no-reasoning.patch`.
3. Перезапустить сервер: `strata launch --preset "IQ3_S 200K" --no-tui`.
4. Проверить лог сервера: `thinking level: none`, `DFlash2`, `draft vocabulary: draft_vocab_en.bin`.
5. Конфиг модели (`install\strata-iq3_s.json`) обновление не трогает; если он окажется
   пересоздан, повторить `python -I strata\apply_final_config.py`.

## 5. A/B-замеры

Методика: один прогон на вариант, одинаковые промпты, `ctx 204800`, `kv int8`, parallel 1,
no-reasoning, DFlash2 (кроме b7/b8/b11). 3 coding-промпта × 2 повтора (до 512 токенов),
глубина 16k, длинный prefill. «prefill90k» фактически **191 587 токенов** — почти весь контекст.
Задержки снимались по SSE; decode = (токены−1)/(время между первым и последним токеном).

| вариант | drafting / conf | vocab | сэмплеры | short decode, med | depth16k | prefill 191k |
| --- | --- | --- | --- | ---: | ---: | ---: |
| b0 (как было, без thinking) | dflash2 / 0.35 | cyrillic | 0.7 / 0.8 / presence 1.5 | 115.2 | 64.3 | 2698 |
| **b1 (выбран)** | dflash2 / 0.35 | en | 0.6 / 0.8, seed 1 | **122.1** | **70.3** | **2706** |
| b2 | dflash2 / 0.5 | en | 0.6 / 0.8, seed 1 | 121.9 | 67.7 | 2701 |
| b3 | dflash2 / 0.7 | en | 0.6 / 0.8, seed 1 | 114.4 | 66.2 | 2701 |
| b4 | dflash2 / 0.7 | latin | 0.6 / 0.8, seed 1 | 117.5 | 65.4 | 2695 |
| b6 | dflash2 / 0.7 | en | 0.6 / top_p 0.95, seed 1 | 121.3 | 73.0 | 2689 |
| b7 | без драфтера | — | greedy, seed 1 | 64.5 | 32.9 | 2762 |
| b10 | dflash2 / 0.35 | en | greedy, `--prompt-cache 0` | 128.0 | 69.3 | 2715 |
| b11 | без драфтера | — | greedy, `--prompt-cache 0` | 64.8 | 34.9 | 2750 |
| b12 | dflash2 / 0.35 | en | greedy, `--expert-cache-cpu-order` | 121.0 | 66.0 | 2700 |
| final (через launch) | dflash2 / 0.35 | en | 0.6 / 0.8, seed 1 | 114.7 | 69.2 | 2705 |

Выводы:

- DFlash2 — главный источник скорости: без него decode падает ~2× (b7/b11).
- Разница 0.5/0.7 conf, en/latin и top_p 0.8/0.95 — в пределах шума ±5–8 % (один прогон на вариант);
  выбран дефолт движка 0.35 и словарь `en` (карточка: «English and code»).
- Принятие драфтов в b1: 76–88 % на коротких ответах (в логе движка `drafts accepted`).
- Prefill стабилен, ~2700 t/s даже на 191k; decode на глубине ~16k — 65–73 t/s.

## 6. Повторяемость: честный результат

Побитовой повторяемости на этой сборке/железе **нет**, и конфигом она не лечится:

- `temperature 0.6 + seed 1`: короткие ответы (45 символов) совпадают, длинные (500+ токенов)
  расходятся в 2 из 3 промптов.
- `temperature 0` (greedy), seed 1 — тоже расходится на длинных ответах.
- `--prompt-cache 0` и отключение DFlash2 (b10, b11) — всё равно расходятся.
- `--expert-cache-cpu-order` (b12) — не помогает.
- Совпадение повторов наблюдалось для одного промпта (merge_intervals) при `--prompt-cache 0`.

Причина — недетерминизм движка (MoE-редукции/expert cache), а не сэмплер. Карточка модели
детерминизма не обещает. Практический вывод: фиксированный `seed` и конфиг дают **стабильный
стиль и скорость**, но для воспроизводимых экспериментов сравнивайте короткие ответы или
усредняйте несколько прогонов. Greedy за повторяемость платить не стоит: он не гарантирует
её и стоит ~2× скорости.

## 7. Как пользоваться

```powershell
# запуск итогового конфига (штатный путь, база — install\strata-iq3_s.json)
strata launch --preset "IQ3_S 200K" --no-tui

# статус / остановка
strata launch --status
strata launch --stop --preset "IQ3_S 200K"

# повторный замер
python -I c:\MyProjecs\llamacpp\strata\bench\bench.py `
  --variant final `
  --config c:\MyProjecs\llamacpp\strata\qwen3.8-flash-next-iq3_s.coding-noreason.json `
  --out-dir c:\MyProjecs\llamacpp\strata\bench\results

# пересобрать варианты A/B
python -I c:\MyProjecs\llamacpp\strata\bench\make_configs.py `
  C:\Users\viktor\AppData\Local\Strata\install\strata-iq3_s.json `
  c:\MyProjecs\llamacpp\strata\bench\configs
```

Применить конфиг заново после сброса: `python -I strata\apply_final_config.py`.
Откатить конфиг: скопировать `strata\backup\strata-iq3_s.json.before-final` в
`C:\Users\viktor\AppData\Local\Strata\install\strata-iq3_s.json` и перезапустить сервер.

Проверка, что всё в силе (лог сервера):

- `[strata] sampling defaults from the config: temperature=0.6, top_p=0.8, ... seed=1`
- `[strata] thinking level: none`
- `[strata] drafting: DFlash2 alone (--draft dflash2, --draft-conf 0.35)`
- `[strata] drafting: draft vocabulary: draft_vocab_en.bin`
- `ready: ... context 204800 tokens`

## 8. Ограничения и риски

- Патч `serve\` не переживает `strata update`; после обновления повторить
  `patches\apply-no-reasoning.ps1` и перезапустить сервер (порядок — §4, «После обновления Strata»).
- Профили `strata-ab-b*` и конфиги `bench\configs\b*.json` — артефакты A/B, на работу
  штатного пресета не влияют; можно удалить.
- `--prompt-cache 0` в b10/b11 не отключил переиспользование промпта (TTFT второго повтора
  0.06 с), поэтому считать эти варианты «без кэша» нельзя.
- Замеры — по одному прогону на вариант (кроме 3 промптов × 2 повторов внутри), шум ±5–8 %.
  Числа 90.6/1210 из тюнера и 120–158 t/s из логов движка относятся к другим промптам.
