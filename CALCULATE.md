# CALCULATE.md — расчёт бюджета VRAM и выгрузки слоёв в llama.cpp

Назначение: по параметрам **модели**, **запуска** и **железа** заранее посчитать,
поместится ли модель в видеопамять целиком, сколько слоёв уйдёт на GPU, какой
максимум контекста возможен и как сбалансировать несколько карт — так, чтобы
**видеопамять была заполнена слоями максимально**, но **ни один слой/операция не
падали на CPU**.

Формулы обобщённые (dense / GQA / MoE / SWA / hybrid-SSM). В конце —
полностью просчитанный калибровочный пример на `Qwen3.5-27B` (`arch=qwen35`) +
2× RTX 5060 Ti 16 ГБ, где все коэффициенты сверены с реальным логом загрузки.

Единицы: всё считаем в байтах, потом `МиБ = байты / 1048576`, `ГиБ = байты / 2³⁰`.

---

## 1. Обозначения

### 1.1 Параметры модели (откуда брать)

Запусти `llama-server -m MODEL --verbose 2>&1 | grep -E "print_info|kv_cache|memory_recurrent|buffer size|offloaded"`
(или `llama-gguf`/`gguf_dump`). Ключи GGUF даны как `<arch>.*`.

| Символ | Смысл | `print_info:` | Ключ GGUF | HF `config.json` |
|---|---|---|---|---|
| `L` | число блоков (слоёв) | `n_layer` | `<arch>.block_count` | `num_hidden_layers` |
| `d` | скрытый размер | `n_embd` | `<arch>.embedding_length` | `hidden_size` |
| `n_head` | голов внимания | `n_head` | `<arch>.attention.head_count` | `num_attention_heads` |
| `n_kv` | KV-голов (GQA) | `n_head_kv` | `<arch>.attention.head_count_kv` | `num_key_value_heads` |
| `dh_k`,`dh_v` | размер головы K/V | `n_embd_head_k/v` | `<arch>.attention.key/value_length` | `head_dim` |
| `d_kgqa` | `= n_kv · dh_k` | `n_embd_k_gqa` | — | — |
| `d_vgqa` | `= n_kv · dh_v` | `n_embd_v_gqa` | — | — |
| `n_ff` | размер FFN | `n_ff` | `<arch>.feed_forward_length` | `intermediate_size` |
| `V` | размер словаря | `n_vocab` | `<arch>.vocab_size` / tokenizer | `vocab_size` |
| `C_train` | обученный контекст | `n_ctx_train` | `<arch>.context_length` | `max_position_embeddings` |
| `W_swa` | окно SWA (0 = нет) | `n_swa` | `<arch>.attention.sliding_window` | `sliding_window` |
| `E`,`E_act` | всего/активных экспертов | `n_expert`,`n_expert_used` | `<arch>.expert_count`,`expert_used_count` | `num_experts`,`num_experts_per_tok` |
| SSM: `d_conv` | ширина conv1d | `ssm_d_conv` | `<arch>.ssm.conv_kernel` | — |
| SSM: `d_inner` | внутренний размер | `ssm_d_inner` | `<arch>.ssm.inner_size` | — |
| SSM: `d_state` | размер состояния | `ssm_d_state` | `<arch>.ssm.state_size` | — |
| SSM: `n_group` | групп | `ssm_n_group` | `<arch>.ssm.group_count` | — |
| `N_par` | число параметров | `model params` | — | — |
| `file_bytes` | размер `.gguf` | `file size` | — | — |
| `bpw` | бит на вес | `BPW` | `= 8·file_bytes / N_par` | — |

Производные:
- `L_attn` — слои с обычным KV-кэшем (в чистом трансформере `= L`).
- `L_swa` — из них со скользящим окном (Gemma-2/3 и т. п.).
- `L_rec` — рекуррентные (SSM/Mamba/gated-delta) слои, `L_rec = L − L_attn`.
  Гибриды с шаблоном «каждый `p`-й слой — полное внимание»: `L_attn = L / p`.

### 1.2 Параметры запуска (`llama-server`)

