"""Tests for the secret-safe Responses-compatible adapter."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, date, datetime

import pytest

from signalforge.digest.generator import DigestGenerationError, ResponsesDigestGenerator
from signalforge.digest.models import DigestMessage, MessageLink


@dataclass
class FakeTransport:
    response: object
    seen_url: str = ""
    seen_headers: Mapping[str, str] = field(default_factory=dict)
    seen_payload: Mapping[str, object] = field(default_factory=dict)

    def post(
        self,
        url: str,
        headers: Mapping[str, str],
        payload: Mapping[str, object],
        timeout: float,
    ) -> object:
        assert timeout == 60
        self.seen_url = url
        self.seen_headers = headers
        self.seen_payload = payload
        return self.response


def test_generates_responses_request_and_extracts_nested_text() -> None:
    expected = "# SignalForge — 2026-07-12\n\n## Кратко\n\nИтог"  # noqa: RUF001
    transport = FakeTransport(
        {"output": [{"content": [{"type": "output_text", "text": expected}]}]}
    )
    generator = ResponsesDigestGenerator(
        "llm-secret-canary", "configured-model", "https://provider.example/v1/", transport
    )
    message = DigestMessage(10, 77, datetime(2026, 7, 12, tzinfo=UTC), "Source text")
    link = MessageLink(10, 77, "https://example.com")

    assert generator.generate(date(2026, 7, 12), [message], [link]) == expected
    assert transport.seen_url == "https://provider.example/v1/responses"
    assert transport.seen_payload["model"] == "configured-model"
    assert "message_id=77: Source text" in str(transport.seen_payload["input"])
    assert "https://example.com" in str(transport.seen_payload["input"])
    assert transport.seen_headers["Authorization"] == "Bearer llm-secret-canary"


@pytest.mark.parametrize("response", [{}, {"output": []}, "secret-canary malformed"])
def test_reduces_invalid_provider_response_to_safe_error(response: object) -> None:
    generator = ResponsesDigestGenerator(
        "llm-secret-canary", "model", "https://provider.example/v1", FakeTransport(response)
    )

    with pytest.raises(DigestGenerationError) as captured:
        generator.generate(date(2026, 7, 12), [], [])

    assert str(captured.value) == "llm_error"
    assert "secret-canary" not in str(captured.value)
