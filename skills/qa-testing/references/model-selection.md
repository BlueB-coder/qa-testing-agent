# Model selection

Default to inheriting the supported parent model. Codex omits a model override;
Claude uses `model: inherit`. Do not hardcode internal nicknames or assume provider
families have equivalent capability, pricing or latency.

If the coordinator explicitly chooses an override, verify its actual identifier,
account access and host support against current vendor documentation. Optional
provider-family recommendations are heuristics, not compatibility promises.

For difficult or ambiguous QA, request reassignment through the coordinator when
needed; do not claim automatic switching. Record the model only when known from
the runtime, and identify unknowns or substitutions. Model choice never replaces
evidence or authorizes unsafe tests, source fixes or external writes.