| Флаг | В расчёте | Влияние на VRAM |
|---|---|---|
| `-ngl N` (`--n-gpu-layers`) | `g` = слоёв на GPU | ↑ `g` → ↑ вес на GPU; `g < L+1` ⇒ часть блоков на CPU |
| `-ts a,b,…` (`--tensor-split`) | доли `ts_i` | распределение весов/KV между картами |
| `-sm {layer,row,none}` | режим сплита | `layer`: слой целиком на одной карте; `row`: каждый тензор дробится; `none`: всё на `main-gpu` |
| `-c N` (`--ctx-size`) | `n_ctx` | линейный рост KV (и, для гибрид/`-fa off`, compute-буфера) |
| `-ctk`,`-ctv TYPE` | `bpe_k`,`bpe_v` | байт/элемент KV (таблица ниже) |
| `-b`,`-ub N` | `n_batch`,`n_ubatch` | `ub` линейно масштабирует compute-буфер |
| `-fa {on,off}` | flash-attention | `on` убирает член compute-буфера `∝ n_ctx·n_head` |
| `-np N` (`--parallel`) | `n_seq` слотов | KV и SSM-состояние умножаются на число слотов |
| `-kvu` (`--kv-unified`) | `n_seq_kv = 1` | один общий KV-буфер (иначе `× n_np`) |
| `--n-cpu-moe N` | MoE-слои на CPU | выносит expert-веса `N` слоёв в RAM (только MoE) |
| `--no-kv-offload` | KV в RAM | KV не в VRAM (резко медленнее) |
| `--spec-type …` + `--spec-draft-*` | draft-модель | +веса черновика (0 при MTP) +его KV +его compute |
| `-ctxcp`,`-cram` | чекпоинты контекста | **host RAM**, НЕ VRAM |
| `--mmproj FILE` / `--no-mmproj` | vision-проектор | `+file_bytes(mmproj)` в VRAM либо 0 |

### 1.3 Железо

| Символ | Смысл |
|---|---|
| `n_gpu` | число GPU |
| `VRAM_i` | всего памяти на карте `i` (`nvidia-smi --query-gpu=memory.total`; у RTX 5060 Ti 16G это **16311 МиБ**) |
| `P` | копий compute-буфера: `1` для одной карты или tensor-split без pipeline; `= n_gpu` при pipeline parallelism (несколько карт, `-sm layer`, без NVLink/P2P — обычный случай) |
| `margin_i` | резерв под фрагментацию/драйвер, **≥ 512 МиБ/карту** |

### 1.4 Байты на элемент KV (`bpe`) по типу `-ctk/-ctv`

| type | bpe (Б/элемент) |
|---|---|
| `f16`, `bf16` | 2.0 |
| `q8_0` | 1.0625 |
| `q5_1` | 0.75 |
| `q5_0` | 0.6875 |
| `q4_1` | 0.625 |
| `q4_0` | 0.5625 |

(Блок из 32 значений: `q4_0` = 16+2 Б, `q4_1`/`q5_0` = 18/22 Б, `q5_1` = 24 Б,
`q8_0` = 32+2 Б; делим на 32.)

---

## 2. Формулы по компонентам (память на всю модель, затем делим по картам)

Итоговая занятость карты `i`:

```
Used_i  ≈  W_i  +  KV_i  +  RS_i  +  CB_i·[есть PP]  +  DRAFT_i  +  OVH_i
Условие «всё на GPU, без CPU»:  Used_i + margin_i ≤ VRAM_i   для каждой i
                                и  g ≥ L + 1  (ngl покрывает все блоки + выход)
```

### 2.1 Веса `W`

```
W_model      ≈ file_bytes                       (метаданные GGUF ≈ 0)
bpw          = 8 · file_bytes / N_par
W_embed      = V · d · bpw_embed / 8            (тензор token_embd)
W_output     = V · d · bpw_output / 8           (тензор output; при tied = 0)
W_repeat     = W_model − W_embed − W_output     (сумма всех blk.*)
W_layer      ≈ W_repeat / L                     (средний вес одного блока)
```

Распределение (`-sm layer`, `g ≥ L+1`):

```
доля карты i:            r_i = ts_i / Σ ts
W_i ≈ W_repeat · r_i  +  (W_output если output-тензор на карте i)
```

