# Daftar Model Bawaan SlashAI

Aplikasi memakai daftar ini sebagai fallback untuk **Online AI Insight** ketika endpoint `GET https://api.slashai.my.id/v1/models` tidak tersedia atau gagal dibaca. Request chat tetap memakai format:

```text
POST https://api.slashai.my.id/v1/chat/completions
Authorization: Bearer <your-key>
Content-Type: application/json
model: slashai/<nama-model>
```

Body juga memuat field:

```json
{"model": "slashai/gpt-5.5-instant"}
```


## Endpoint Default

Aplikasi disetel untuk memakai endpoint kompatibel OpenAI berikut secara default:

```text
POST https://api.slashai.my.id/v1/chat/completions
Authorization: Bearer <your-key>
Content-Type: application/json
model: slashai/<nama-model>
```

Pengguna tetap dapat mengganti API Base URL jika memakai gateway kompatibel lain.

## Rekomendasi Cepat

- **Auto pilih model hemat biaya**: `slashai/gpt-5.5-instant`
- **Auto pilih model kualitas tinggi**: `slashai/gpt-5.5`
- **Manual yang kuat untuk tulisan akademik**: `slashai/claude-sonnet-4.7`, `slashai/gpt-5.4-pro`, `slashai/gemini-3.1-pro`

## Claude

- `slashai/claude-haiku-4.5`
- `slashai/claude-opus-4.5`
- `slashai/claude-opus-4.6`
- `slashai/claude-opus-4.7`
- `slashai/claude-sonnet-4.5`
- `slashai/claude-sonnet-4.6`
- `slashai/claude-sonnet-4.7`

## GPT / Codex

- `slashai/gpt-5-codex`
- `slashai/gpt-5-codex-mini`
- `slashai/gpt-5-codex-mini-review`
- `slashai/gpt-5-codex-review`
- `slashai/gpt-5-mini`
- `slashai/gpt-5-nano`
- `slashai/gpt-5.1`
- `slashai/gpt-5.1-codex`
- `slashai/gpt-5.1-codex-max`
- `slashai/gpt-5.1-codex-max-review`
- `slashai/gpt-5.1-codex-mini`
- `slashai/gpt-5.1-codex-mini-high`
- `slashai/gpt-5.1-codex-mini-high-review`
- `slashai/gpt-5.1-codex-mini-review`
- `slashai/gpt-5.1-codex-review`
- `slashai/gpt-5.1-review`
- `slashai/gpt-5.2`
- `slashai/gpt-5.2-codex`
- `slashai/gpt-5.2-codex-review`
- `slashai/gpt-5.2-review`
- `slashai/gpt-5.3-codex`
- `slashai/gpt-5.3-codex-high`
- `slashai/gpt-5.3-codex-high-review`
- `slashai/gpt-5.3-codex-low`
- `slashai/gpt-5.3-codex-low-review`
- `slashai/gpt-5.3-codex-none`
- `slashai/gpt-5.3-codex-none-review`
- `slashai/gpt-5.3-codex-review`
- `slashai/gpt-5.3-codex-spark`
- `slashai/gpt-5.3-codex-spark-review`
- `slashai/gpt-5.3-codex-xhigh`
- `slashai/gpt-5.3-codex-xhigh-review`
- `slashai/gpt-5.4`
- `slashai/gpt-5.4-mini`
- `slashai/gpt-5.4-nano`
- `slashai/gpt-5.4-pro`
- `slashai/gpt-5.4-review`
- `slashai/gpt-5.5`
- `slashai/gpt-5.5-instant`
- `slashai/gpt-5.5-review`

## DeepSeek

- `slashai/deepseek-3.2`
- `slashai/deepseek-v3.2`
- `slashai/deepseek-v4-flash`
- `slashai/deepseek-v4-pro`

## Gemini

- `slashai/gemini-3-flash`
- `slashai/gemini-3.1-pro`

## Kimi

- `slashai/Kimi-K2.5`
- `slashai/Kimi-K2.6`

## Qwen

- `slashai/qwen3-coder-next`
- `slashai/Qwen3.6-Max-Preview`
- `slashai/Qwen3.6-Plus`

## GLM

- `slashai/GLM-5`
- `slashai/GLM-5.1`

## MiniMax

- `slashai/MiniMax-M2.5`
- `slashai/MiniMax-M2.7`

## MiMo

- `slashai/mimo-v2-flash`
- `slashai/mimo-v2-omni`
- `slashai/mimo-v2-pro`
- `slashai/mimo-v2.5`
- `slashai/mimo-v2.5-pro`

## Step

- `slashai/Step-3.5-Flash`

## Catatan akses/deposit

Jika API menolak request dengan pesan `Deposit required to unlock pre`, itu bukan berarti API key pasti salah. Biasanya akun/provider belum membuka akses untuk model tertentu. Coba lakukan deposit/top up pada provider atau pilih model lain yang lebih ringan, misalnya `slashai/gemini-3-flash` atau `slashai/deepseek-v4-flash`.
