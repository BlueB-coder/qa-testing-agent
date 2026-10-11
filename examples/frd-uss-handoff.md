# Synthetic FRD / USS handoff

Place actual requirement documents in the target application's documented paths.
These excerpts illustrate a handoff, not an existing application or completed QA.

FRD section 4, AC-4: A signed-in user may update the display name to 1–80 characters.
Saving shows `Profile saved.` and persists the value after reload.

USS story US-2: As a signed-in user, I can change my display name so teammates
recognize me. AC-5: a blank display name shows `Display name is required.`

```text
Delegate QA testing to the qa-tester agent using docs/FRD.md and docs/USS.md.
Derive test cases from the acceptance criteria and prepare a QA report.
```

Derive and label scenarios for successful persistence, empty input and the stated
length boundaries; link each to the originating section/AC. If USS instead states a
60-character limit, record the conflict and ask which expectation applies rather than
silently selecting one. Use `docs/RFD.md` if that is the project's real filename.
