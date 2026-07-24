# fotovid

Typed Python client for the [Fotovid](https://fotovid.co) media API — run
ffmpeg-style operations (watermark, trim, extract audio, thumbnails…) over one
HTTPS call, with **zero dependencies** (standard library only).

## Install

```bash
pip install fotovid
```

## Usage

```python
import os
from fotovid import Fotovid

client = Fotovid(api_key=os.environ["FOTOVID_API_KEY"])

result = client.video.watermark(
    source_url="https://cdn.example.com/clip.mp4",
    watermark_type="image",
    watermark_image_url="https://cdn.example.com/logo.png",
    position="bottom-right",
    opacity=0.8,
)
print(result.url)  # presigned URL to the finished file — store your own copy
```

## Operations

| Method | Endpoint |
| --- | --- |
| `client.video.watermark(...)` | `POST /v1/video/watermark` |
| `client.image.watermark(...)` | `POST /v1/image/watermark` |
| `client.video.trim(...)` | `POST /v1/video/trim` |
| `client.video.extract_audio(...)` | `POST /v1/video/extract-audio` |
| `client.audio.trim(...)` | `POST /v1/audio/trim` |
| `client.video.thumbnail(...)` | `POST /v1/video/extract-cover` |
| `client.video.probe(...)` | `POST /v1/video/probe` |

Parameter names match the API 1:1. Every media operation returns a
`MediaResult` (`id`, `type`, `url`, `expires_at`, `duration`); `probe` returns a
`ProbeResult` with video metadata.

## Idempotency

The billed endpoints require an `Idempotency-Key` header — the client sends a
fresh key per call automatically. To safely retry without being charged twice,
pass the same key both times:

```python
key = "my-unique-key"
client.video.watermark(source_url=url, idempotency_key=key)
# a retry with the same key replays the original result instead of re-charging
client.video.watermark(source_url=url, idempotency_key=key)
```

## Config

```python
Fotovid(
    api_key="p6_<key_id>:<secret>",  # or set FOTOVID_API_KEY
    base_url="https://api.fotovid.co",  # optional
    timeout=60.0,  # optional, seconds
)
```

## License

MIT