- `token_embd` часто **не выгружается**: в логе это `CPU_Mapped model buffer
  size ≈ W_embed`. Это **нормально** (эмбеддинг-lookup на хосте), НЕ «слой на CPU».
- `-sm row`: каждый тензор дробится по `r_i` → `W_i ≈ W_model · r_i`.
- `-sm none`: `W` целиком на `main-gpu`.
- Неполный offload (`g < L+1`): `W_cpu ≈ (L + 1 − g) · W_layer` уходит в RAM
  и обрабатывается на CPU → скорость падает в разы. **Этого избегаем.**

MoE: `W_layer` делится на «плотную» часть и expert-часть
`W_exp_layer ≈ E · (3 · d · n_ff) · bpw / 8`. `--n-cpu-moe N` убирает с GPU
`N · W_exp_layer`.

### 2.2 KV-кэш `KV`

Растёт **только на слоях с обычным вниманием** (`L_attn`). На карту попадает
KV тех слоёв, что назначены этой карте (`-sm layer`).

```
kv_per_tok_layer = d_kgqa · bpe_k  +  d_vgqa · bpe_v          (Б/токен/слой)
                 = n_kv · dh_k · bpe_k  +  n_kv · dh_v · bpe_v

ctx_len(l) = n_swa            если слой l — SWA  (и n_swa>0)
           = n_ctx            иначе

KV_total = Σ_{l ∈ L_attn}  kv_per_tok_layer · ctx_len(l) · n_seq_kv
n_seq_kv = 1                  при -kvu или -np 1
         = n_np               иначе
```

Частные случаи:
- **Dense / GQA** (все слои одинаковые, без SWA):
  `KV_total = 2 · L · n_kv · dh · bpe · n_ctx · n_seq_kv`
  (при `dh_k = dh_v = dh`, `bpe_k = bpe_v = bpe`).
- **SWA-гибрид** (напр. Gemma-3: 5 локальных на 1 глобальный):
  считаем глобальные слои по `n_ctx`, локальные по `min(n_ctx, n_swa)`.
- **Hybrid-SSM** (qwen35, Jamba, …): `L_attn = L/p`, рекуррентные слои KV
  **не имеют** — см. 2.3.
- **MLA** (DeepSeek-V2/V3): вместо `d_kgqa+d_vgqa` берётся
  `kv_lora_rank + dh_rope` на токен/слой.

На карту `i`:
```
KV_i = (Σ по слоям L_attn, назначенным карте i) kv_per_tok_layer · ctx_len(l) · n_seq_kv
```
При `-sm layer` слои распределяются пропорционально `ts`, поэтому грубо
`KV_i ≈ KV_total · r_i` (с округлением до целого числа attn-слоёв).

### 2.3 Рекуррентное состояние `RS` (SSM / Mamba / gated-delta)

**Фиксированный** размер: не зависит от `n_ctx`, масштабируется числом
последовательностей `n_rs` (`≈ 1`; `+2`, если включён MTP/спекулятивный черновик,
он держит доп. копии состояния).

```
conv_state_layer = (d_inner + 2 · n_group · d_state) · (d_conv − 1) · 4Б   (R, f32)
ssm_state_layer  ≈ heads · dh_state² · 4Б   (S, f32; точная форма зависит от арх.
                   — gated-delta ≠ Mamba2; сверять по логу)

RS_total = L_rec · (conv_state_layer + ssm_state_layer) · n_rs
```

Практика: итог — **сотни МиБ** и меньше; проще прочитать из лога строку
`llama_memory_recurrent: size = … MiB` и делёж `CUDA0/CUDA1 RS buffer size`.

### 2.4 Compute / graph-буфер `CB`

Рабочая память графа вычислений на **одно устройство**. При pipeline
parallelism каждая карта держит свою копию (`P = n_gpu`); плюс небольшой
`CUDA_Host compute buffer` в RAM.

```
CB_dev ≈ c_act · n_ubatch · d · 2Б            (базовый член, ∝ ub)
        + [если -fa off]  n_ubatch · n_head · n_ctx · 2Б   (матрица оценок внимания)
        + [гибрид/SSM]    рост ∝ n_ctx  (буферы chunk-scan линейного внимания)
```

