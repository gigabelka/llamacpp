# Комментарии к .bat-скриптам

Комментарии из `.bat` вынесены сюда: в самих скриптах `REM` / `::` не пишем (см. «Editing conventions» в `CLAUDE.md`).
Один раздел на скрипт, заголовок — `## <путь к файлу>`; текст дословный, на английском, как был в скрипте.
Новый скрипт — новый раздел; переименовали или удалили скрипт — переименуйте или удалите раздел.

## vllm/ukisai-swift15-qwen38-27-nvfp4-vllm.bat

```text
ModelOpt MIXED_PRECISION checkpoint (NVFP4 + FP8), pinned to the snapshot in the HF cache.
KV stays int4_per_token_head + TRITON_ATTN: the checkpoint has no kv_cache_scheme and no KV scales,
  and the model card forbids fp8/nvfp4 KV without them. int4 here uses dynamic per-token-head scales.
--dtype bfloat16 is from the model card. mamba SSM state stays at the checkpoint's float32 (the default).
The model card says full NVFP4 generation was not tested by the authors: not measured on this bench.
VLLM_DISABLED_KERNELS: for ModelOpt FP8 layers vLLM picks FlashInferFP8ScaledMMLinearKernel, whose JIT gemm module
  links -lcublas -lcublasLt; the venv has only libcublas.so.13 (nvidia/cu13/lib), so ld fails and the engine dies in
  profile_run. Disabling it falls back to CutlassFP8ScaledMMLinearKernel, the one the unsloth checkpoint runs on.
```

## gittensor/gittensor-qwen38-27-nvfp4-vllm-rtx5060.bat

```text
Recipe: https://github.com/skrodahl/qwen38-27B-dual-rtx5060 (fp8 KV + FlashInfer + MTP k=4).
Differences from the recipe, on purpose:
  --gpu-memory-utilization 0.905, not 0.94: under WSL GPU-PV and the desktop take ~1.4 GiB
    before vLLM starts, 0.95 fails immediately.
  --kv-cache-dtype fp8, not nvfp4: the recipe's nvfp4 numbers come from vLLM 0.32.0rc1.dev100,
    this distro has 0.30.0 where nvfp4 KV is closed on SM120.
  no PYTORCH_CUDA_ALLOC_CONF=expandable_segments (breaks startup inside WSL), no --load-format
    ipc_cache / --api-key (Docker).
--chat-template gittensor/chat_template-gittensor.jinja = the revision's own template with the reasoning-effort
  check patched: the stock one raises on "high"/"max" and Claude Code (high) got HTTP 400.
The checkpoint is pinned to 0cc2795: later commits have no MTP head, decode falls to ~42 t/s.
--mamba-ssm-cache-dtype bfloat16: neither the recipe nor this repo has quality data for it.
```

## gittensor/gittensor-qwen38-27-nvfp4-vllm-rtx5060-no-reasoning.bat

```text
Recipe: https://github.com/skrodahl/qwen38-27B-dual-rtx5060 (fp8 KV + FlashInfer + MTP k=4).
Differences from the recipe, on purpose:
  --gpu-memory-utilization 0.905, not 0.94: under WSL GPU-PV and the desktop take ~1.4 GiB
    before vLLM starts, 0.95 fails immediately.
  --kv-cache-dtype fp8, not nvfp4: the recipe's nvfp4 numbers come from vLLM 0.32.0rc1.dev100,
    this distro has 0.30.0 where nvfp4 KV is closed on SM120.
  no PYTORCH_CUDA_ALLOC_CONF=expandable_segments (breaks startup inside WSL), no --load-format
    ipc_cache / --api-key (Docker).
--chat-template gittensor/chat_template-gittensor.jinja = the revision's own template with the reasoning-effort
  check patched: the stock one raises on "high"/"max" and Claude Code (high) got HTTP 400.
Model path /mnt/c/Qwen3.8-27B-NVFP4-RTX5090 (Windows c:\Qwen3.8-27B-NVFP4-RTX5090\), not the HF id,
  so no --revision. That folder holds a LATER build of the repo (2 shards, 17.9 GB) whose MTP head was
  removed upstream; the head was grafted back on 2026-11-08 from revision 0cc2795:
  - model-mtp.safetensors = the 15 mtp.* tensors (bf16, 849,398,784 B of data) cut by HTTP Range out of
    0cc2795's model-00002/00003-of-00003.safetensors; byte spot-checks against HF matched;
  - config.json and hf_quant_config.json replaced by 0cc2795's own files - against the folder's
    originals they differ ONLY in mtp_num_hidden_layers 1, mtp_use_dedicated_embeddings false and the
    "mtp*" / "mtp.layers.0*" quantization excludes;
  - model.safetensors.index.json: 15 mtp.* -> model-mtp.safetensors entries, total_size and
    total_parameters raised accordingly. The untouched originals sit next to them as *.orig.
  Without the head --speculative-config.method mtp cannot start and decode falls to ~42 t/s.
  Measured once, 2026-11-08, on the rebuilt `vllm` distro, cards free: weights 40.8 s + MTP head
  10.3 s from /mnt/c, init engine 380 s cold (40.6 s compile; first flashinfer JIT), KV 4.88 GiB/card,
  pool 269,385 tokens (1.03x of 262144). One ~605-token code reply: 70 t/s wall, MTP mean acceptance
  length 4.16, draft acceptance 79.1 %, per-position 0.943 / 0.830 / 0.730 / 0.660 - the grafted head
  fits the later body. One sample, not an A/B. If acceptance ever drops to ~0 %, restore the *.orig
  files and drop the two --speculative-config lines.
--mamba-ssm-cache-dtype bfloat16: neither the recipe nor this repo has quality data for it.
No-reasoning variant of gittensor-qwen38-27-nvfp4-vllm-rtx5060.bat. Only two flags differ, and
  the KV/backend half is unchanged on purpose, so every measurement in CLAUDE.md for the base
  script still applies (pool 283,722 tokens at 262144, prefill 2955 t/s at 33k / 1755 t/s at 111k).
--default-chat-template-kwargs is the lever, not an edit to the template: the same merged dict
  also feeds the reasoning parser, so with enable_thinking=false the template emits a closed empty
  <think></think> (gittensor/chat_template-gittensor.jinja:300) AND the parser starts in CONTENT state.
  Without it the whole answer would land in "reasoning" with an empty "content". The request wins
  the merge, so a client sending chat_template_kwargs {"enable_thinking": true} gets thinking back
  - which is why --reasoning-parser qwen3 stays. Side effect: the reasoning-effort block is skipped
  entirely, so neither the xhigh preamble nor an HTTP 400 on "high"/"max" is reachable here.
presence_penalty 0.0, not the card's 1.5: in code the repeated tokens it attacks (indentation,
  identifiers, boilerplate) are normal. Measured 2026-11-07 against rep 1.05 / 1.10 and presence
  0.5 / 1.5 (see the -test section): no penalty helped correctness, all of them cost MTP
  acceptance, presence 1.5 was the worst. The 2026-10-28 -fast collapse that once argued for this
  is now attributed to FULL CUDA graphs, not to the sampler (see the -test section).
```

