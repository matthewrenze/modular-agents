# OpenAI
 - gpt-5_2-2025-12-11
 - gpt-5_4-2026-03-05
 - gpt-5_4-mini-2026-03-17 (excluded)
 - gpt-5_5-2026-04-23

# Anthropic
 - claude-sonnet-4-6 (API echoes only the bare id — no dated snapshot; captured in the `model_version` column since P7-03, but this doc remains the provenance anchor)
 - claude-opus-4-6 (same — bare id only)

# Google
 - gemini-3.1-pro-preview (March 9, 2026 release; API echoes only the bare id)

# Fireworks
 - deepseek-v4-pro (`accounts/fireworks/models/deepseek-v4-pro`, 1040k context; verified on model card 2026-07-06)
 - glm-5.1 (DROPPED 2026-07-06 — repetition collapse on long react-kn episodes; completed v6.0 data retained)
 - glm-5.2 (`accounts/fireworks/models/glm-5p2`, 1040k context; verified on model card 2026-07-06)
 - kimi-k2.5 (direct model — replaces the deprecated turbo router for the next full run)
 - kimi-k2.6
 - kimi-k2.7-code (`accounts/fireworks/models/kimi-k2p7-code`, 262k context; verified on model card 2026-07-06)
 - minimax-m3 (`accounts/fireworks/models/minimax-m3`, 512k context; verified on model card 2026-07-06)
 - nemotron-3-ultra (`accounts/fireworks/models/nemotron-3-ultra-nvfp4`, 262k context; serverless serves only the NVFP4-quantized "(Preview)" variant — the BF16 build is on-demand only; verified on model card 2026-07-06)
 - qwen3.7-plus (`accounts/fireworks/models/qwen3p7-plus`, verified live 2026-07-05) (DROPPED 2026-07-06 — repetition collapse on long react-kn episodes; completed v6.0 data retained)
 - qwen3.6-plus (DEPRECATED — not served by Fireworks, `NOT_FOUND` as of 2026-07-05; never ran)
 - glm-5-fast (DEPRECATED — FirePass router 404s as of 2026-07-02; v5.0 data only)
 - kimi-k2p5-turbo (DEPRECATED — FirePass router 404s as of 2026-07-02; v5.0 data only)
