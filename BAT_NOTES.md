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

## vllm/gittensor-qwen38-27-nvfp4-vllm-rtx5060.bat

```text
Recipe: https://github.com/skrodahl/qwen38-27B-dual-rtx5060 (fp8 KV + FlashInfer + MTP k=4).
Differences from the recipe, on purpose:
  --gpu-memory-utilization 0.905, not 0.94: under WSL GPU-PV and the desktop take ~1.4 GiB
    before vLLM starts, 0.95 fails immediately.
  --kv-cache-dtype fp8, not nvfp4: the recipe's nvfp4 numbers come from vLLM 0.32.0rc1.dev100,
    this distro has 0.30.0 where nvfp4 KV is closed on SM120.
  no PYTORCH_CUDA_ALLOC_CONF=expandable_segments (breaks startup inside WSL), no --load-format
    ipc_cache / --api-key (Docker).
--chat-template chat_template-gittensor.jinja = the revision's own template with the reasoning-effort
  check patched: the stock one raises on "high"/"max" and Claude Code (high) got HTTP 400.
The checkpoint is pinned to 0cc2795: later commits have no MTP head, decode falls to ~42 t/s.
--mamba-ssm-cache-dtype bfloat16: neither the recipe nor this repo has quality data for it.
```

## vllm/gittensor-qwen38-27-nvfp4-vllm-rtx5060-no-reasoning.bat

```text
Recipe: https://github.com/skrodahl/qwen38-27B-dual-rtx5060 (fp8 KV + FlashInfer + MTP k=4).
Differences from the recipe, on purpose:
  --gpu-memory-utilization 0.905, not 0.94: under WSL GPU-PV and the desktop take ~1.4 GiB
    before vLLM starts, 0.95 fails immediately.
  --kv-cache-dtype fp8, not nvfp4: the recipe's nvfp4 numbers come from vLLM 0.32.0rc1.dev100,
    this distro has 0.30.0 where nvfp4 KV is closed on SM120.
  no PYTORCH_CUDA_ALLOC_CONF=expandable_segments (breaks startup inside WSL), no --load-format
    ipc_cache / --api-key (Docker).
--chat-template chat_template-gittensor.jinja = the revision's own template with the reasoning-effort
  check patched: the stock one raises on "high"/"max" and Claude Code (high) got HTTP 400.
The checkpoint is pinned to 0cc2795: later commits have no MTP head, decode falls to ~42 t/s.
--mamba-ssm-cache-dtype bfloat16: neither the recipe nor this repo has quality data for it.
No-reasoning variant of gittensor-qwen38-27-nvfp4-vllm-rtx5060.bat. Only two flags differ, and
  the KV/backend half is unchanged on purpose, so every measurement in CLAUDE.md for the base
  script still applies (pool 283,722 tokens at 262144, prefill 2955 t/s at 33k / 1755 t/s at 111k).
--default-chat-template-kwargs is the lever, not an edit to the template: the same merged dict
  also feeds the reasoning parser, so with enable_thinking=false the template emits a closed empty
  <think></think> (chat_template-gittensor.jinja:300) AND the parser starts in CONTENT state.
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

## vllm/gittensor-qwen38-27-nvfp4-vllm-rtx5060-no-reasoning-test.bat

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

## vllm/gittensor-qwen38-27-nvfp4-vllm-rtx5060-no-reasoning-test2.bat

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

## vllm/gittensor-qwen38-27-nvfp4-vllm-rtx5060-reasoning-test2.bat

```text
Copy of gittensor-qwen38-27-nvfp4-vllm-rtx5060-no-reasoning-test2.bat with thinking ON, so the
  harness can pick the reasoning level. Its CC Switch provider config is in CC-Switch.md
  (reasoning true, reasoningEfforts ["low","medium","high"]). Every engine flag (PIECEWISE, fp32 mamba, fp8 KV,
  MTP k=4, 262144, pool 269,385 tokens) is -test.bat's and documented there. Two lines differ:
--default-chat-template-kwargs {"enable_thinking":true,"preserve_thinking":true}. Both are the
  template's own defaults (chat_template-gittensor.jinja:16-17); spelled out so the intent is
  visible. preserve_thinking keeps <think> in past assistant turns, so the prefix is not
  rewritten and the prefix cache keeps hitting.
  The level is the request's reasoning_effort, normalised by the patched block at
  chat_template-gittensor.jinja:103-120:
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