## gittensor/gittensor-qwen38-27-nvfp4-vllm-rtx5060-no-reasoning-test.bat

```text
Test variant of gittensor-qwen38-27-nvfp4-vllm-rtx5060-no-reasoning.bat for coding without
  reasoning. It replaces the deleted -no-reasoning-fast.bat. The context half is untouched
  (--revision 0cc2795, fp8 KV, FlashInfer, --max-model-len 262144, --max-num-seqs 2,
  -batched-tokens 4096, MTP k=4, 0.905, enable_thinking:false). Two lines differ from the base
  script, both measured 2026-11-07 on free cards:
1) NO --mamba-cache-dtype / --mamba-ssm-cache-dtype bfloat16 -> the checkpoint's own
   mamba_ssm_dtype float32. This is the one accuracy lever that costs no context: nothing here or
   in the reference has quality data for bf16, and NVIDIA report accuracy loss from quantising the
   mamba cache. Pool 283,722 -> 269,385 tokens, so a full 262144-token request still fits.
2) NO VLLM_ALLOW_LONG_MAX_MODEL_LEN: max_position_embeddings is 262144, so it allows nothing and
   only silences a real check.
--compilation-config cudagraph_mode=PIECEWISE STAYS, and this is the main finding. The deleted
  -fast script dropped it for FULL_AND_PIECEWISE (+10 % decode, ~84 vs ~75 t/s). Re-measured with
  this script, FULL graphs CORRUPT THE ENGINE:
    - "CUDA error: unspecified launch failure" on Worker_TP1 (surfacing in
      sampler.apply_staged_writes -> temperature.copy_to_uva, i.e. reported asynchronously), on
      the 1st request of one start and the ~20th of another;
    - a hung worker mid-decode at 187k context ("No available shared memory broadcast block" x4,
      then "RPC call to sample_tokens timed out", EngineDeadError);
    - a degenerate reply on the 187k stress prompt: 8192 tokens of "ductductduct...",
      finish_reason length, zlib ratio 0.002, at the base sampler.
  The same prompts on the unmodified base script (PIECEWISE + bf16 mamba) and on this script with
  PIECEWISE restored (fp32 mamba) gave 0 faults, and the 187k stress prompt answered normally
  (finish stop, 541-989 tokens, code present) in 12 of 12 runs. So FULL graphs are the cause,
  not mamba fp32, not the sampler and not the request's seed. This very likely also explains the
  2026-10-28 la2 collapse on -fast (endless "00000000", max_tokens replies, no tool calls), which
  was blamed on temperature 0.3: -fast ran FULL_AND_PIECEWISE too. Do NOT drop PIECEWISE again.
--override-generation-config: temperature 0.7 / top_p 0.80 / top_k 20 / min_p 0.0 /
  presence_penalty 0.0 / repetition_penalty 1.0 - the card's non-thinking set minus its
  presence_penalty 1.5. Chosen by measurement, 2026-11-07, on this script (PIECEWISE, fp32 mamba).
  Code suite: 12 Python tasks with unit tests (expression evaluator, LRU, topo sort, min window,
  wildcard, roman, duration parser, RLE with escapes, spiral, k-th largest, binary search ...),
  3 seeds each, system prompt "reply with one python block". Stress: one 187,012-token prompt
  (48 KB hexdump, 55 % zero rows, the la2 failure shape) asking for a TypeScript packet splitter,
  max_tokens 8192, 2 runs. Samplers were passed per request, so all rows share one engine start.
    config (only penalties vary)  pass   decode t/s  MTP accept  stress (2 runs)
    presence 0.0 / rep 1.00       28/36    75.7        0.820      2x stop, code ok   <- script
    rep 1.05 (Qwen3-Coder card)   29/36    74.5        0.794      2x stop, code ok
    rep 1.10 (r/LocalLLaMA tip)   30/36    72.5        0.777      2x stop, code ok
    presence 0.5                  29/36    75.4        0.815      2x stop, code ok
    presence 1.5 (Qwen3.8 card)   26/36    75.1        0.793      2x stop, code ok
  Pass rates 26-30/36 are inside noise (sd ~2.4 at n=36); no penalty prevents a loop, because on
  a healthy engine none happened. What penalties do measurably is cost MTP acceptance (rep 1.10:
  -4.3 pp, -4 % decode). presence 1.5 was the worst on correctness (eval_expr 0/3, roman 1/3),
  matching the card's own warning about it. Hence the base set; rep 1.05 / 1.10 and presence
  0.5 / 1.5 are measured and REJECTED - do not re-add without a longer agentic run that shows a
  loop on this (PIECEWISE) engine.
  Claude Code sends no samplers, so this set is what the model actually runs on.
Measured and REJECTED earlier on -fast (still valid, do not re-add): --max-num-seqs 1 (decode
  66.9-69.4 vs 78.7-83.9 t/s), --max-num-batched-tokens 8192 (engine refuses: "estimated maximum
  model length is 256096"), MTP k=3 (slower), flashinfer autotune on (no gain, +80 s startup).
Closed by the build / the checkpoint: fp8 KV runs on unit scales (no k_scale/v_scale in the
  checkpoint, no --calculate-kv-scales in 0.30.0; fp8_per_token_head exists only on TRITON_ATTN,
  3.7x slower prefill; bf16 KV halves the pool and breaks 262144). Attention and lm_head are NVFP4
  in this checkpoint, so weight precision is not a flag.
Everything else is the base script's and documented there.
For maximum accuracy use the thinking script instead: gittensor-qwen38-27-nvfp4-vllm-rtx5060.bat.
A/B against the base -no-reasoning.bat, 2026-11-08, cards free, one start each, same prompts and
  seeds, server-default samplers, wall clock via streaming (TTFT = prefill, rest = decode):
                                         base (bf16 mamba)   -test (fp32 mamba)
    GPU KV cache size / concurrency      283,722 / 1.08x     269,385 / 1.03x
    Available KV, init engine            4.89 GiB, 16.6 s    4.89 GiB, 15.6 s
    code 12x3, 1 stream: per-req decode  78.9 t/s            78.7 t/s
                         MTP accept      0.800               0.799
                         pass            28/36               27/36
    code 12x3, 2 streams: aggregate      138.1 t/s           143.7 t/s
                          per-req decode 76.8 t/s            78.1 t/s
                          MTP accept     0.824               0.839
    prefill 33k (2 runs)                 3044 / 3036 t/s     3029 / 2996 t/s
    prefill 111k (2 runs)                1760 / 1757 t/s     1764 / 1762 t/s
    decode at 99k depth, 512 tok         48.2 / 49.7 t/s     48.8 / 48.9 t/s
    2 x 120k at once: wall               148.7 s             148.2 s
    2 x 138k at once: wall               189.8 s             191.2 s
    preemptions, errors in server log    0, 0                0, 0
  Conclusion: fp32 mamba state costs nothing measurable in speed; every row is inside run-to-run
  noise. The only real difference is the 14,337-token smaller pool.
  Concurrency is bounded by the scheduler, not by the pool. Two long prompts are not prefilled in
  parallel: at 2 x 120k the second prefill runs after the first, and the first request decodes at
  ~3.4 t/s while it does (prefill chunks starve the other stream's decode). At 2 x 138k
  (276k > -test pool, < base pool) the second request waits for the first to finish entirely on
  BOTH scripts, so the base script's larger pool did not buy concurrency there either. On short
  code requests 2 streams give ~1.9x aggregate throughput at almost no per-stream cost.
```

