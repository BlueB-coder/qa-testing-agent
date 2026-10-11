# Synthetic standalone QA cases

Application: a local fixture issue tracker. Use only isolated synthetic identities.
This is requirement input, not execution evidence.

- AC-1: an authenticated editor can create an issue with a title of 1–120 characters.
- AC-2: an empty title is rejected with the exact message `Title is required.`
- AC-3: a viewer cannot create an issue; a denied request persists no issue.

| Case | AC | Steps | Expected |
| --- | --- | --- | --- |
| TC-01 | AC-1 | Sign in as fixture editor; create `Printer offline`; reload list | One issue named `Printer offline` remains visible |
| TC-02 | AC-2 | Submit an empty title | `Title is required.`; no issue created |
| TC-03 | AC-3 | Attempt creation as fixture viewer through UI and API | Creation denied; no new record |

Invocation: `Delegate QA testing to the qa-tester agent using examples/standalone-test-cases.md.`
Set the application repository and fixture environment in its project context first.