- `c_act` — число одновременно живых активаций в графе (эмпирически单; читать
  `sched_reserve: CUDAx compute buffer size` из `--verbose`).
- Чистый dense-трансформер с `-fa on`: `CB` практически **не зависит** от `n_ctx`.
- `-fa off` или hybrid/SSM: `CB` **растёт** с `n_ctx` (для qwen35 —
  см. калибровку: ≈ 0.018 МиБ/токен суммарно по картам в окне 180k–262k).
- `CB ∝ n_ubatch` — уменьшение `-ub` (512→256→128) кратно ужимает `CB`, ценой
  скорости prefill.
- Если `Σ CB_dev` не влезает — llama.cpp пишет
  `retrying without pipeline parallelism` и переходит на **одну** копию `CB`
  (медленнее, но экономит память).

### 2.5 Draft-модель `DRAFT` (спекулятивное декодирование)

```
DRAFT = W_draft + KV_draft(n_ctx_draft) + CB_draft
```
- `--spec-type draft-mtp`: `W_draft = 0` (MTP-голова делит веса target),
  `KV_draft` мал (1 слой), `CB_draft` — сотни МиБ (в логе — второй блок
  `sched_reserve` с малым `graph nodes`).
- Отдельная draft-GGUF: `W_draft = file_bytes(draft)`, свой KV по своим
  `L,n_kv,dh` и `n_ctx_draft`.

### 2.6 Прочее `OVH`

```
OVH_i ≈ ctx_output_i (≈ 1 МиБ)  +  CUDA/cuBLASLt overhead (≈ 300…800 МиБ/карту,
        включает workspace cuBLASLt и аллокатор)  +  fragmentation
+ mmproj (если грузится): + file_bytes(mmproj)  (у qwen35 mmproj-F16 ≈ 0.86 ГиБ; --no-mmproj → 0)
```
Закладывать `margin_i ≥ 512 МиБ` сверх расчёта.

---

## 3. Обратные задачи (ядро калькулятора)

### 3.1 Максимальный `-ngl` при заданном `n_ctx`

Наибольшее `g`, при котором для **каждой** карты
`W_i(g) + KV_i(g) + RS_i + CB_i·[PP] + DRAFT_i + OVH_i + margin_i ≤ VRAM_i`.
(KV/RS тоже зависят от `g` — учитываются только слои, реально попавшие на GPU.)
Если максимум `g < L + 1` — **контекст или квантизацию KV надо ужимать**, иначе
часть блоков останется на CPU.

### 3.2 Максимальный `-c` (`n_ctx`) при `g = L + 1`

```
свободно_под_KV = Σ_i ( VRAM_i − margin_i − W_i − RS_i − CB_i(0)·[PP] − DRAFT_i − OVH_i )

n_ctx_max = свободно_под_KV / kv_per_tok_total
где kv_per_tok_total = Σ_{l∈L_attn} kv_per_tok_layer   (Б/токен по всем attn-слоям)

n_ctx_max ← min( ⌊n_ctx_max⌋ , C_train )        # жёсткий потолок обучения
```
Затем **проверить по-картно** (перекос `-ts`): для самой нагруженной карты
`KV_i + всё_остальное_i + margin ≤ VRAM_i`. При гибрид/`-fa off` добавить в
знаменатель член роста `CB` (`≈ slope_CB` из калибровки).

### 3.3 Минимальный тип KV под нужный `n_ctx`

```
bpe_max = ( свободно_под_KV / (n_ctx · Σ_{l∈L_attn}(d_kgqa + d_vgqa)) )
выбрать ближайший снизу из таблицы 1.4 (q8_0 → q5_1 → q4_1 → q4_0).
Можно раздельно: K точнее (q8_0), V грубее (q4_0).
```

### 3.4 Балансировка `-ts` под равную занятость

Не-весовые буферы (KV, RS, CB, output) тяготеют к старшей/`main` карте. Пусть
при равном `-ts` перекос `Δ = Used_hi − Used_lo`. Перенос доли `δ` весов на
разгруженную карту уменьшает перекос на `≈ 2 · δ · W_repeat`:

```
δ* ≈ Δ / (2 · W_repeat)
ts_lo += δ*·Σts ;  ts_hi −= δ*·Σts        (итерировать: пере-замерить, повторить)
```

---

## 4. Признаки, что слои/операции ушли на CPU (диагностика)

Читать **stdout/stderr** сервера (в `--log-file` этих строк нет). Запускать с
`--verbose` для полной раскладки буферов.

| Признак | Значение |
|---|---|
| `load_tensors: CPU model buffer size = X` c `X` порядка `blk.*` | часть блоков **на CPU** (плохо) |
| `CPU_Mapped model buffer size ≈ W_embed` | только эмбеддинг на хосте — **норма** |
| `offloaded N/M layers to GPU`, `N < M` | не все слои на GPU |
| `sched_reserve: retrying without pipeline parallelism` | compute-буферы не влезли → одна копия CB (медленнее) |
| `ggml_backend_cuda… cudaMalloc failed: out of memory` | не хватило VRAM на буфер |
| `nvidia-smi`: `memory.used ≈ memory.total` | карта под завязку, риск вытеснения |
| prefill (`prompt eval`) падает с сотен tok/s до единиц-десятков | фактическая работа идёт на CPU |

Приоритет ужимания при нехватке (сохраняя `g = L+1`):
`-c` ↓ → `-ctv` грубее → `-ctk` грубее → `-ub` ↓ → (`--n-cpu-moe` для MoE) →
в последнюю очередь `-ngl` ↓.

---

## 5. Чек-лист «максимум VRAM, ничего на CPU»

1. `-ngl ≥ L + 1` (для qwen35: `≥ 65`; ставим `99`).
2. Для каждой карты: `memory.used ≤ memory.total − 512 МиБ` после загрузки.
3. В логе нет `CPU model buffer` по `blk.*`; `offloaded M/M`.
4. В логе нет `retrying without pipeline parallelism` и `cudaMalloc failed`.
5. `prompt eval` в сотнях tok/s (не единицы).
6. Карты сбалансированы (`|Used_0 − Used_1|` ≲ 1 ГиБ) — иначе правим `-ts` (§3.4).
7. Контекст = `min(желаемый, C_train)`; если `< желаемого` — ужимаем KV (§3.3).

---

## 6. Калибровка — `Qwen3.5-27B` (`arch=qwen35`) на 2× RTX 5060 Ti 16 ГБ

Все числа сверены с `llama-server --verbose` (Q4_K_M, `-c 262144`, `-ts 17,13`,
`-ctk q8_0 -ctv q8_0`, `-ub 256`, `-b 1024`, `-kvu`, `-fa on`,
`--spec-type draft-mtp`, `-ngl 99`).

### 6.1 Параметры модели (из `print_info:`)

```
L=64   L_attn=16 (каждый 4-й слой: 3,7,…,63)   L_rec=48
d=5120   n_head=24   n_kv=4   dh_k=dh_v=256   d_kgqa=d_vgqa=1024
n_ff=17408   n_expert=0   n_swa=0   V=248320   C_train=262144
SSM: d_conv=4  d_inner=6144  d_state=128  n_group=16
N_par=27.32 B   file=15.32 ГиБ  →  bpw=4.82
GGUF: Q4_K_M 16 464 440 224 Б (15.33 ГиБ) · Q5_K_M 19 771 509 664 (18.41) · Q6_K 23 088 409 504 (21.50)
mmproj-F16 927 607 488 Б (0.86 ГиБ) — не грузится (--no-mmproj)
VRAM_i = 16311 МиБ ×2   P = 2 (pipeline parallelism, без NVLink)
```

### 6.2 KV-кэш — формула против замера

```
kv_per_tok_total = 2 · L_attn · n_kv · dh · bpe(q8_0)
                 = 2 · 16 · 4 · 256 · 1.0625  = 34 816 Б/токен
KV_total(262144) = 34 816 · 262144 / 1048576 = 8704.0 МиБ
```
Лог: `llama_kv_cache: size = 8704.00 MiB (262144 cells, 16 layers, 1/1 seqs),`
`K (q8_0): 4352.00 MiB, V (q8_0): 4352.00 MiB` — **точное совпадение**.
Делёж по картам (`-ts 17,13` → 9 attn-слоёв на CUDA0, 7 на CUDA1):
`KV_0 = 9/16·8704 = 4896`, `KV_1 = 7/16·8704 = 3808` МиБ.