## gittensor/gittensor-qwen38-27-nvfp4-vllm-rtx5060-no-reasoning-test2.bat

```text
Copy of gittensor-qwen38-27-nvfp4-vllm-rtx5060-no-reasoning-test.bat. ONE value differs:
  --override-generation-config temperature 0.4 instead of 0.7. top_p 0.8 / top_k 20 / min_p 0.0 /
  presence_penalty 0.0 / repetition_penalty 1.0 are unchanged. Every engine flag (PIECEWISE,
  fp32 mamba, fp8 KV, MTP k=4, 262144) is -test.bat's and documented there.
The -test.bat sweep covered only the penalties; this one covers temperature and the tail cut.
  Measured 2026-11-07 on free cards, one engine start, samplers passed per request, seeds fixed
  per request (outputs are reproducible: the base config re-run gave byte-identical answers).
  Code: 25 Python tasks with unit tests (the 12 of -test.bat + CSV line parser, Dijkstra with
  path, LIS O(n log n), LCS, signed bigint add, add_months with clamping, Trie with delete/count,
  bracket balance with string literals, in-place rotate, tokenizer, meeting rooms, dict flatten,
  text justification), 5 seeds. Tool: 10 agentic tool-call cases x 5 seeds (right tool, valid
  JSON args, a multi-turn fix after a tool result, a no-tool question, shell quoting, two calls).
  Long: 120-row checkable table, 300+ line Python module, 1500-word prose, max_tokens 8192.
  Stage A, temperature (top_p 0.8, top_k 20), seeds 1000-1004:
    temp   code pass  d vs 0.7 [95% CI]  decode t/s  MTP accept code/long  tool   loops/cuts
    0.20   102/125    +2 [-2,+7]          75.4        0.836 / 0.791        50/50  module 8192 cut once (996 lines, not a loop)
    0.40   101/125    +1 [-6,+7]          75.9        0.829 / 0.790        50/50  0
    0.55   100/125    +0 [-5,+5]          75.9        0.828 / 0.780        50/50  0
    0.70   100/125    base                75.1 (*)    0.812 / 0.782        50/50  0
    0.85   100/125    +0 [-5,+6]          75.2        0.820 / 0.765        50/50  flatten ran away to 4096 tokens
    (*) 73.1 on its first pass (warm-up); 75.1 is the stage-B re-run.
  Stage B, tail cut at temperature 0.7:
    top_p 0.95 / top_k 20   100/125   accept long 0.756   flatten runaway (4096 tokens)
    top_p 0.90 / top_k 20    99/125   accept long 0.775   flatten runaway
    top_p 0.95 / top_k 0     99/125   accept long 0.755   flatten runaway
    top_p 0.80 / top_k 40   100/125   byte-identical to top_k 20 (top_p 0.8 already cuts deeper)
    -> widening the tail buys nothing, costs MTP acceptance and is the only thing besides
       temp 0.85 that produced a runaway reply. top_k is not a lever at top_p 0.8.
  Stage C, new seeds 2000-2004, pooled with stage A (n=250):
    0.70   198/250   accept 0.818   74.3 t/s
    0.40   202/250   accept 0.829   76.0 t/s   +4 [-9,+17]
    0.20   201/250   accept 0.831   75.9 t/s   +3 [-7,+12]
  Stress, the 187,012-token hexdump prompt of -test.bat (DUMP_BYTES 48000), 3 runs each at 0.2,
    0.4 and 0.7: 9/9 finish stop, 447-777 tokens, splitPackets present, no zero runs, 0 engine
    errors. Low temperature did not loop on this (PIECEWISE) engine.
  Verdict: nothing is significantly better than 0.7; 0.4 is chosen because pass, MTP acceptance
    and decode all lean its way (none significantly), with no loop or cut anywhere. 0.2 is as
    good on code but cut a long module at 8192 once, so 0.4 is the safer step. If an agentic
    session ever loops, 0.7 (= -test.bat) is the one-line way back.
min_p is CLOSED by vLLM 0.30, not by measurement: any request with min_p != 0 is rejected with
  HTTP 400 "The min_p and logit_bias sampling parameters are not yet supported with speculative
  decoding". Putting min_p > 0 into --override-generation-config would break every request.
  Keep it 0.0 while MTP is on. top_k 0 (disabled) is accepted.
Not covered: a long multi-turn Claude Code session. The harness is single-turn plus one tool
  round; the sweep shows no regression there, not proof for hour-long agent loops.
```

