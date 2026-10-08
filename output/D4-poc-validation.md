# D4. Focused POC / validation

## Question and hypothesis

**Question:** Can a compact workflow-style triage queue make synthetic exception work visible, offer an explainable routing suggestion, and capture a human's acceptance or override without connecting to or changing the core platform?

**Hypothesis:** A small queue with explicit exception reason, suggested route, human accept/override controls, and a decision history will make the human-control flow understandable and demonstrate how an auditable orchestration layer could handle exceptions.

## Scope and safety

- Tests the interaction and handoff concept for D2's workflow-led orchestration recommendation.
- Uses five fictional, synthetic case records and transparent keyword rules to simulate routing suggestions.
- No AI model, paid endpoint, external network call, personal or production data, credentials, live core, or supporting system is used.
- A human must accept or override each recommendation. This prototype does not perform a business transaction.
- A browser-session audit list shows each reviewed case and action. Refresh resets the prototype state.

## Prototype

**Artifact:** [`poc/exception-triage/index.html`](../poc/exception-triage/index.html)

**How to run:** Open the HTML file directly in a modern browser. No server, install, or dependency is required. Select **Accept suggestion** or choose a route and **Apply override**. Observe the queue counters and Decision history.

The page displays a synthetic exception queue, a simulated recommendation and its keyword-rule explanation, accept/override actions, and counts for total, pending, reviewed, and overridden cases.

## Test method

1. Open the prototype and confirm that five synthetic cases appear as awaiting review.
2. Accept the suggestion for one case. Confirm the card displays the reviewed route, open/reviewed counts update, and one decision-history entry appears.
3. For a different case, choose a different route and apply the override. Confirm the override count increments and the history records an override.
4. Attempt to review an already-reviewed case; confirm no duplicate audit entry is created.
5. Refresh the page; confirm the data returns to its initial synthetic state and no decision state persists.

**Success criteria:** Recommendations are visibly labeled as simulated; human accept and override actions update queue state; decisions are recorded in the session history; no production system or external AI service is invoked.

## Results and learning

The standalone browser prototype was exercised against the steps above:

- Five synthetic exceptions are rendered with distinct rule explanations, including a general-operations fallback when no specific keyword rule matches.
- Accept and override actions update review counters and the displayed final route.
- Each action records the case ID, action type, route, and browser-local timestamp in the on-page session history.
- Already-reviewed records cannot create a second decision entry through the queue controls.
- Refresh returns the prototype to its initial state; this is an in-memory mock, not persistent audit storage.

**Learning:** The human-in-the-loop interaction and visible decision capture can be demonstrated without connecting to the core. The mock-up makes review/override explicit, but it does not establish whether an AI model can classify exceptions accurately or whether source systems can provide the data required.

## Limitations and what remains unproven

- Keyword rules simulate a suggestion; no AI model has been evaluated, and no accuracy or quality claim can be made.
- Synthetic cases are illustrative, not representative evidence of actual exception types, volumes, or operational behavior.
- No authentication, authorization, durable storage, audit integrity, privacy controls, integration adapter, retries, or production monitoring is implemented.
- No core/supporting-system interface or end-to-end workflow has been tested.
- The browser-only history is volatile and not suitable as an audit record.
- Production design still requires business validation of exception categories, lifecycle/status definitions, human ownership, data minimization, security, retention, service expectations, and integration contracts.

## Handoff to D5

- Sequence lifecycle/exception workshops and interface discovery before implementing operational orchestration.
- Treat classification quality, durable audit capture, source-system integration, security, and operational scale as open risks requiring separate evidence.
- Keep human review and override as explicit controls; do not infer runtime AI readiness from this UI demonstration.
