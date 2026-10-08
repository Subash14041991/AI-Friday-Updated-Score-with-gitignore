# D2. Architecture options & decision

## Decision context

D1 frames an incremental modernization of a business-critical request/case/transaction capability. Phase 1 must retain the stable but expensive-to-change core, keep normal processing running, protect sensitive information, and target an initial usable capability in about 12 weeks. The decision should improve end-to-end status and ownership, reduce avoidable manual effort, make integrations easier to change, and strengthen auditability and operational insight.

The core's supported interfaces, first-release scope, work-item lifecycle, data ownership, and current baselines are not yet confirmed. The options below therefore describe patterns, not a committed product or deployment design.

## Option A — Workflow-led case orchestration

Introduce a workflow/case orchestration capability as a system of engagement around the existing core. It coordinates the selected end-to-end work-item lifecycle, maintains a shared status and ownership view, routes exceptions to a human work queue, and invokes existing systems through replaceable adapters. The core remains the system of record for its existing responsibilities; rollout is incremental and limited to an agreed initial scope.

**Strengths:** Directly addresses fragmented hand-offs, distributed process knowledge, exception handling, and missing end-to-end ownership. A centrally visible workflow can provide a natural place to record process state and operational decisions.

**Limitations and dependencies:** Requires agreement on lifecycle, ownership, and which system owns each piece of data. Workflow integration with the core and supporting applications must be feasible through interfaces that are not yet known. It adds a new operational capability and risks duplicating rules if existing applications continue to own overlapping process logic.

## Option B — API/event integration backbone with existing workflows retained

Introduce a decoupling layer of APIs and adapters, with events or other supported change notifications where available, between channels, existing applications, and the core. Existing systems continue to own their current workflows; a consolidated status/read view and operational history are assembled from their interfaces and records. New channels integrate through the shared boundary rather than adding more direct point-to-point connections.

**Strengths:** Targets tight coupling and makes integration boundaries more reusable while minimizing early changes to existing process behavior. It can improve the ability to add channels without replacing the core.

**Limitations and dependencies:** Existing workflow ownership and rules remain distributed, so consistent end-to-end handling and exception resolution may remain difficult. A consolidated view depends on reliable status data, identifiers, and interface support across systems. The integration layer adds operational complexity and does not by itself standardize the work lifecycle.

## Trade-off comparison

| Criterion | Option A — Workflow-led case orchestration | Option B — API/event backbone, workflows retained |
|---|---|---|
| Phase 1 feasibility and initial usability | Can focus on one agreed lifecycle and a thin integration slice; feasibility depends on interfaces and how quickly ownership/rules can be agreed. | Can begin with a bounded integration and status view; feasibility depends on usable source interfaces and consistent identifiers/status data. |
| Business continuity and core impact | Core remains in place; requires careful coexistence and incremental routing so active processing continues. | Core and current workflows remain in place; typically changes integration boundaries and reporting before changing process behavior. |
| End-to-end visibility and ownership | Stronger fit: workflow state and work ownership are explicit in the orchestration layer for the in-scope lifecycle. | Partial fit: a consolidated view may be possible, but work ownership and process state remain spread across source systems. |
| Integration flexibility and changeability | Adapters isolate the orchestration from system-specific interfaces; the approach also introduces a new workflow integration point. | Strong fit for decoupling channel/system connections; integration changes can be isolated, subject to the chosen interface and delivery patterns. |
| Auditability and operational insight | Can record workflow transitions and human decisions centrally for the in-scope journey; source-of-truth boundaries must be explicit. | Can provide integration and status history; complete decision history depends on what existing workflows expose and record. |
| Delivery and operating complexity | Adds workflow ownership, operational support, and migration/coexistence work; scope must be tightly controlled. | Adds integration and data-reconciliation operations; distributed process rules and exception handling remain to manage. |
| Future channels and higher volumes | New channels can enter through the orchestration boundary; capacity and resilience need validation in the target design. | New channels can use shared APIs/adapters; event capabilities and source-system throughput need validation. |

## Preferred direction

**Recommend Option A, workflow-led case orchestration, for a narrowly scoped initial lifecycle, subject to validation of core/application interfaces and business ownership.** It more directly addresses the scenario's end-to-end status and ownership gap, distributed process knowledge, and manual exception handling. Option B improves coupling but leaves process ownership and much of the resolution logic distributed, so it is less likely by itself to deliver a consistent end-to-end operating view.

The team accepts that Option A introduces a new workflow capability, requires explicit data and process ownership, and needs careful coexistence with current applications. To control scope and risk:

- Keep the existing core in place and authoritative for its established records and transactions.
- Start with an agreed in-scope lifecycle and integrate through replaceable adapters; do not assume a specific core interface.
- Make workflow state, source-of-truth ownership, and failure/retry behavior explicit in D3.
- Keep consequential decisions with authorized staff. Treat AI-assisted classification or routing as optional recommendations subject to review and governance, not an autonomous requirement for Phase 1.

This is a conditional architecture recommendation, not a confirmed implementation commitment.

## Decision dependencies and revisit triggers

- Confirm the core and supporting systems' available interfaces, data ownership, and constraints. If they cannot support safe, timely interaction for a bounded workflow, reconsider Option A's scope or use Option B as an initial decoupling/status foundation.
- Agree the first usable lifecycle, process owner, and system-of-record boundaries. If a common workflow cannot be agreed, defer central orchestration and first establish shared status and integration boundaries.
- Validate first-release scope against the approximately 12-week expectation and continuity requirement. If workflow rollout would put either at unacceptable risk, reduce the scope or phase the recommendation.
- Confirm the source systems can provide reliable identifiers, status, and decision history. If not, define a staged data-quality and reconciliation approach before promising consolidated visibility or audit completeness.
- Confirm AI governance and human-review capacity before considering AI-assisted operational steps. If sensitive information cannot be sent to an approved AI service, keep AI out of the runtime flow; the architecture direction can still proceed without it.

## Handoff to D3

- Show the workflow/case orchestration boundary coordinating one initial lifecycle around the existing core and supporting applications, with adapters isolating system-specific interfaces.
- Identify which system owns each key work-item record and status; distinguish orchestration state from authoritative core data.
- Show the channel/system integration paths, operational status/history, and how the design can add future channels without direct point-to-point growth.
- Include security and resilience controls, including sensitive-data minimization and safe handling of integration failures; exact mechanisms depend on platform capabilities.
- Show a human work queue/approval point for exceptions and any AI-assisted recommendation. No autonomous consequential action is assumed.
- Mark core interfaces, data ownership, lifecycle scope, volume/service expectations, and AI governance as unresolved inputs to validate—not settled design facts.
