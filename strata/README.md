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
| Копия конфига для запуска и документации | `c:\MyProjecs\llamacpp\strata\qwen3.8-flash-next-iq3_s.coding-noreason.json` |
| Конфиг режима с размышлениями | `c:\MyProjecs\llamacpp\strata\qwen3.8-flash-next-iq3_s.coding-reason.json` |
| **Запуск режима с размышлениями** (сервер + TUI-дашборд) | `c:\MyProjecs\llamacpp\strata\run-iq3_s-coding-reason.bat` |
| Профиль режима с размышлениями (runtime) | `C:\Users\viktor\AppData\Roaming\Strata\profiles\iq3_s-coding-reason.json` |
| Лог сервера режима с размышлениями | `C:\Users\viktor\AppData\Local\Strata\runtime\iq3_s-coding-reason.server.log` |
| Лог движка режима с размышлениями | `c:\MyProjecs\llamacpp\strata\iq3_s-coding-reason.engine.log` |
| **Файл запуска (с дашбордом `strata launch`)** | `c:\MyProjecs\llamacpp\strata\run-iq3_s-coding-noreason.bat` |
| Файл запуска PowerShell (то же самое) | `c:\MyProjecs\llamacpp\strata\run-iq3_s-coding-noreason.ps1` |
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
- С 2026-11-27 патч — **гейт по переменной `STRATA_ALLOW_THINKING`**: без неё оба слоя работают
  ровно как раньше (жёсткое «без размышлений»), с ней шаблон может думать. Переменную выставляет
  только `run-iq3_s-coding-reason.bat`, так что noreason-пресет, `install\run-iq3_s.bat` и
  обычный `strata launch` не изменились. Скрипт патча идемпотентен и сам обновляет старую
  безусловную форму (`patched: … (upgraded)`), а `-Revert` по-прежнему восстанавливает
  `.pre-no-reasoning`-копии. Подробности — §9.
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
# запуск из этой папки: сервер + TUI-дашборд, как у strata launch
strata\run-iq3_s-coding-noreason.bat
powershell -NoProfile -ExecutionPolicy Bypass -File strata\run-iq3_s-coding-noreason.ps1

# режим с размышлениями: сервер фоном + TUI-дашборд в том же окне, API на http://127.0.0.1:8080
strata\run-iq3_s-coding-reason.bat
# то же вручную (переменная обязательна, иначе патч выключит мышление);
# профиль создаётся один раз, если его ещё нет
strata profile create iq3_s-coding-reason --from-config c:\MyProjecs\llamacpp\strata\qwen3.8-flash-next-iq3_s.coding-reason.json
set STRATA_ALLOW_THINKING=1
strata runtime start --profile iq3_s-coding-reason
strata monitor --url http://127.0.0.1:8080
# остановка и статус этого запуска
strata runtime stop --profile iq3_s-coding-reason
strata runtime status --profile iq3_s-coding-reason

# headless-вариант (без монитора), если нужен только сервер
strata serve --profile c:\MyProjecs\llamacpp\strata\qwen3.8-flash-next-iq3_s.coding-noreason.json

# штатный путь через пресет (база — install\strata-iq3_s.json), без монитора
strata launch --preset "IQ3_S 200K" --no-tui

# статус / остановка
strata launch --status
strata launch --stop --preset "IQ3_S 200K"

# повторный замер
python -I c:\MyProjecs\llamacpp\strata\bench\bench.py `
  --variant final `
  --config c:\MyProjecs\llamacpp\strata\qwen3.8-flash-next-iq3_s.coding-noreason.json `
  --out-dir c:\MyProjecs\llamacpp\strata\bench\results

# замер режима с размышлениями: уровень — на запрос (off/low/medium/xhigh),
# лимиты вывода подняты, потому что thinking тратит max_tokens
python -I c:\MyProjecs\llamacpp\strata\bench\bench.py `
  --variant r0-xhigh `
  --config c:\MyProjecs\llamacpp\strata\bench\configs\r0.json `
  --effort xhigh --max-tokens-short 2048 --max-tokens-depth 512 --max-tokens-prefill 256

