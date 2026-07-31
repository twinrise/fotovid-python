from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal
from urllib.parse import quote

from ._http import clean, request_json

if TYPE_CHECKING:
    from ._client import Fotovid

# Deliberately excludes "video.meta" — the async worker always fails it (probe
# has no artifact to produce); use the sync ``client.video.probe`` instead.
TaskType = Literal[
    "image.watermark",
    "video.watermark",
    "video.cover",
    "video.trim",
    "video.audio",
    "audio.trim",
]
TaskStatus = Literal["starting", "processing", "succeeded", "failed", "canceled"]
WebhookEvent = Literal["completed", "failed"]

# Stable, closed set of task-level error codes (taskerr.ExternalCode).
TaskErrorCode = Literal[
    "invalid_input",
    "unsupported_media",
    "source_unreachable",
    "source_too_large",
    "unknown_task_type",
    "insufficient_credits",
    "processing_failed",
    "internal_error",
]


@dataclass
class TaskOutput:
    """One produced artifact. ``kind`` is "video" | "cover" | "image" | "audio"."""

    kind: str
    url: str


@dataclass
class TaskError:
    """Task-level failure, carried in ``Task.error`` on a "failed" task.

    Distinct from ``FotovidError``, which is raised for transport-layer
    failures (a non-2xx response to create/get itself).
    """

    code: TaskErrorCode
    message: str
    request_id: str
    detail: str | None = None


@dataclass
class Task:
    id: str
    status: TaskStatus
    source: str
    data_removed: bool
    created_at: str
    urls: dict[str, str]
    # Present when status is "failed". A failed task is not an exception —
    # check this field.
    error: TaskError | None = None
    task_type: str | None = None
    # The source URL exactly as submitted. Also delivered to your webhook and
    # retained in the delivery record.
    source_url: str | None = None
    # The processing params exactly as submitted. None for types that take none.
    params: dict[str, Any] | None = None
    # The labels passed as ``metadata``, returned verbatim. None when none were
    # supplied; on an idempotent replay this is the *stored* task's metadata,
    # not what the replay sent.
    metadata: dict[str, str] | None = None
    # Produced artifacts, once status is "succeeded". Order is not
    # guaranteed — read by kind.
    outputs: list[TaskOutput] | None = None
    started_at: str | None = None
    completed_at: str | None = None
    # RFC 3339, empty until the task succeeds. Output artifacts expire 7 days
    # after completion.
    expires_at: str | None = None
    metrics: dict[str, Any] | None = None

    @property
    def is_terminal(self) -> bool:
        return self.status in ("succeeded", "failed", "canceled")


def _task(data: dict[str, Any]) -> Task:
    raw_error = data.get("error")
    error = (
        TaskError(
            code=raw_error["code"],
            message=raw_error["message"],
            request_id=raw_error["request_id"],
            detail=raw_error.get("detail"),
        )
        if raw_error
        else None
    )
    raw_outputs = data.get("outputs")
    outputs = (
        [TaskOutput(kind=o["kind"], url=o["url"]) for o in raw_outputs]
        if raw_outputs
        else None
    )
    return Task(
        id=data["id"],
        status=data["status"],
        source=data["source"],
        data_removed=data["data_removed"],
        created_at=data["created_at"],
        urls=data["urls"],
        error=error,
        task_type=data.get("task_type"),
        source_url=data.get("source_url"),
        params=data.get("params"),
        metadata=data.get("metadata"),
        outputs=outputs,
        started_at=data.get("started_at"),
        completed_at=data.get("completed_at"),
        expires_at=data.get("expires_at"),
        metrics=data.get("metrics"),
    )


class _Tasks:
    """Async task surface: submit larger jobs than the sync endpoints accept,
    then poll for the result. There is no built-in ``wait`` — poll ``get``
    yourself::

        task = client.tasks.video.watermark(source_url=url, **params)
        while not task.is_terminal:
            time.sleep(2)
            task = client.tasks.get(task.id)
    """

    def __init__(self, client: Fotovid) -> None:
        self._client = client
        self.video = _TasksVideo(self)
        self.image = _TasksImage(self)
        self.audio = _TasksAudio(self)

    def create(
        self,
        *,
        type: TaskType,
        source_url: str,
        params: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
        webhook: str | None = None,
        webhook_events_filter: list[WebhookEvent] | None = None,
        metadata: dict[str, str] | None = None,
    ) -> Task:
        body = clean(
            {
                "type": type,
                "source_url": source_url,
                "params": params,
                "idempotency_key": idempotency_key or str(uuid.uuid4()),
                "webhook": webhook,
                "webhook_events_filter": webhook_events_filter,
                "metadata": metadata,
            }
        )
        data = request_json(
            base_url=self._client._base_url,
            api_key=self._client._api_key,
            timeout=self._client._timeout,
            path="/v1/tasks",
            method="POST",
            body=body,
        )
        return _task(data)

    def get(self, task_id: str) -> Task:
        """``failed`` is not raised — check ``task.error``. Only a transport
        failure raises ``FotovidError``."""
        data = request_json(
            base_url=self._client._base_url,
            api_key=self._client._api_key,
            timeout=self._client._timeout,
            path=f"/v1/tasks/{quote(task_id, safe='')}",
            method="GET",
        )
        return _task(data)


