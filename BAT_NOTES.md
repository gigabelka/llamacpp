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
  identifiers, boilerplate) are normal, and 0.7/0.80 already suppress looping - which the 2026-10-28
  agentic run confirms by contrast: the -fast variant at temperature 0.3 looped, this one did not
  (see the -fast section). The 1.5 itself is still untested.
```

## vllm/gittensor-qwen38-27-nvfp4-vllm-rtx5060-no-reasoning-fast.bat

```text
Tuned variant of gittensor-qwen38-27-nvfp4-vllm-rtx5060-no-reasoning.bat. The context half is
  untouched on purpose (--max-model-len 262144, fp8 KV, FlashInfer, --revision 0cc2795, k=4), so
  the pool still covers a full 262144-token request. Two lines differ from the base script, both
  measured 2026-10-28 on free cards (--host 0.0.0.0 was used for the bench only, not here).

1) NO --compilation-config: the base script forces cudagraph_mode=PIECEWISE (from the reference
   recipe), which throws away full-graph decode for nothing. FlashInfer reports UNIFORM_BATCH on
   SM120 (xqa, head_dim 256, GQA 24/4) and so do the GDN/mamba backends, so the default
   FULL_AND_PIECEWISE survives the spec-decode check and captures FULL graphs at
   uniform_decode_query_len = k+1 = 5. That matters here because the log says "Fused multi-step
   draft decode is not supported by FLASHINFER; falling back to rebuilding attention metadata
   between draft steps" - 4 draft steps per token, so per-launch overhead is what full graphs cut.
   Measured (code prompt, 1000 tokens, greedy): 83.9 / 83.2 t/s against 75.2 / 77.5 on PIECEWISE;
   4000 tokens at temp 0.7: 84.7 against 74.7 t/s. Prefill unchanged (2712 vs 2752 t/s at 44.5k).
   Cost: graph capture takes 3196 tokens of the pool (283,722 -> 280,526) and ~45 s of startup.
2) NO --mamba-cache-dtype / --mamba-ssm-cache-dtype bfloat16: config.json declares
   mamba_ssm_dtype float32 and nothing in this repo or the reference has quality data for bf16
   (NVIDIA report accuracy loss from quantising the mamba cache), so this is the one accuracy
   lever that costs no context. Measured: pool 266,488 tokens, "Maximum concurrency for 262,144
   tokens per request: 1.02x", nvidia-smi 15587 / 15568 MiB, decode unchanged (4000 tokens at
   temp 0.7: 87.4 t/s). It eats the headroom, so --max-num-batched-tokens can NOT be raised any
   more (see below) and needle was re-run because of it: found at ~120k and ~245k tokens.
--override-generation-config: temperature 0.7 / top_p 0.80 - the card's general non-thinking set,
  identical to the base script. It was 0.3 / 0.95 until 2026-10-28 on the theory that for code a
  low temperature is both more accurate and faster (MTP acceptance was 78-90 % on code prompts).
  That is REVERTED and must not come back: with presence_penalty 0.0 and repetition_penalty 1.0
  there is nothing to break a repetition cycle, and on a long agentic task 0.3 collapsed into
  degenerate generation. Measured on the benchmark in c:\MyProjecs\la2-hf-headless-client-llm-testing
  (generate an L2 client from one prompt; transcript
  c:\Users\viktor\.claude\projects\c--MyProjecs-la2-hf-headless-client-llm-testing\b7c8eae1-5f52-4adc-ae3e-ede0e4434ddd.jsonl):
  the run was clean through gate 1 (12/12), tsc clean and the first npm run dev, then after a large
  hexdump tool result it emitted SEVEN consecutive replies of exactly 16384 output tokens with
  stop_reason max_tokens and NOT ONE tool call, input_tokens frozen at ~177,700 for ~30 minutes,
  the text degenerating into endless runs of "00000000"; two replies died with "response exceeded
  the 16384 output token maximum" and one earlier Write was cut mid-JSON (InputValidationError).
  Same run drifted off its instructions: answered in English against a CLAUDE.md that demands
  Russian, and spawned no subagent at all (0 Agent/Task calls, 25 Writes by hand) where the base
  script at 0.7 / 0.80 finished the same task in ~1 h 20 min with subagents. The perf half of this
  script (FULL_AND_PIECEWISE, mamba fp32) is NOT implicated and stays.
  Note the old claim here was wrong: /v1/messages does forward a client's temperature / top_p /
  top_k (entrypoints/anthropic/serving.py:477-491), but Claude Code sends NONE of them - an
  api-request in that transcript carries only model, betas, max_tokens, thinking,
  context_management and output_config (0 occurrences of "temperature"/"top_p"/"top_k" in the whole
  file, Claude Code 2.1.312). So --override-generation-config is what the model actually runs on.