## gittensor/gittensor-qwen38-27-nvfp4-vllm-rtx5060-reasoning-test2.bat

```text
Copy of gittensor-qwen38-27-nvfp4-vllm-rtx5060-no-reasoning-test2.bat with thinking ON, so the
  harness can pick the reasoning level. Its CC Switch provider config is in CC-Switch.md
  (reasoning true, reasoningEfforts ["low","medium","high"]). Every engine flag (PIECEWISE, fp32 mamba, fp8 KV,
  MTP k=4, 262144, pool 269,385 tokens) is -test.bat's and documented there. Two lines differ:
--default-chat-template-kwargs {"enable_thinking":true,"preserve_thinking":true}. Both are the
  template's own defaults (gittensor/chat_template-gittensor.jinja:16-17); spelled out so the intent is
  visible. preserve_thinking keeps <think> in past assistant turns, so the prefix is not
  rewritten and the prefix cache keeps hitting.
  The level is the request's reasoning_effort, normalised by the patched block at
  gittensor/chat_template-gittensor.jinja:103-120:
    xhigh (also high, max, unknown, absent)  -> "think carefully ... prioritize correctness" preamble
    medium                                   -> no instruction (the model's native thinking)
    low (also minimal)                       -> "keep your thinking brief" preamble
  "none" does NOT turn thinking off - it is unknown and becomes xhigh. The only off switch is
  chat_template_kwargs {"enable_thinking": false} in the request (the request wins the merge;
  the parser follows the same dict). The preamble sits in the system block, so changing the
  level between requests invalidates the prefix cache from position 0.
--override-generation-config temperature 1.0 / top_p 0.95 / top_k 20 / min_p 0.0 /
  presence_penalty 0.0 / repetition_penalty 1.0 - the card's thinking-mode set, as on the base
  gittensor-qwen38-27-nvfp4-vllm-rtx5060.bat. NOT test2's 0.4 / 0.8: that set was tuned with
  thinking off, and lowering the temperature in thinking mode is what sends the model into
  loops inside <think>. min_p stays 0.0 (vLLM 0.30 rejects min_p != 0 with MTP on).
Not measured. MTP k=4 acceptance at temp 1.0 was ~49 % on the base script (bf16 mamba); expect
  decode near its 48-53 t/s, below the ~75 t/s of the no-reasoning test scripts.
```

## gittensor/gittensor-qwen38-27-nvfp4-vllm-rtx5060-mtp-reasoning.bat

