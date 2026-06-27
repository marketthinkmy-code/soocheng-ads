"""Retry behaviour of the Graph client — specifically that Meta's HTTP-400 throttling
errors (which carry an error code, not a 429 status) are retried, not surfaced as a hard
failure. This is the gap that broke the nightly daily-report on 2026-06-24."""

import time

import pytest

from adbot.clients.graph import GraphClient, GraphError


class _FakeResp:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = str(payload)

    def json(self):
        return self._payload


class _FakeSession:
    """Returns the queued responses in order, recording how many calls were made."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0

    def request(self, *args, **kwargs):
        self.calls += 1
        return self._responses.pop(0)


THROTTLE_400 = _FakeResp(400, {"error": {
    "code": 17, "message": "There have been too many calls from this ad account."}})
OK_200 = _FakeResp(200, {"id": "1", "name": "me"})


@pytest.fixture(autouse=True)
def _no_real_sleep(monkeypatch):
    # tenacity's exponential backoff sleeps between attempts; skip the wall-clock wait.
    monkeypatch.setattr(time, "sleep", lambda *_: None)


def test_throttle_400_is_retried_then_succeeds():
    session = _FakeSession([THROTTLE_400, THROTTLE_400, OK_200])
    client = GraphClient("tok", session=session)
    assert client.me() == {"id": "1", "name": "me"}
    assert session.calls == 3  # two throttles retried, third succeeded


def test_non_throttle_400_is_not_retried():
    bad = _FakeResp(400, {"error": {"code": 100, "message": "Invalid parameter"}})
    session = _FakeSession([bad])
    client = GraphClient("tok", session=session)
    with pytest.raises(GraphError):
        client.me()
    assert session.calls == 1  # a real error fails fast, no wasted retries
