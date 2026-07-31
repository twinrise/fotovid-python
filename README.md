# fotovid

[![PyPI](https://img.shields.io/pypi/v/fotovid)](https://pypi.org/project/fotovid/)

Typed Python SDK for the [Fotovid](https://fotovid.co) media API — a serverless
ffmpeg API for watermarking video and images, trimming video and audio,
extracting audio from video, generating video thumbnails, and probing video
metadata. POST a source URL, get back the finished file over one HTTPS call,
with **zero dependencies** (standard library only — no ffmpeg binary, nothing
native to compile).

**Full docs, guides, and API reference:** [fotovid.co/docs](https://fotovid.co/docs)

## Why Fotovid

- **No ffmpeg to install or maintain.** No binary in your container/Lambda, no
  native build step, no version drift across machines — zero runtime
  dependencies, standard library only.
- **One call, typed end to end.** Parameter names match the API 1:1;
  `MediaResult`/`ProbeResult`/`Task` are dataclasses, nothing to guess.
- **Sync for quick jobs, async for large ones.** Small/short media returns in
  the same call; video over ~720p or 15s goes through the async task API
  instead of failing outright.
- **Idempotent by default.** Every billed call gets a fresh idempotency key
  automatically — retry safely without a double charge.
- **Hosted output.** Every operation returns a URL to the finished file; no
  storage bucket to provision or clean up yourself.

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

## Examples

### Video

```python
# Text watermark, bottom-right corner.
client.video.watermark(
    source_url="https://cdn.example.com/clip.mp4",
    watermark_type="text",
    text="© Acme Inc.",
    position="bottom-right",
)

# Cut a 10s clip.
client.video.trim(source_url="https://cdn.example.com/clip.mp4", start=5, end=15)

# Pull out the audio track as an MP3.
client.video.extract_audio(source_url="https://cdn.example.com/clip.mp4")

# Grab a frame at 2.5s as a thumbnail.
client.video.thumbnail(source_url="https://cdn.example.com/clip.mp4", at=2.5)

# Metadata only — no file produced.
meta = client.video.probe(source_url="https://cdn.example.com/clip.mp4")
print(meta.width, meta.height, meta.duration_sec, meta.fps, meta.codec)
```

### Image

```python
# Logo watermark, scaled to 20% of the source width.
client.image.watermark(
    source_url="https://cdn.example.com/photo.jpg",
    watermark_type="image",
    watermark_image_url="https://cdn.example.com/logo.png",
    scale=0.2,
)
```

### Audio

```python
client.audio.trim(source_url="https://cdn.example.com/track.mp3", start=0, end=30)
```

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

### Your own metadata

Pass `metadata` to tag a task with your own labels. They come back on the `Task`
and in the webhook payload, so a callback can be matched against your records
without a second lookup:

```python
task = client.tasks.video.trim(
    source_url="https://cdn.example.com/clip.mp4",
    start=0,
    end=30,
    metadata={"order_id": "A-1001", "tenant": "acme"},
    webhook="https://example.com/hooks/fotovid",
)

task.metadata  # {"order_id": "A-1001", "tenant": "acme"}
```

The platform never interprets `metadata` — it takes no part in routing, auth,
billing or idempotency. At most 50 keys, keys ≤40 chars (no square brackets),
string values ≤500 chars. Don't put secrets in it: it is returned to anyone who
can read the task and delivered to your webhook endpoint. On an idempotent replay
the stored task's metadata comes back and the one you sent is ignored.

`Task` also echoes `input` back exactly as submitted — the `source_url` plus that task type's params, flattened into one object.

### Breaking in 1.0.0: the `input` envelope

The async wire moved to an `input` envelope. **The typed helpers above are
unchanged** — `tasks.video.watermark(source_url=..., **params)` still takes flat
keyword arguments. Only two things moved:

```python
p = {"start": 0, "end": 30}

# tasks.create — the low-level escape hatch
client.tasks.create(type="video.trim", source_url=url, params=p)  # ❌ 0.x
client.tasks.create(type="video.trim", input={"source_url": url, **p})  # ✅ 1.0

# Task — the two echo fields collapsed into one
task.source_url, task.params  # ❌ 0.x
task.input  # ✅ 1.0
```

The server rejects the old request shape with a `400` whose `errors[].field` is
`body.input.source_url`. The response change is silent — `task.source_url` and
`task.params` simply become `None` — so grep for them when you upgrade. Sync
methods (`client.video.*`, `client.image.*`, `client.audio.*`) are untouched.

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

## Documentation

- [Getting started](https://fotovid.co/docs/getting-started/quickstart)
- [API reference](https://fotovid.co/docs/reference/http) — every endpoint, with request/response schemas
- [Sync vs async guide](https://fotovid.co/docs/guides/sync-vs-async)
- [Pricing](https://fotovid.co/pricing)

## License

MIT