```text
Copy of gittensor-qwen38-27-nvfp4-vllm-rtx5060-mtp-no-reasoning.bat with thinking ON (local
  /mnt/c/Qwen3.8-27B-NVFP4-RTX5090 with the grafted MTP head, fp8 KV, FlashInfer, PIECEWISE, fp32 mamba,
  MTP k=4, 262144). Its CC Switch provider config is in CC-Switch.md (reasoning true,
  reasoningEfforts ["low","medium","high"]). Three lines differ: the title and the two below.
--default-chat-template-kwargs {"enable_thinking":true,"preserve_thinking":true}. Both are the
  template's own defaults (gittensor/chat_template-gittensor.jinja:16-17); spelled out so the intent is
  visible. The model card's kwargs table calls preserve_thinking=false "prefix-cache safe"; this repo
  keeps true (old turns keep <think>, the rendered prefix is not rewritten). Not verified either way.
  The level is the request's reasoning_effort, normalised by gittensor/chat_template-gittensor.jinja:103-120:
    xhigh (also high, max, unknown, absent)  -> "think carefully ... prioritize correctness" preamble
    medium                                   -> no instruction (the model's native thinking)
    low (also minimal)                       -> "keep your thinking brief" preamble
  "none" does NOT turn thinking off - it becomes xhigh. The only off switch is chat_template_kwargs
  {"enable_thinking": false} in the request (the request wins the merge; the parser follows the same dict).
--override-generation-config temperature 1.0 / top_p 0.95 / top_k 20 = the model's own generation_config.json
  (the card gives no separate sampler recommendation; its thinking-on smoke test ran at temperature 1.0).
  NOT the no-reasoning 0.7 / 0.8: that set was chosen with thinking off, and lowering the temperature in
  thinking mode is what sends the model into loops inside <think>. min_p 0.0 is mandatory (vLLM 0.30
  rejects min_p != 0 with MTP on); presence_penalty 0.0 / repetition_penalty 1.0 are neutral (penalties
  cost MTP acceptance, see the -test section).
Not measured. MTP k=4 acceptance at temp 1.0 was ~49 % on the old pinned-revision script; expect decode
  well below the ~70-75 t/s of the no-reasoning configs.
```

## gittensor/gittensor-qwen38-27-nvfp4-vllm-rtx5060-mtp-no-reasoning-repro.bat

```text
Copy of gittensor-qwen38-27-nvfp4-vllm-rtx5060-mtp-no-reasoning.bat for byte-identical replies to an
  identical request. Three lines differ: the title, --max-num-seqs 1 (was 2) and temperature 0.6
  (was 0.7, see the sweep at the end). KV, backend, MTP k=4, 262144 are unchanged.
Repeatability needs BOTH halves:
  - the client sends "seed" in every request. The server cannot set it: --override-generation-config
    keeps only repetition_penalty/temperature/top_k/top_p/min_p/max_new_tokens (vllm/config/model.py:1750),
    and the global --seed does not make separate requests repeat. Claude Code sends no seed (and its
    prompt changes every turn), so through Claude Code replies are never repeatable on any config;
  - --max-num-seqs 1, so a second request never shares a batch. On the base script a seeded request
    run alongside another request gave a different reply (stable only because the overlap was).
    Cost: a second request (Claude Code's background calls) waits in the queue.
VLLM_BATCH_INVARIANT=1 (vLLM's "deterministic under any batch" mode) is NOT an option on this model:
  vllm/v1/attention/selector.py:235 raises for a mamba backend without batch-invariance support, and
  GDNAttentionBackend (v1/attention/backends/gdn_attn.py) does not declare it - 48 of 64 layers are GDN.
  It would also cost speed: it disables FlashInfer (Triton attention only, 3.7x slower prefill here),
  forces NCCL to one channel and swaps GEMMs for persistent kernels.
Measured 2026-11-08, cards free, PCIe replays 0, short code prompt, max_tokens 600:
  base script, no seed            5 runs -> 5 different replies
  base script, seed 1234          5 runs -> 1 reply (also at temperature 0)
  base script, seed + concurrent  5 runs -> 1 reply, but different from the solo one
  this script, seed 1234          11 runs (5 solo, 3 with a request queued before, 3 after) -> 1 reply
  A reply repeats only within one config: this script's seeded reply differs from the base script's.
  Decode, 1000 tokens, ignore_eos, 3 runs: 20.1-20.3 s here vs 20.4-20.6 s on the base (~49 t/s both).
  Pool 270 833 tokens (base 269 385). (These rows were taken at temperature 0.7.)
temperature 0.7 -> 0.6, measured 2026-11-08 on this script, cards free, PCIe replays 0 throughout.
  Samplers came from --override-generation-config (requests carried no sampler fields), harness =
  bench3 of the -test2 sweep: 25 code tasks x 5 seeds (1000-1004), 10 tool cases x 5, long x 2.
    temp  code pass  d vs 0.7 [95% CI]  code t/s  MTP accept code/tool/long  tool   cuts / runaways
    0.70   97/125    base                77.0      0.828 / 0.960 / 0.849      50/50  module 8192 once
    0.60  102/125    +5 [-3,+14]         74.1      0.821 / 0.968 / 0.850      50/50  module 8192 once,
                                                                                     flatten ran to 4096 once
  Repeatability at 0.6: no seed 5/5 different; seed 1234 11/11 identical (5 solo, 3+3 with a concurrent
  request), and that reply differs from the 0.7 one - the seeded reply is a function of the samplers.
  Decode, 1000 tokens ignore_eos: 20.9-21.7 s (0.7: 20.1-20.3 s).
  Verdict: no significant difference in either direction. Pass leans to 0.6, speed leans to 0.7
  (-4 % code t/s, acceptance inside noise), and 0.6 produced the only runaway code reply. 0.6 is kept
  as asked; 0.7 is the one-line way back.
presence_penalty in --override-generation-config is a NO-OP: vLLM keeps only repetition_penalty /
  temperature / top_k / top_p / min_p / max_new_tokens (vllm/config/model.py:1750). The startup line
  "Default vLLM sampling parameters have been overridden ... {'repetition_penalty': 1.0, 'temperature':
  0.6, 'top_k': 20, 'top_p': 0.8, 'min_p': 0.0}" shows it missing. 0.0 is vLLM's default anyway, so
  nothing changes here; a non-zero value would have to be sent per request.
```

