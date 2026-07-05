"""GraphClient low-level retry behaviour — esp. Meta's HTTP-400 rate-limit throttling."""
from unittest.mock import MagicMock, patch

import pytest

from src.adbot.clients.graph import GraphClient, GraphError


def _resp(status, payload):
    r = MagicMock()
    r.status_code = status
    r.json.return_value = payload
    r.text = str(payload)
    return r


def test_rate_limit_400_retries_then_succeeds():
    """Meta returns '[400] too many calls' when throttled — must back off + retry, not crash."""
    sess = MagicMock()
    sess.request.side_effect = [
        _resp(400, {"error": {"code": 17,
                              "message": "There have been too many calls from this ad account."}}),
        _resp(400, {"error": {"code": 17, "message": "too many calls"}}),
        _resp(200, {"ok": True}),
    ]
    g = GraphClient("tok", "", session=sess)
    with patch("time.sleep"):                     # skip the exponential backoff waits
        out = g._request("GET", "me")
    assert out == {"ok": True}
    assert sess.request.call_count == 3           # two throttles retried, third succeeded


def test_real_400_is_not_retried():
    """A genuine bad-request 400 must fail fast (single call), not spin on retries."""
    sess = MagicMock()
    sess.request.side_effect = [
        _resp(400, {"error": {"code": 100, "message": "Invalid parameter"}}),
        _resp(200, {"ok": True}),
    ]
    g = GraphClient("tok", "", session=sess)
    with patch("time.sleep"), pytest.raises(GraphError) as exc:
        g._request("GET", "me")
    assert exc.value.status == 400
    assert sess.request.call_count == 1
