# waytoweb4 execution adapter contract

Status: **provisional internal contract while the official waytoweb4 API documentation is pending**.

The authorization, RedLine and passport layers depend on this contract rather
than guessed external URLs. The current paper subprocess is the mock adapter.
When the official documentation arrives, add an HTTP adapter that maps these
commands to the documented endpoints; do not move policy or authorization
decisions into the transport.

## Start command

| Field | Type | Rule |
|---|---|---|
| `protocol_version` | integer | Must equal `1` |
| `request_id` | string | Unique and safe to retry |
| `run_id` | string | Evidence correlation ID |
| `passport_id` | string | Local authorization record ID |
| `spec_hash` | bytes32 hex | Must equal the manually confirmed frozen intent |
| `leader_id` | string | Taken from canonical intent |
| `notional_cents` | positive integer | Never send a floating-point amount |
| `max_loss_cents` | positive integer | Hard cap; transport cannot raise it |
| `expiry` | ISO-8601 UTC | Execution must stop at or before expiry |
| `paper` | boolean | Must be `true` in this project |

The adapter must reject a request unless the backend record is authorized and
`confirmed_spec_hash == spec_hash`. API keys, wallet keys and face data are not
part of this command.

## Required adapter behavior

1. Start is idempotent by `request_id`; retries must not create two sessions.
2. Return a stable execution/session ID and one of `starting`, `running`,
   `stopped`, `failed` or `uncertain`.
3. Stop accepts a reason code and is terminal for the session.
4. Status/readback exposes whether the engine is running and its current
   drawdown, but never authorizes a changed Spec.
5. Controller loss, expiry, policy removal and drawdown limit must stop the
   mock independently of an LLM response.
6. Every request and state change carries `run_id`, `request_id`, timestamps
   and a non-secret error code into the evidence log.

## Mapping checklist when official documentation arrives

- Record the official base URL, authentication scheme, timeout and retry rules.
- Map official decimal/amount semantics explicitly to integer cents.
- Confirm start/stop idempotency behavior and external session identifiers.
- Define timeout reconciliation before allowing retries.
- Add HTTP fixtures for accepted, rejected, timeout and ambiguous responses.
- Run the existing paper adapter tests unchanged, then run the same contract
  suite against the HTTP adapter with network calls mocked.
- Update this document with verified endpoint names only after the official
  documentation is received.