## gittensor/gittensor-qwen38-27-nvfp4-vllm-rtx5060-dspark-no-reasoning.bat

```text
Same as the MTP no-reasoning config (local /mnt/c/Qwen3.8-27B-NVFP4-RTX5090, fp8 KV, FlashInfer, PIECEWISE,
  enable_thinking:false, samplers 0.7 / 0.8 / 20), except the speculator (DSpark v2 instead of MTP k=4) and the
  window: --max-model-len 139264, not 262144 (see below).
Drafter: gittensor-model-hub/Qwen3.8-27B-DSpark-NVFP4 @ eba1ac5a66c74902eaa95a4000a7c5eda96d8e95 (1.40 GB, one
  model.safetensors; Qwen3DSparkModel, 5 full-attention layers, 8 KV heads x 128, block_size 7, target_layer_ids
  4/16/28/40/52, modelopt NVFP4 with attention q/k/v, fc, markov_head and confidence_head left in bf16).
  Downloaded with the venv's hf download --local-dir /opt/vllm/models/Qwen3.8-27B-DSpark-NVFP4 (ext4, not drvfs).
  The model card's recommended drafter. The BF16 source (Qwen3.8-27B-NVFP4-RTX5090-DSpark, 2.72 GB) returns HTTP 401
  anonymously, so it was not used.
The card gives no vLLM recipe for DSpark, only SGLang (--speculative-algorithm DSPARK --speculative-dspark-block-size 7
  --speculative-draft-model-quantization modelopt_fp4). The vLLM flags come from vLLM 0.30.0 sources:
  method dspark exists (config/speculative.py, models/qwen3_dspark.py), Qwen3DSparkModel is auto-detected,
  parallel_drafting is forced on, and num_speculative_tokens must be given explicitly: 7 = the trained block_size.
  The drafter's quantization comes from its own quantization_config (modelopt).
DSpark speeds up decode only; prefill is unchanged. Card figures (RTX 5090, not this bench): 180 t/s vs 137 t/s for the
  built-in MTP head, accept length 2.90 overall, 3.86 on coding.
The grafted MTP head in the model folder is not used by this script.
The drafter's config is patched (2026-11-08). First start died loading the drafter weights with
  "RuntimeError: The size of tensor a (128) must match the size of tensor b (256) at non-singleton dimension 1"
  (vocab_parallel_embedding.py:507, from qwen3_dspark.py:369). markov_head.markov_w2.weight is BF16 [248320, 256]
  in the checkpoint, but vLLM built it as an NVFP4 ParallelLMHead (packed 256/2 = 128): the modelopt ignore entry
  "markov_head*" does not match the vLLM prefix "model.markov_head.markov_w2" (is_layer_excluded in modelopt.py
  tries exact, literal substring and fnmatch; the x* -> x, x.* rewrite in apply_vllm_mapper is not applied because
  the mapper sits on the inner DFlashQwen3Model). confidence_head* had the same problem. Fix: "*markov_head*",
  "*confidence_head*", "*fc" appended to quantization_config.ignore in config.json (the list vLLM reads) and to
  exclude_modules in hf_quant_config.json; originals kept as config.json.orig / hf_quant_config.json.orig in
  /opt/vllm/models/Qwen3.8-27B-DSpark-NVFP4. Re-apply after any re-download of the drafter.
262144 does not fit (second start, 2026-11-08, cards free): "To serve at least one request with the model's max
  seq len (262144), (6.99 GiB KV cache is needed, which is larger than the available KV cache memory (4.07 GiB) ...
  the estimated maximum model length is 140080". The MTP script has 4.89 GiB available at the same settings; the
  drafter's weights and its own 5-layer KV take the difference, and the log adds "Add 4 padding layers, may waste at
  most 25.00% KV cache memory" and "no KV cache group could be identified as the draft model's". The 2.9 GiB gap is
  far beyond bf16 mamba cache or --max-num-seqs 1 (hundreds of MiB), so the window was cut to 139264 (the repo's
  earlier fp8 profile value, just under the 140080 estimate). If it still fails: --max-num-batched-tokens 2048.
Claude Code on this script: the provider's CLAUDE_CODE_MAX_CONTEXT_TOKENS + CLAUDE_CODE_MAX_OUTPUT_TOKENS must sum to
  <= 139264 (e.g. 106496 + 32768), not the 229376 + 32768 used for the 262144 scripts, or vLLM rejects long requests.
Not measured beyond starting attempts.
```

## strata/run-iq3_s-coding-noreason.bat

Starts Strata through its own launcher, `terminal\current\bin\strata.cmd launch --preset "IQ3_S 200K"`:
the preset starts the model and opens the terminal monitor (Overview, Serving, Requests, Engine,
Hardware, Logs, Connect) that `strata launch` shows. Qwen3.8-Flash-Next IQ3_S on both RTX 5060 Ti,
context 204800, kv int8, DFlash2 alone (--draft-conf 0.35, draft_vocab_en.bin), no reasoning,
sampling 0.6 / 0.8 / 20 / min_p 0 / penalties 0 / seed 1 (README.md sections 3-5).

