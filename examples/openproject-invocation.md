# OpenProject invocation

```text
Delegate QA testing for OpenProject task #1234 to the qa-tester agent.
```

1234 is a placeholder. Supply a real ID and an application repository with an isolated
QA runtime. Install/authenticate the separate integration in the host's environment.
The agent reads the exact task and related cases/ACs, prepares local evidence and an
exact draft comment, attachments and proposed project status transition.

All external drafts remain NOT POSTED until their individual actions are explicitly
approved. If delegated QA cannot request approval, it returns drafts to the coordinator.
Standalone file mode never requires or invokes this integration.
