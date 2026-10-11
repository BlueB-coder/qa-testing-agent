# Optional OpenProject integration

Read this only for an explicitly supplied OpenProject work-package ID. Standalone
file/inline testing must not inspect or call the integration.

Use the separately installed [OpenProject skill and CLI](https://github.com/yungts97/openproject-skill)
or the project's available integration. Do not duplicate authentication or API code,
reinstall the integration, overwrite configuration or assume credentials. Read its
installed instructions and help before choosing commands. Authentication must be
available in the same operating environment; Windows and WSL profiles are separate.

Retrieve the exact ID, verify repository/project mapping where documented and read
test cases, related ACs, relations, accessible attachments and current status. Do
not infer readiness from task naming prefixes. Record missing ACs as traceability
gaps; block cases whose expected outcomes cannot be determined.

For the referenced CLI, documented read examples include `openproject task 1234
--full --json`, `openproject relations 1234 --json` and `openproject statuses --json`.
Verify installed help; other integrations may use different syntax. Missing integration
or authentication is a blocker, not evidence of having read the task. Explicitly
supplied local cases may still be tested with their own provenance.

Prepare the exact comment, sanitized attachment list, proposed defect details and
actual project status transition locally. Mark all drafts NOT POSTED. Approval of
a comment does not approve attachments, defect creation or status changes. A dry-run
is not approval. If the subagent cannot obtain approval, hand drafts to its coordinator.

Before approved submission, recheck repository revision, requirement changes and
task state. If material facts or content changed, seek renewed approval. Submit only
approved actions, record responses and identifiers, and stop on an error rather than
blindly retrying a potentially completed write. Check read-only state before any retry.