The parameters come from the installed run config `%LOCALAPPDATA%\Strata\install\strata-iq3_s.json`,
which every `strata launch` uses as its base; `strata/apply_final_config.py` keeps it in sync with
`strata/qwen3.8-flash-next-iq3_s.coding-noreason.json`. That repository copy is documentation for this
launch file (it no longer reads the file itself).

Both paths in the script are absolute on purpose, as in the installer's run-iq3_s.bat. A launcher that
pipes the .bat into cmd.exe (some IDE "run" buttons) never expands `%~dp0`: it reaches the line as the
literal text `%~dp0`, and the call fails before Strata is reached. Moving the repository means editing
the `cd /d` path.

The server is an instance of `strata launch` / `strata runtime`: stop it from the monitor's `q`
("keep serving or stop") or with `strata launch --stop --preset "IQ3_S 200K"`; the second leaves the
monitor window open, close it by hand. Logs:
`...\Local\Strata\launch\iq3_s-200k.engine.log` and `...\Local\Strata\runtime\launch-iq3_s-200k.server.log`.

If the same choices already serve, `strata launch` prints the address and does not open the monitor:
use `strata monitor --url http://127.0.0.1:8080`. If other choices serve, it asks once; without a
screen (a piped launcher) that start refuses, and `--restart` stops the running session first.

No-reasoning needs `strata/patches/apply-no-reasoning.ps1` applied to the installed serve\ files
(strata/README.md section 4). Without the patch, `reasoning_effort: none` only covers requests that
do not ask for thinking; a client that sends `thinking` gets its own level back. Since the patch
became a gate on `STRATA_ALLOW_THINKING` (the reasoning .bat is the only thing that sets it), this
launch keeps the hard off: the variable is unset here. `strata update` does
not touch this .bat, the preset or the installed config, but it does replace serve\: re-run the patch
after an update.

Not benchmarked separately: the `final` run in strata/README.md section 5 is this exact configuration.

## strata/run-iq3_s-coding-noreason.ps1

The PowerShell form of the .bat above: `terminal\current\bin\strata.cmd launch --preset "IQ3_S 200K"`,
so the same preset, the same dashboard and the same parameters (the installed run config
`%LOCALAPPDATA%\Strata\install\strata-iq3_s.json`, kept in sync by `strata/apply_final_config.py`).
The working folder is `$PSScriptRoot`; when PowerShell runs the file from a pipe `$PSScriptRoot` is
empty, and the hard-coded fallback `C:\MyProjecs\llamacpp\strata` is used. Moving the repository means
editing that fallback.

Stop from the monitor's `q` ("keep serving or stop") or with `strata launch --stop --preset "IQ3_S 200K"`;
the second leaves the monitor window open. Logs are the same as the .bat's:
`...\Local\Strata\launch\iq3_s-200k.engine.log` and
`...\Local\Strata\runtime\launch-iq3_s-200k.server.log`.

If the execution policy blocks local scripts, run it as
`powershell -NoProfile -ExecutionPolicy Bypass -File strata\run-iq3_s-coding-noreason.ps1`.
The no-reasoning patch (`strata/patches/apply-no-reasoning.ps1`) is required in the same way as for
the .bat; `strata update` replaces serve\ and the patch must be applied again.

## strata/run-iq3_s-coding-reason.bat

The reasoning twin of the noreason .bat: the same model, engine, context (204800), `kv int8`,
DFlash2 alone (`--draft-conf 0.35`, `draft_vocab_en.bin`), both cards, sampling defaults, but
thinking ON at the template's `xhigh` level and the model-card sampler set
`temperature 1.0 / top_p 0.95 / top_k 20 / min_p 0 / penalties 0 / repetition 1.0 / seed 1`
(strata/README.md section 9).

It does **not** use `strata launch --preset`. The preset (and `strata launch` itself) rebuilds the
engine config from the single installed model config `%LOCALAPPDATA%\Strata\install\strata-iq3_s.json`,
which holds `reasoning_effort: none` and the 0.6/0.8 samplers, so two presets on one model cannot
differ in thinking. Instead the script runs its own run config as a managed background instance and
shows the dashboard in the one console it opens — the same shape `strata launch` has for the preset:

- the saved profile `iq3_s-coding-reason` (`%APPDATA%\Strata\profiles\iq3_s-coding-reason.json`)
  only points at the repository config (`source_config`,
  `strata\qwen3.8-flash-next-iq3_s.coding-reason.json`); the bytes are not copied, so an edit to
  the config is used by the next start. The script creates the profile on the first run
  (`if not exist … profile create …`; `profile create` refuses an existing name, hence the guard).
  When the repository moves, repoint it with
  `strata profile use-config iq3_s-coding-reason --from-config <new path>`;
- `strata runtime start --profile iq3_s-coding-reason --wait 900` starts the owner host without a
  window (`CREATE_NO_WINDOW`) and the server under it; the host inherits the script's environment,
  so `STRATA_ALLOW_THINKING=1` reaches the server process, which is what the patch gate reads
  (strata_control/runtime.py:715-719, 1064). The script prints one "Starting the model..." line,
  then the command waits for the model to load and prints
  `<profile>: ready  instance …  http://127.0.0.1:8080`, or fails with exit 6 (`server_exited` —
  port 8080 taken, a broken engine — or `this profile already has a live managed runtime`) or exit
  8 (the 900 s wait expired, the load goes on; the start itself continues) plus the engine-log
  tail; a bad or missing config/profile is refused earlier as `strata: …` with exit 2 or 5; on any
  failure the script prints the path of the server log and pauses instead of opening a dashboard
  nobody serves. The precise reason for a failed start (for a taken port, `port 8080 is already in
  use - is Strata (or another server) already running?`) is written to that server log, not echoed
  — the console line is `…: failed  server_exited`, followed by the engine-log tail (stale when the
  engine never started, as for a taken port). `--wait` accepts 0..1800 (strata_control/runtime.py MAX_START_WAIT).
  A live instance keeps the environment it was started with, and the script attaches to it rather
  than restarting it (see below), so one started by hand without `STRATA_ALLOW_THINKING` keeps
  serving without thinking until it is stopped. Ctrl+C during the wait only abandons the wait: the
  owner host is detached and finishes starting the model in the background (a later run just opens
  the dashboard against it);
