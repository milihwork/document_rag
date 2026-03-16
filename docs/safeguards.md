# Safeguards 🛡️

The RAG pipeline is protected by **configurable input and output safeguards**. They run inside the RAG service: the **input safeguard** validates the user query before embedding and search; the **output safeguard** validates the LLM response before it is returned. Blocked requests or responses return HTTP 403 with a clear error message.

---

## Overview 🧭

Safeguards help protect against:

- **Prompt injection** — e.g. "ignore previous instructions", "reveal system prompt"
- **Unsafe or disallowed topics** — e.g. harmful or illegal content in the query
- **Leaked sensitive content** — e.g. "confidential" or "internal document" in the LLM output

Safeguards are **modular** (you can add new providers) and **config-driven** (enable/disable and select provider via environment variables). All rule content is centralized in one file so it can be reused across the system.

---

## Where rules live 📂

All blocked patterns and topics are defined in:

**`backend/shared/safeguard_constants.py`**

- `BLOCKED_PROMPT_PATTERNS` — phrases that cause the **input** to be blocked (prompt injection, jailbreak, etc.)
- `BLOCKED_TOPICS` — topic phrases that cause the **input** to be blocked
- `BLOCKED_OUTPUT_PATTERNS` — phrases that cause the **output** to be blocked (e.g. confidential leakage)

Edit this file to add or remove rules. No code changes are required in the safeguard implementations; they read from these constants.

---

## Configuration ⚙️

| Variable | Default | Description |
|----------|---------|-------------|
| `SAFEGUARD_ENABLED` | `true` | Set to `false` (or `0`/`no`) to disable input and output checks. |
| `SAFEGUARD_PROVIDER` | `basic` | Safeguard implementation. Currently only `basic` is supported. |

Example: disable safeguards (e.g. for local testing):

```bash
SAFEGUARD_ENABLED=false
```

---

## Current provider: `basic` 🧩

The **basic** safeguard:

- **Input:** Normalizes the query to lowercase and checks for any of `BLOCKED_PROMPT_PATTERNS` or `BLOCKED_TOPICS` as substrings. If found, the query is blocked (403).
- **Output:** Normalizes the response to lowercase and checks for any of `BLOCKED_OUTPUT_PATTERNS`. If found, the response is blocked (403).

Blocked requests are logged at WARNING (e.g. "Query blocked by safeguard: ...") to help detect prompt injection or policy violations.

---

## Adding a new safeguard provider 🔌

1. In `backend/services/safeguard/`, add a new module (e.g. `advanced_guard.py`).
2. Implement a class that inherits from `BaseSafeguard` and defines:
   - `validate_input(self, query: str) -> bool` — return `False` to block the query
   - `validate_output(self, response: str) -> bool` — return `False` to block the response
3. In `factory.py`, import the new class and add a branch for the new provider name (e.g. `if provider == "advanced": return AdvancedSafeguard()`).
4. Document any provider-specific environment variables. Users set `SAFEGUARD_PROVIDER=advanced` to select it.

The RAG service and Gateway do not need changes; they already call the safeguard via the factory.

---

## Future improvements 🗺️

Possible extensions (not implemented yet):

- **AI-based prompt injection detection** — use a small classifier or LLM call to detect adversarial prompts
- **LLM-based intent classification** — classify query intent and block certain categories
- **Document-level prompt injection protection** — validate ingested or retrieved chunks before they are sent to the LLM
- **Moderation APIs** — integrate with third-party content moderation services

These can be added as new safeguard providers (e.g. `services/safeguard/advanced_guard.py`) and selected via `SAFEGUARD_PROVIDER`.