# проверка API-контрактов на запущенном сервере (уровни, thinking-блоки, разбор)
python -I c:\MyProjecs\llamacpp\strata\bench\verify_reasoning_api.py

# пересобрать варианты A/B
python -I c:\MyProjecs\llamacpp\strata\bench\make_configs.py `
  C:\Users\viktor\AppData\Local\Strata\install\strata-iq3_s.json `
  c:\MyProjecs\llamacpp\strata\bench\configs
python -I c:\MyProjecs\llamacpp\strata\bench\make_configs.py `
  c:\MyProjecs\llamacpp\strata\qwen3.8-flash-next-iq3_s.coding-reason.json `
  c:\MyProjecs\llamacpp\strata\bench\configs --family reason
```

`run-iq3_s-coding-noreason.bat` вызывает `strata launch --preset "IQ3_S 200K"`: сервер запускается
как инстанс `strata runtime` и открывается тот же монитор, что и при обычном `strata launch`
(Overview / Serving / Requests / Engine / Hardware / Logs / Connect). Остановка — `q` в мониторе
(«keep serving or stop») или `strata launch --stop --preset "IQ3_S 200K"`; во втором случае окно
монитора остаётся открытым и его надо закрыть вручную. Логи этого запуска:
`...\Local\Strata\launch\iq3_s-200k.engine.log` и
`...\Local\Strata\runtime\launch-iq3_s-200k.server.log`.

Параметры берутся из установленного конфига `install\strata-iq3_s.json` (его использует каждый
`strata launch`); `apply_final_config.py` держит его синхронным с копией
`strata\qwen3.8-flash-next-iq3_s.coding-noreason.json`. Копия — документация и источник для
headless-запуска `strata serve --profile`, сам `.bat` её больше не читает.

Если те же настройки уже обслуживаются, `strata launch` печатает адрес и монитор не открывает —
тогда дашборд вручную: `strata monitor --url http://127.0.0.1:8080`. Если обслуживаются другие
настройки, `launch` спросит про перезапуск; в неинтерактивном запуске нужен `--restart` (он
остановит текущую сессию).

В `.bat` путь к папке **абсолютный**, как в установочном `run-iq3_s.bat`: раннер, который передаёт
файл в `cmd` через поток, не раскрывает `%~dp0` (он доходит литералом), и Strata падает с
`cannot read run config (FileNotFoundError)`. При переносе репозитория поправить `cd /d` в файле.
В `.ps1` папка берётся из `$PSScriptRoot`; если он пуст (запуск через поток), срабатывает
абсолютный fallback `C:\MyProjecs\llamacpp\strata`. Если политика запрещает локальные скрипты —
запускать с `-ExecutionPolicy Bypass`, как в команде выше.

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

## 9. Режим с размышлениями

Отчёт от 2026-11-27. Вторая конфигурация того же стенда: та же модель, движок, контекст 204800,
`kv int8`, DFlash2 (`--draft-conf 0.35`, `draft_vocab_en.bin`), обе карты — но мышление включено,
а уровень выбирает harness по запросу. Noreason-конфиг §3–§8 не меняется.

### 9.1 Состав

| что | путь |
| --- | --- |
| Конфиг (источник правды для `strata serve`) | `strata\qwen3.8-flash-next-iq3_s.coding-reason.json` |
| Запуск | `strata\run-iq3_s-coding-reason.bat` |
| Лог движка | `strata\iq3_s-coding-reason.engine.log` |
| A/B-конфиги | `strata\bench\configs\r0..r2.json` |
| Результаты | `strata\bench\results\r*-*.json` |
| Проверка API | `strata\bench\verify_reasoning_api.py` |
| Проверка кэша при смене уровня | `strata\bench\check_effort_cache.py` |

