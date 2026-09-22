"""Backend package for the waytoweb4-agent demo.

This package is intentionally a thin HTTP layer on top of the
`agent` library. Every security-critical decision lives there; this
package is responsible for:

    * running the Agent layer on user requests
    * minting / revoking passports (mock or Sepolia-shaped)
    * running a deterministic mock copy-trading engine
    * exposing everything via REST for the React frontend

Importing from this package should not have side effects beyond
loading settings.
"""
