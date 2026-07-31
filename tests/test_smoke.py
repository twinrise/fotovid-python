from typing import Any

import pytest

import fotovid
import fotovid._tasks


def test_exports() -> None:
    assert hasattr(fotovid, "Fotovid")
    assert hasattr(fotovid, "FotovidError")
    assert hasattr(fotovid, "MediaResult")
    assert hasattr(fotovid, "ProbeResult")


def test_client_namespaces() -> None:
    client = fotovid.Fotovid(api_key="p6_test:secret", base_url="http://localhost:9")
    assert callable(client.video.watermark)
    assert callable(client.video.trim)
    assert callable(client.video.extract_audio)
    assert callable(client.video.thumbnail)
    assert callable(client.video.probe)
    assert callable(client.image.watermark)
    assert callable(client.audio.trim)


def test_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FOTOVID_API_KEY", raising=False)
    with pytest.raises(ValueError):
        fotovid.Fotovid()


def test_base_url_strips_trailing_slash() -> None:
    client = fotovid.Fotovid(api_key="p6_test:secret", base_url="http://x/")
    assert client._base_url == "http://x"


def test_error_message_from_detail() -> None:
    err = fotovid.FotovidError(400, {"detail": "bad input"})
    assert err.status == 400
    assert "bad input" in str(err)


def test_task_metadata_round_trip(monkeypatch: pytest.MonkeyPatch) -> None:
    """metadata goes out in the body and the echoed fields come back on Task."""
    captured: dict[str, Any] = {}

    def fake_request_json(**kwargs: Any) -> dict[str, Any]:
        captured.update(kwargs)
        return {
            "id": "01JAB",
            "status": "starting",
            "source": "api",
            "data_removed": False,
            "created_at": "2026-06-03T12:00:00Z",
            "urls": {"get": "https://api.fotovid.co/v1/tasks/01JAB"},
            "error": None,
            "source_url": "https://cdn.example.com/clip.mp4",
            "params": {"start": 0, "end": 30},
            "metadata": {"order_id": "A-1001"},
        }

    monkeypatch.setattr(fotovid._tasks, "request_json", fake_request_json)
    client = fotovid.Fotovid(api_key="p6_test:secret", base_url="http://localhost:9")
    task = client.tasks.video.trim(
        source_url="https://cdn.example.com/clip.mp4",
        start=0,
        end=30,
        metadata={"order_id": "A-1001"},
    )

    assert captured["body"]["metadata"] == {"order_id": "A-1001"}
    assert task.metadata == {"order_id": "A-1001"}
    assert task.source_url == "https://cdn.example.com/clip.mp4"
    assert task.params == {"start": 0, "end": 30}


def test_task_metadata_omitted_when_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    """No metadata kwarg means no metadata key in the body."""
    captured: dict[str, Any] = {}

    def fake_request_json(**kwargs: Any) -> dict[str, Any]:
        captured.update(kwargs)
        return {
            "id": "01JAB",
            "status": "starting",
            "source": "api",
            "data_removed": False,
            "created_at": "2026-06-03T12:00:00Z",
            "urls": {"get": "https://api.fotovid.co/v1/tasks/01JAB"},
            "error": None,
        }

    monkeypatch.setattr(fotovid._tasks, "request_json", fake_request_json)
    client = fotovid.Fotovid(api_key="p6_test:secret", base_url="http://localhost:9")
    task = client.tasks.audio.trim(
        source_url="https://cdn.example.com/track.mp3", start=0, end=30
    )

    assert "metadata" not in captured["body"]
    assert task.metadata is None
