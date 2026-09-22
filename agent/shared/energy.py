"""Energy estimation for Kiln / gpt-oss-120b calls.

Per PRD section 9 we are not allowed to actually measure the chip. We
use the 180W NPU-class assumption stated in the PRD itself:

    energy_Wh = 180 * latency_s / 3600

The latency here is wall-clock latency of the API call. We deliberately
do NOT multiply by token count: the chip is power-bound at ~180W while
it is running, and tokens are correlated with latency anyway. This
matches the PRD template the README will reproduce.
"""

from __future__ import annotations

# Per PRD §9: "180W 估算即可，禁止真测芯片"
NPU_POWER_W: float = 180.0


def estimate_wh(latency_s: float, tokens: int | None = None) -> float:
    """Estimate energy in Wh for a single Kiln call.

    Args:
        latency_s: Wall-clock latency of the API call in seconds.
        tokens: Optional token count, kept for forward compatibility.
            The current formula only uses latency, but the signature
            matches the PRD template which mentions both.

    Returns:
        Energy in watt-hours. Returned as float so callers can format
        it however they like (typically 4 decimal places).
    """
    if latency_s < 0:
        # Defensive: treat negative latencies as 0 rather than producing
        # nonsensical negative energy.
        latency_s = 0.0
    return NPU_POWER_W * latency_s / 3600.0


def assumption_note() -> str:
    """Return the human-readable assumption string for the README."""
    return f"{NPU_POWER_W:g}W NPU-class, energy = {NPU_POWER_W:g} * latency / 3600"