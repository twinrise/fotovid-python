import pytest

import fotovid


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