class _TasksVideo:
    def __init__(self, tasks: _Tasks) -> None:
        self._tasks = tasks

    def watermark(
        self,
        *,
        source_url: str,
        watermark_type: str | None = None,
        text: str | None = None,
        font_size: int | None = None,
        font_color: str | None = None,
        watermark_image_url: str | None = None,
        scale: float | None = None,
        opacity: float | None = None,
        position: str | None = None,
        padding: int | None = None,
        output_format: str | None = None,
        quality: int | None = None,
        preset: str | None = None,
        idempotency_key: str | None = None,
        webhook: str | None = None,
        webhook_events_filter: list[WebhookEvent] | None = None,
        metadata: dict[str, str] | None = None,
    ) -> Task:
        params = clean(
            {
                "watermark_type": watermark_type,
                "text": text,
                "font_size": font_size,
                "font_color": font_color,
                "watermark_image_url": watermark_image_url,
                "scale": scale,
                "opacity": opacity,
                "position": position,
                "padding": padding,
                "output_format": output_format,
                "quality": quality,
                "preset": preset,
            }
        )
        return self._tasks.create(
            type="video.watermark",
            source_url=source_url,
            params=params,
            idempotency_key=idempotency_key,
            webhook=webhook,
            webhook_events_filter=webhook_events_filter,
            metadata=metadata,
        )

    def trim(
        self,
        *,
        source_url: str,
        start: float,
        end: float,
        idempotency_key: str | None = None,
        webhook: str | None = None,
        webhook_events_filter: list[WebhookEvent] | None = None,
        metadata: dict[str, str] | None = None,
    ) -> Task:
        return self._tasks.create(
            type="video.trim",
            source_url=source_url,
            params={"start": start, "end": end},
            idempotency_key=idempotency_key,
            webhook=webhook,
            webhook_events_filter=webhook_events_filter,
            metadata=metadata,
        )

    def extract_audio(
        self,
        *,
        source_url: str,
        idempotency_key: str | None = None,
        webhook: str | None = None,
        webhook_events_filter: list[WebhookEvent] | None = None,
        metadata: dict[str, str] | None = None,
    ) -> Task:
        return self._tasks.create(
            type="video.audio",
            source_url=source_url,
            idempotency_key=idempotency_key,
            webhook=webhook,
            webhook_events_filter=webhook_events_filter,
            metadata=metadata,
        )

    def thumbnail(
        self,
        *,
        source_url: str,
        at: float | None = None,
        output_format: str | None = None,
        quality: int | None = None,
        idempotency_key: str | None = None,
        webhook: str | None = None,
        webhook_events_filter: list[WebhookEvent] | None = None,
        metadata: dict[str, str] | None = None,
    ) -> Task:
        params = clean({"at": at, "output_format": output_format, "quality": quality})
        return self._tasks.create(
            type="video.cover",
            source_url=source_url,
            params=params,
            idempotency_key=idempotency_key,
            webhook=webhook,
            webhook_events_filter=webhook_events_filter,
            metadata=metadata,
        )


class _TasksImage:
    def __init__(self, tasks: _Tasks) -> None:
        self._tasks = tasks

    def watermark(
        self,
        *,
        source_url: str,
        watermark_type: str | None = None,
        text: str | None = None,
        font_size: int | None = None,
        font_color: str | None = None,
        watermark_image_url: str | None = None,
        scale: float | None = None,
        opacity: float | None = None,
        position: str | None = None,
        padding: int | None = None,
        output_format: str | None = None,
        quality: int | None = None,
        idempotency_key: str | None = None,
        webhook: str | None = None,
        webhook_events_filter: list[WebhookEvent] | None = None,
        metadata: dict[str, str] | None = None,
    ) -> Task:
        params = clean(
            {
                "watermark_type": watermark_type,
                "text": text,
                "font_size": font_size,
                "font_color": font_color,
                "watermark_image_url": watermark_image_url,
                "scale": scale,
                "opacity": opacity,
                "position": position,
                "padding": padding,
                "output_format": output_format,
                "quality": quality,
            }
        )
        return self._tasks.create(
            type="image.watermark",
            source_url=source_url,
            params=params,
            idempotency_key=idempotency_key,
            webhook=webhook,
            webhook_events_filter=webhook_events_filter,
            metadata=metadata,
        )


class _TasksAudio:
    def __init__(self, tasks: _Tasks) -> None:
        self._tasks = tasks

    def trim(
        self,
        *,
        source_url: str,
        start: float,
        end: float,
        idempotency_key: str | None = None,
        webhook: str | None = None,
        webhook_events_filter: list[WebhookEvent] | None = None,
        metadata: dict[str, str] | None = None,
    ) -> Task:
        return self._tasks.create(
            type="audio.trim",
            source_url=source_url,
            params={"start": start, "end": end},
            idempotency_key=idempotency_key,
            webhook=webhook,
            webhook_events_filter=webhook_events_filter,
            metadata=metadata,
        )