Для `q4_0/q4_0`: `kv_per_tok = 18 432 Б` → `KV(262144) = 4608 МиБ`.

### 6.3 Рекуррентное состояние — против замера

Лог: `llama_memory_recurrent: size = 598.50 MiB (1 cells, 64 layers, 1 seqs
3 rs_seq), R (f32): 22.50 MiB, S (f32): 576.00 MiB`;
`CUDA0 RS buffer size = 361.59`, `CUDA1 RS buffer size = 236.91`.
→ **фиксированные ~599 МиБ**, от `n_ctx` не зависят. `rs_seq = 3` — эффект MTP
(держит 3 копии состояния). На слой: `S ≈ 576/48/3 = 4.0 МиБ` (f32),
`R ≈ 0.156 МиБ` — сверяется со структурной формулой §2.3 с точностью ~30 %
(gated-delta ≠ чистый Mamba2; для точности берём число из лога).

### 6.4 Compute-буфер — против замера

Лог (target-граф, `graph nodes = 4279`):
`CUDA0 compute buffer size = 1597.09`, `CUDA1 = 1597.09`,
`CUDA_Host = 523.10` МиБ.
Draft-граф (MTP, `graph nodes = 50`): `CUDA1 += 613.03`, `CUDA_Host += 537.04`.
→ на GPU суммарно `CB ≈ 2·1597 + 613 ≈ 3807 МиБ` при `ub=256`, `-fa on`.
`CB ∝ ub`: при `ub=512` ждать ~вдвое больше (это и выбивало pipeline
parallelism на ранних итерациях).

### 6.5 Веса и overhead

```
Лог: offloaded 66/66 layers to GPU ;  CPU_Mapped model buffer size = 682.03 МиБ
  (≈ token_embd: V·d·~4.3bpw/8 ≈ 700 МиБ — на хосте, это норма)
W_на_GPU ≈ 15.33 ГиБ − 682 МиБ ≈ 15 005 МиБ ; делёж ~ ts 17:13
```
Суммарно по замеру `nvidia-smi` при `-c 262144 / -ts 17,13`:
**CUDA0 14 914 МиБ, CUDA1 14 658 МиБ** (Σ = 29 572), запас ~1.4 / 1.6 ГиБ.

Сверка компонентов (Σ по картам, МиБ):
`W 15 005 + KV 8704 + RS 599 + CB_gpu 3807 + output 1 = 28 116`;
остаток до 29 572 ≈ **1456 МиБ** — overhead CUDA/cuBLASLt (~730/карту).

### 6.6 Быстрая эмпирическая модель (окно n_ctx ≈ 180k…262k)

По 4 замерам пробы (Σ used, МиБ): 212992→27076, 229376→27908, 245760→28740,
262144→29594. Линейно:

```
Used_Σ(МиБ) ≈ 16 166  +  0.05123 · n_ctx        (только для 180k ≤ n_ctx ≤ 262k)
             ├─ KV-часть наклона  = 34816/1048576 = 0.03320 МиБ/ток
             └─ рост CB (гибрид)  ≈ 0.018 МиБ/ток
```
Проверка: `16 166 + 0.05123·262144 ≈ 29 594` ↔ замер 29 594. ✔
Вне окна (малый контекст) `CB` не убывает линейно — пользоваться покомпонентным
методом §2, а этой формулой только для прикидки у потолка.

### 6.7 Обратная задача для стенда

```
свободно_под_KV = Σ_i(VRAM_i − margin − W_i − RS_i − CB_i·P − DRAFT_i − OVH_i)
 ≈ 2·16311 − 2·512 − 15005 − 599 − 3807 − 0 − 1456
 ≈ 32622 − 1024 − 20867  ≈ 10 731 МиБ
n_ctx_max ≈ 10 731·1048576 / 34 816  ≈ 323 000  →  min(323000, C_train=262144)
```
Вывод: при `q8_0/q8_0` стенд упирается в **`C_train = 262144`**, а не в VRAM
(что и подтвердила проба — все ступени до 262144 прошли на GPU).
Для `q4_0/q4_0` знаменатель 18 432 Б → `n_ctx_max ≈ 610 000` → тоже потолок 262144.