`.bat` делает `set STRATA_ALLOW_THINKING=1`, один раз создаёт профиль `iq3_s-coding-reason`
(`%APPDATA%\Strata\profiles\`, ссылка на репозиторный конфиг — байты не копируются), поднимает
сервер как фоновый runtime-инстанс
(`strata runtime start --profile iq3_s-coding-reason --wait 900`) и в том же — единственном —
окне открывает дашборд `strata monitor --url http://127.0.0.1:8080`: те же семь экранов
(Overview / Serving / Requests / Engine / Hardware / Logs / Connect), что и у `strata launch`;
веб-UI и API — на `http://127.0.0.1:8080`. Пока модель грузится, консоль показывает строку
«Starting the model...»; `runtime start` ждёт готовности и печатает
`iq3_s-coding-reason: ready  instance …  http://127.0.0.1:8080` (или ошибку — тогда скрипт
останавливается с `pause`). `STRATA_ALLOW_THINKING` наследуется owner host'ом и сервером, а
точная причина сбоя (например, занятый порт) — в
`%LOCALAPPDATA%\Strata\runtime\iq3_s-coding-reason.server.log`. `q` в мониторе только отцепляет:
сервер продолжает работать, окно закрывается. Остановка —
`strata runtime stop --profile iq3_s-coding-reason`; статус —
`strata runtime status --profile iq3_s-coding-reason`. Через `strata launch --preset` этот режим не
запустить: пресет один на модель и каждый запуск пересобирает конфиг из `install\strata-iq3_s.json`,
где `reasoning_effort: none`; два пресета с разным мышлением на одну модель не сосуществуют.
Повторный запуск ничего не перезапускает: скрипт сначала спрашивает
`strata runtime status --profile iq3_s-coding-reason`, и состояние `ready` или `starting` сразу
ведёт в дашборд (двойной клик во время загрузки модели тоже просто откроет монитор). Если 8080
уже занят другим сервером (например, noreason-запуском), скрипт пишет
`Another Strata server already serves http://127.0.0.1:8080; stop it to start the reason instance.`
и ждёт клавишу. Одновременно живёт только один режим (порт 8080 и обе карты): reason-инстанс и
noreason-запуск вместе не поднимаются.

Патч `serve\` (§4) стал гейтом: без `STRATA_ALLOW_THINKING` оба слоя жёстко выключают `<think>` —
noreason-пресет, `install\run-iq3_s.bat` и обычный `strata launch` ведут себя как раньше.

### 9.2 Что в конфиге

| ключ | значение | зачем |
| --- | --- | --- |
| `reasoning_effort` | `"high"` | уровень по умолчанию для запросов без своего. Ключ конфига принимает только `none/low/medium/high`; `xhigh` отвергается при старте, а `high` — это `xhigh` шаблона |
| `sampling` | 1.0 / 0.95 / 20 / min_p 0 / penalties 0 / rep 1.0 / seed 1 | thinking-набор карточки модели; совпадает с thinking-протоколом самой Strata (`strata-qwen38-thinking-v1-draft.1`). Карточка предупреждает о циклах в `<think>` при низкой температуре; в прогоне r1 (0.6) их не было, но дефолт оставлен 1.0 |
| `effort_position` | `"end"` | не-дефолтный уровень едет коротким system-ходом прямо перед ответом (`--tail-role-token`), префикс промпта не меняется — смена уровня в harness не сбрасывает кэш |
| `anthropic_thinking` | не задан | `"on_request"` **не помогает**: при заданном `reasoning_effort` `Service.with_shared` подставляет `output_config` раньше конвертера, и запрос без `thinking` всё равно думает на конфиг-уровне |

Проверено в логе старта: `thinking level: high`, `sampling defaults from the config: temperature=1.0,
top_p=0.95, top_k=20, min_p=0.0, presence_penalty=0.0, frequency_penalty=0.0, repetition_penalty=1.0,
seed=1`, `effort_position end: ...`, `drafting: DFlash2 alone (--draft dflash2, --draft-conf 0.35)`,
`drafting: draft vocabulary: draft_vocab_en.bin`. Аргументы движка совпадают с noreason-линией
(DFlash2 нормализует `--spec 4 --spec-min-p 0.5` в `--spec 6`, MTP вырезан, драфтер —
конвертированный `-selq4`-пак), плюс `--tail-role-token`.

Ещё одна механика, которую стоит знать: при `max_tokens ≥ 1024` Strata без бюджета закрывает
thinking заранее, чтобы ответу осталось место: `budget = max_tokens − clamp(max_tokens/4, 512,
max_tokens/2)`; при 2048 это 1536. Отключается `"answer_room": false` в конфиге — не отключаем,
иначе harness с малым `max_tokens` получит пустой ответ.

### 9.3 Как выбрать уровень

Запрос всегда побеждает конфиг:

| клиент | поле | маппинг |
| --- | --- | --- |
| OpenAI | `reasoning_effort` | `off`/`none`/`minimal`/`disabled` → выключено; `low`; `medium`; `high`/`xhigh`/`max` → xhigh |
| OpenAI | `chat_template_kwargs {"enable_thinking": false}` | выключено |
| Anthropic | `thinking: {"type": "disabled"}` | выключено |
| Anthropic | `thinking.budget_tokens` | <2048 → low, <8192 → medium, иначе high (и сам бюджет) |
| Anthropic | `output_config.effort` | как `reasoning_effort` |

Шаблон различает три уровня: `low` (кратко), `medium` (без преамбулы), `xhigh` (полная
инструкция). Ответы приходят с `reasoning_content` (OpenAI) и `thinking`-блоками (Anthropic).
Провайдер CC Switch для harness — в `CC-Switch.md`; родной путь Strata — `strata connect claude`.

### 9.4 Замеры

Методика та же, что в §5: те же промпты и кейсы, один сервер, карты свободны. Отличия: лимиты
вывода подняты, потому что thinking тратит `max_tokens` (short 2048, depth 512, prefill 256), а
`decode_all` считается по всем completion-токенам (reasoning + ответ) от первого до последнего
дельты — старый `decode` в thinking-прогонах измеряет только видимый ответ и врёт. Уровень —
per-request на одном старте (r0, 1.0/0.95, `effort_position end`).

| прогон | short decode_all, med | depth16k decode_all | prefill 191k, t/s | reasoning, символов | пустых ответов |
| --- | ---: | ---: | ---: | ---: | ---: |
| r0, effort xhigh | 88.7 | 75.8 | 2708.8 | 35 085 | 1 (warmup) |
| r0, effort medium | 89.5 | 62.0 | 2687.8 | 29 672 | 1 (warmup) |
| r0, effort low | 90.9 | 84.3 | 2709.0 | 25 330 | 1 (warmup) |
| r0, effort off | 118.2 | 68.1 | 2704.8 | 0 | 0 |
| r1 (0.6/0.8), effort xhigh | 96.3 | 78.0 | 2706.9 | 31 974 | 1 (warmup) |
| r2 (`effort_position start`), effort xhigh | 86.5 | 88.1 | 2712.1 | 30 942 | 1 (warmup) |

Для сравнения, noreason-линия §5 (512 `max_tokens`, temp 0.6/0.8, ответы без reasoning) — 114.7 t/s
по видимому ответу; наш `off` на сэмплерах 1.0/0.95 дал 118.2 t/s, то есть то же в пределах шума.
Выводы:

- мышление стоит ~25 % скорости ответа (88.7 против 118.2 на одинаковых сэмплерах); prefill не
  меняется (~2700 t/s на 191k, как в §5);
- уровень меняет длину рассуждения (35k / 30k / 25k символов на xhigh/medium/low при 2048
  max_tokens), но не скорость декода в пределах шума; выбор уровня — это про качество и длину
  thinking, а не про t/s;
- `temperature 0.6` (r1) дал 96.3 t/s против 88.7 у 1.0 — на ~8 % быстрее при той же длине
  рассуждений; зацикливания в шести коротких ответах не было. Это один прогон, а карточка модели
  прямо предупреждает о циклах в `<think>` при низкой температуре, поэтому 1.0 оставлено
  дефолтом; 0.6 — рычаг, если скорость важнее;
- `decode` (только видимый ответ) в thinking-прогонах не имеет смысла (сотни и тысячи t/s): ответ
  короткий, а токены считаются все; ориентироваться только на `decode_all`;
- depth16k-числа шумные: ответ там 3–35 символов, `decode_all` считается по 12–131 токену;
- разброс между повторами одного промпта большой (reasoning 2.6k против 6.0k символов на
  `medium`), это стохастика temp 1.0, а не конфиг; одиночный прогон — не A/B.

Точность на двух синтетических задачах (по одному прогону, не статистика): `util_137(2)=686`
верно у medium/xhigh (у low и off — выражение `137*2+412`, тоже верное), а `k2711=8134` на
глубине 191k верно у xhigh на r0 и на r2; low/medium/off и r1 (0.6) ответили 8734/9085. Это
аргумент держать xhigh дефолтом для длинного контекста, но выборка слишком мала — проверять на
своих задачах.

### 9.4.1 Смена уровня и кэш

`check_effort_cache.py` шлёт один и тот же промпт (11.1k токенов) три раза: xhigh → low → xhigh.

| сервер | запрос | prompt_tokens | cached_tokens | время |
| --- | --- | ---: | ---: | ---: |
| r1, `effort_position: end` | xhigh | 11 105 | 0 | 7.7 с |
| r1, `effort_position: end` | low | 11 135 (+30 хвост) | **11 100** | 0.9 с |
| r1, `effort_position: end` | xhigh | 11 105 | **11 100** | 0.6 с |
| r2, `effort_position: start` | xhigh | 11 105 | 0 | 7.6 с |
| r2, `effort_position: start` | low | 11 093 | 0 | 7.1 с |
| r2, `effort_position: start` | xhigh | 11 105 | 0 | 7.1 с |

На `end` смена уровня переиспользует весь префикс: новый только 30-токенный хвост с уровнем
(0.9 с против 7.7 с холодного префилла). На `start` каждый запрос с другим уровнем префиллит
заново: `cached_tokens` 0 и ~7 с на всех трёх запросах, включая возврат к xhigh — преамбула
уровня стоит в system-блоке в начале и меняет префикс. Скорость декода при этом одинаковая
(r0 88.7 против r2 86.5 — шум), так что `end` не стоит ничего и экономит префилл в harness,
где уровень меняют на ходу.

Оговорка об артефактах: r0.json пересобран после этих прогонов — в нём исправлен только путь к
`log` (был относительный, из-за чего сервер не стартовал из r1/r2). Поэтому `config_sha256` в
`r0-*.json` относится к предыдущей версии файла; настройки, по которым шли замеры, те же.

### 9.5 Ограничения

- `strata update` заменяет `serve\`: после обновления повторить
  `patches\apply-no-reasoning.ps1` (скрипт идемпотентен) и перезапустить сервер. Конфиг, батник
  и бенч апдейт не трогает.
- Без `STRATA_ALLOW_THINKING=1` reasoning-конфиг ведёт себя как noreason — переменную выставляет
  только `run-iq3_s-coding-reason.bat`. Проверено живьём: при незаданной переменной запросы с
  `reasoning_effort: "low"` и `"xhigh"` вернули `reasoning_content` 0 символов и
  `reasoning_tokens: 0`, хотя в конфиге стоит `high`, а лог печатает `thinking level: high` —
  гейт патча стоит ниже конфига и перебивает и его, и запрос.
- `strata serve` пишет свой вывод в консоль; у reason-скрипта сервер фоновый (runtime), его вывод —
  в `%LOCALAPPDATA%\Strata\runtime\iq3_s-coding-reason.server.log`, лог движка — по полю `log`
  конфига (`strata\iq3_s-coding-reason.engine.log`).
- Файл `<config>.shared-settings.json` рядом с конфигом (настройки Chat из веб-UI) перекрывает
  `reasoning_effort`; при замерах его быть не должно.
- Никакой побитовой повторяемости по-прежнему нет (§6): с thinking это тем более так.
