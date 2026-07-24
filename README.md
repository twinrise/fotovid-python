# fotovid

[![PyPI](https://img.shields.io/pypi/v/fotovid)](https://pypi.org/project/fotovid/)

Typed Python SDK for the [Fotovid](https://fotovid.co) media API — a serverless
ffmpeg API for watermarking video and images, trimming video and audio,
extracting audio from video, generating video thumbnails, and probing video
metadata. POST a source URL, get back the finished file over one HTTPS call,
with **zero dependencies** (standard library only — no ffmpeg binary, nothing
native to compile).

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
print(result.url)  # hosted, time-limited URL — see expires_at, store your own copy
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

## Async (large or long video)

The sync methods above reject video over ~720p or 15s with a 400 asking you to
use the async endpoint (a hard limit — the sync API has a short time budget).
For a large video watermark, a long trim, or anything you don't need back in a
couple of seconds, submit a task instead and poll for the result:

```python
import time

# A vertical / large video like this is rejected by the sync endpoint.
task = client.tasks.video.watermark(
    source_url="https://cdn.example.com/1080x1920.mp4",
    watermark_type="image",
    watermark_image_url="https://cdn.example.com/logo.png",
)

while not task.is_terminal:
    time.sleep(2)
    task = client.tasks.get(task.id)

if task.status == "succeeded":
    # [TaskOutput(kind="video", url="...")] — read by kind, order not guaranteed
    print(task.outputs)
else:
    # TaskError(code, message, request_id, detail) — not an exception, just data
    print(task.error)
```

`client.tasks.*` mirrors the sync methods 1:1 (`tasks.video.watermark`,
`tasks.video.trim`, `tasks.video.extract_audio`, `tasks.video.thumbnail`,
`tasks.image.watermark`, `tasks.audio.trim`) plus the low-level
`tasks.create`/`tasks.get`. There's no built-in polling helper — the loop
above is the whole pattern. `probe` has no async form; it's sync-only.

## Sync vs async

| | Sync (`client.video.*`, …) | Async (`client.tasks.*`) |
| --- | --- | --- |
| Returns | Finished result, same call | A `Task` — poll `tasks.get` until terminal |
| Limits | ~720p / 15s | 4K / 600s |
| Use for | Small/short media, need the result now | Large video, long clips, batch/background jobs |

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

The same applies to `client.tasks.*` — pass `idempotency_key` there too (it
travels in the request body, not a header, but the client handles that
difference for you).

## Errors

A non-2xx response raises `FotovidError` (`status`, `detail`, `retry_after`).
For `client.tasks.*`, that's the only thing that raises — a task that finishes
as `"failed"` is a normal return value, not an exception; check `task.error`.

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