### 6.8 Прикидка для Q5_K_M / Q6_K

`W_model` растёт на `+3.08 / +6.17 ГиБ` относительно Q4_K_M
(18.41 / 21.50 vs 15.33 ГиБ). Свободный член модели §6.6 растёт примерно на
столько же: `B(Q5) ≈ 16 166 + 3154 ≈ 19 320`, `B(Q6) ≈ 16 166 + 6318 ≈ 22 484`.

```
n_ctx_max(KV=q8_0/q8_0) ≈ (Σ VRAM − 2·margin − B) / 0.03320
 Q5_K_M: (32622 − 1024 − 19320)/0.03320 ≈ 370 000  → потолок 262144, запас мал
 Q6_K:   (32622 − 1024 − 22484)/0.03320 ≈ 275 000  → 262144 «впритык»
```
Для Q6_K безопаснее `-ctv q4_0` (знаменатель падает до `~0.0264`, запас растёт)
или `-c 229376`. Проверять по логу (`retrying without pipeline parallelism`).

---

## 7. Псевдокод калькулятора

```python
def vram_budget(model, run, hw):
    p = 2 if (hw.n_gpu > 1 and run.sm == "layer" and not hw.nvlink) else 1
    L_attn = model.L // model.attn_period          # attn_period=1 для dense
    L_rec  = model.L - L_attn

    W_model  = model.file_bytes
    W_embed  = model.V * model.d * model.bpw_embed / 8
    W_output = 0 if model.tied else model.V * model.d * model.bpw_output / 8
    W_repeat = W_model - W_embed - W_output

    kv_per_tok = sum(                                  # Б/токен по attn-слоям
        model.n_kv*model.dh_k*bpe(run.ctk) + model.n_kv*model.dh_v*bpe(run.ctv)
        for _ in range(L_attn))
    n_seq_kv = 1 if (run.kvu or run.np == 1) else run.np
    KV = kv_per_tok * ctx_len_eff(model, run.n_ctx) * n_seq_kv

    RS = L_rec * (conv_state(model) + ssm_state(model)) * run.n_rs   # или из лога
    CB = c_act * run.ub * model.d * 2
    if run.fa == "off":
        CB += run.ub * model.n_head * run.n_ctx * 2
    if model.is_hybrid:
        CB += slope_cb_hybrid * run.n_ctx            # калибр.: qwen35 ≈ 0.018 МиБ/ток·2^20
    DRAFT = draft_cost(run)                           # 0 или из лога
    OVH   = hw.n_gpu * cublas_overhead + output_buf + (model.mmproj if run.mmproj else 0)

    per_gpu = []
    for i in range(hw.n_gpu):
        r = run.ts[i] / sum(run.ts)
        Wi  = W_repeat * r + (W_output if i == run.output_gpu else 0)
        KVi = KV * r_layers(i, L_attn, run.ts)        # округление до целых слоёв
        used = Wi + KVi + RS*r + (CB if p == 2 else CB/hw.n_gpu) + DRAFT*r + OVH/hw.n_gpu
        per_gpu.append(used)
        assert used + hw.margin <= hw.VRAM[i], f"GPU{i}: перелив, part → CPU"
    assert run.ngl >= model.L + 1, "ngl не покрывает все блоки → CPU"
    return per_gpu
```

Обратные задачи (§3) — бинарный поиск по `n_ctx` / `ngl` / `bpe` поверх
`vram_budget()` с проверкой всех `assert`.

---

## 8. Ссылки на артефакты в этом репозитории

- Рабочие конфиги: [configs/llamacpp-qwen38-27-4km.bat](configs/llamacpp-qwen38-27-4km.bat)
  (Q4_K_M, кодинг-конфиг: `-c 196608`, `-ts 17,13`, `q8_0/q8_0`; вмещает и `-c 262144`),
  [configs/llamacpp-qwen38-27-5km.bat](configs/llamacpp-qwen38-27-5km.bat).
- Пояснения по гибридной архитектуре и подбору `-c`/`-ts` — в [README.md](README.md).
