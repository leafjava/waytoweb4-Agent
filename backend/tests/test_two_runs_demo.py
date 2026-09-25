"""Keep the judge-facing controlled-run script aligned with the live API."""

from scripts.two_runs_demo import _run_one


def test_two_run_script_uses_current_authorization_lifecycle(client):
    first = _run_one(client, "contract-a", 500, 50, 50)
    second = _run_one(client, "contract-b", 100, 10, 10)

    for result, limit in ((first, 50), (second, 10)):
        assert result["drawdown_usd"] == limit
        assert result["verdict_level"] == "TRIP"
        assert result["verdict_codes"] == ["DD_LIMIT"]
        assert result["verdict_source"] == "rule_gate"
        assert result["status"] == "revoked"
        assert result["mint_tx_hash"] is None
        assert result["revoke_tx_hash"] is None
        assert result["simulation_id"].startswith("sim-")

    assert first["passport_id"] != second["passport_id"]
