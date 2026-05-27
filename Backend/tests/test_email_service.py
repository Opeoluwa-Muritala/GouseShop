import pytest
from fastapi import HTTPException
from httpx import Request, Response

from app.core.config import settings
from app.services.email_service import render_email_content, send_email


class FakeSession:
    def __init__(self) -> None:
        self.logs = []

    def add(self, log):
        self.logs.append(log)

    async def commit(self):
        return None

    async def refresh(self, log):
        log.id = len(self.logs)


def test_email_templates_include_tokens():
    text, html = render_email_content("email_verification", {"token": "verify-token"})
    assert "verify-token" in text
    assert "<strong>verify-token</strong>" in html

    text, html = render_email_content("password_reset", {"token": "reset-token"})
    assert "reset-token" in text
    assert "<strong>reset-token</strong>" in html


@pytest.mark.asyncio
async def test_fake_email_logs_without_http(monkeypatch):
    monkeypatch.setattr(settings, "use_fake_external_services", True)
    session = FakeSession()

    log = await send_email(session, "user@example.com", "Subject", "email_verification", {"token": "abc"})

    assert log.status == "sent"
    assert log.provider_message_id == "fake_email_verification"
    assert session.logs == [log]


@pytest.mark.asyncio
async def test_real_email_posts_expected_payload(monkeypatch):
    monkeypatch.setattr(settings, "use_fake_external_services", False)
    monkeypatch.setattr(settings, "email_api_url", "https://email-api.test")
    calls = []

    class FakeClient:
        def __init__(self, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            return None

        async def post(self, url, json):
            calls.append((url, json))
            return Response(200, json={"id": "msg_123"}, request=Request("POST", url))

    monkeypatch.setattr("app.services.email_service.httpx.AsyncClient", FakeClient)
    session = FakeSession()

    log = await send_email(session, "user@example.com", "Reset", "password_reset", {"token": "reset-token"})

    assert calls == [
        (
            "https://email-api.test",
            {
                "to": "user@example.com",
                "subject": "Reset",
                "text": "Reset your GouseShop password with this token:\n\nreset-token",
                "html": "<p>Reset your GouseShop password with this token:</p><p><strong>reset-token</strong></p>",
            },
        )
    ]
    assert log.status == "sent"
    assert log.provider_message_id == "msg_123"


@pytest.mark.asyncio
async def test_provider_failure_logs_and_raises(monkeypatch):
    monkeypatch.setattr(settings, "use_fake_external_services", False)
    monkeypatch.setattr(settings, "email_api_url", "https://email-api.test")

    class FakeClient:
        def __init__(self, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            return None

        async def post(self, url, json):
            return Response(500, text="nope", request=Request("POST", url))

    monkeypatch.setattr("app.services.email_service.httpx.AsyncClient", FakeClient)
    session = FakeSession()

    with pytest.raises(HTTPException):
        await send_email(session, "user@example.com", "Reset", "password_reset", {"token": "reset-token"})

    assert session.logs[-1].status == "failed"
    assert session.logs[-1].error == "nope"