- `strata monitor --url http://127.0.0.1:8080` runs in the script's own console: the same seven
  screens `strata launch` opens (Overview / Serving / Requests / Engine / Hardware / Logs /
  Connect). `--url` is required — the monitor's default address is `http://127.0.0.1:8095`
  (strata_cli/connections.py) and `strata monitor` only discovers `strata launch` sessions.
  Telemetry needs no key here: a local bind is open when the config sets neither `api_key` nor a
  telemetry key (serve/server.py:7458-7466). The start command has already waited for readiness,
  so the monitor connects at once. `q` only detaches — the monitor did not start the server, so
  there is no "keep serving or stop" question (`ask_quit=False`,
  strata_cli/launch/monitor_ext.py:160-161); the server keeps serving and the script's window
  closes. Stop it with `strata runtime stop --profile iq3_s-coding-reason` (drains, then frees both
  cards); `strata runtime status --profile iq3_s-coding-reason` prints `ready`, `failed` or
  `stopped`.

A second run is cheap: before starting anything the script asks
`strata runtime status --profile iq3_s-coding-reason`, and a `ready` or `starting` line goes straight
to `strata monitor` — a double-click while the model is still loading opens the dashboard too, and
only the first run pays the load (`runtime start` would otherwise refuse with `this profile already
has a live managed runtime`). When the start fails and another Strata server already answers on 8080
(the noreason launch, for one), the script adds `Another Strata server already serves
http://127.0.0.1:8080; stop it to start the reason instance.` before the pause.

A piped launcher (an IDE "run" button, no TTY) gets `interactive monitor needs a terminal` from the
monitor (exit 2) and the script pauses on it; start the file from a normal console.

Engine log: `strata\iq3_s-coding-reason.engine.log`. The server's own output (startup lines, request
errors) goes to `%LOCALAPPDATA%\Strata\runtime\iq3_s-coding-reason.server.log`, because the instance
is backgrounded. Only one configuration runs at a time, as before: the reason instance and the
noreason launch share port 8080 and both cards, so they cannot be up together; a server started
while 8080 is taken exits with `address already in use` in its server log, and the script fails at
`runtime start` instead of opening the dashboard against the other server.

The `set` line sets `STRATA_ALLOW_THINKING=1`. The reworked no-reasoning patch
(`strata/patches/apply-no-reasoning.ps1`) reads that variable in both request dialects and passes it
to the template as `strata_allow_thinking`; without it every request renders the closed empty
`<think></think>`, exactly as before this configuration existed. Nothing else sets the variable, so
`strata launch --preset "IQ3_S 200K"`, `install\run-iq3_s.bat` and the noreason .bat keep the hard
no-reasoning behaviour, and the two configurations can be switched by starting one or the other
(they still share port 8080 and both cards, so only one runs at a time).

Run-config keys that matter, on top of the noreason config:
- `reasoning_effort: "high"` - the default level for requests that name none. The config key takes
  `none|low|medium|high` only (`xhigh` is refused at startup by `clean_shared_defaults`); `high`
  maps to the template's `xhigh`, and a request's own `reasoning_effort` / `output_config.effort`
  wins over it.
- `effort_position: "end"` - a request's non-default level is rendered as a short system turn right
  before the answer (`--tail-role-token`), so switching level in a harness does not invalidate the
  cached conversation prefix. The startup log says `effort_position end: ...`.
- `anthropic_thinking` is left at its default. `"on_request"` was tried and removed: with a config
  `reasoning_effort` set, `Service.with_shared` fills `output_config` for every Anthropic request
  that names no thinking, so an unasked request thinks at the config level whatever the key says.
  A client disables thinking per request with `thinking: {"type": "disabled"}` (Anthropic) or
  `reasoning_effort: "off"` (OpenAI).
- The same `args`/`user_args` as the noreason config, so the engine command line is the noreason
  one plus `--tail-role-token`: DFlash2 normalizes `--spec 4 --spec-min-p 0.5` to `--spec 6`, drops
  the MTP layer and the min-p flag, and picks the converted `-selq4` drafter pack when the installed
  engine reads it.

Verified live: `strata serve --plan` reports the same engine argv as the noreason baseline; the
startup log prints `sampling defaults from the config: temperature=1.0, top_p=0.95, ..., seed=1`,
`effort_position end`, `drafting: DFlash2 alone (--draft dflash2, --draft-conf 0.35)` and
`drafting: draft vocabulary: draft_vocab_en.bin`. Run without `STRATA_ALLOW_THINKING` (the same
config, requests asking `reasoning_effort: low` and `xhigh`) it returned `reasoning_tokens: 0`, so
the gate overrides the config level and the request alike. Measurements and the harness provider:
strata/README.md section 9 and CC-Switch.md.