presence_penalty 0.0, not the card's 1.5: in code the repeated tokens it attacks (indentation,
  identifiers, boilerplate) are normal. repetition_penalty 1.0 as in the base script.

Measured and REJECTED (do not re-add):
  temperature 0.3 / top_p 0.95  repetition collapse and instruction drift on a long agentic task,
                            see the --override-generation-config paragraph above. 0.7 / 0.80 stays.
  --max-num-seqs 1          decode 66.9-69.4 t/s greedy against 78.7-83.9 with 2. Worse.
  --max-num-batched-tokens 8192  engine refuses to start: activations eat the KV pool,
                            "estimated maximum model length is 256096" < 262144. 4096 stays.
  MTP k=3                   greedy 79.4 t/s mean against 81.9 at k=4; 4000 tokens 75.4 vs 84.7.
  flashinfer autotune on    within noise (greedy 82.9-84.9 vs 83.2-83.9) for +80 s of startup
                            (init engine 147 s against 65 s). --no-enable-flashinfer-autotune stays.
Closed by the build / the checkpoint, not worth re-opening:
  fp8 KV runs on UNIT scales here (kv_cache_scheme is static fp8 but the checkpoint ships no
  k_scale/v_scale -> "Using KV cache scaling factor 1.0", "uncalibrated q_scale"). There is no
  --calculate-kv-scales in vLLM 0.30.0, fp8_per_token_head (dynamic scales) is declared only by
  TRITON_ATTN (triton_attn.py; FlashInfer's list is auto/float16/bfloat16/fp8/fp8_e4m3/fp8_e5m2/
  nvfp4/nvfp4_4over6, flashinfer.py:414-423) and Triton costs 3.7x of prefill, and bf16 KV halves
  the pool to ~142k, i.e. it breaks 262144. Weights: this checkpoint has attention AND lm_head in
  NVFP4 (lm_head.weight_scale_2 in the index; quantization_config.ignore covers only embed_tokens,
  the linear_attn conv1d/in_proj, model.visual* and mtp*), so weight precision is a property of
  the checkpoint - only a different one (unsloth/ukisai: FP8 attention + lm_head) would change it,
  and those need int4 KV at 262144.
VLLM_ALLOW_LONG_MAX_MODEL_LEN is NOT passed: max_position_embeddings is 262144, so it allows
  nothing and only silences a real check.
Everything else is the base script's and documented there: the 0cc2795 pin (later commits have no
  MTP head), fp8 KV instead of nvfp4 (gated on SM120 in 0.30.0), --gpu-memory-utilization 0.905
  (WSL ceiling), the four WSL variables, the patched chat template, and
  --default-chat-template-kwargs enable_thinking:false as the single no-reasoning lever (the same
  merged dict also feeds --reasoning-parser qwen3, so the parser starts in CONTENT state; a client
  sending chat_template_kwargs {"enable_thinking": true} wins the merge and gets thinking back).
For maximum accuracy use the thinking script instead: gittensor-qwen38-27-nvfp4-vllm-rtx5060.bat.
```
