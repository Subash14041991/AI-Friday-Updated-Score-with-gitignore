# D1. Problem & success snapshot

## Problem statement

Customers, staff, and partners rely on a business-critical request/case/transaction capability whose work is spread across a stable core platform, supporting applications, tightly coupled integrations, spreadsheets, email, and manual steps. This fragmentation obscures end-to-end status and ownership, weakens auditability and operational insight, and contributes to inconsistent handling: 10–12% of work items need manual intervention. The enterprise needs to modernize incrementally—without replacing the core in Phase 1 or interrupting normal processing—to reduce avoidable effort and improve visibility, changeability, and resilience.

## Key constraints

- The current core platform cannot be replaced in Phase 1; the first phase must work with it.
- An initial usable capability is expected in about 12 weeks.
- Normal business processing must continue during modernization.
- Sensitive information must be protected and minimized.
- AI-assisted outputs must remain reviewable and governed.
- The design should support future channels and higher volumes.
- A big-bang replacement is too risky for the first phase.

## Assumptions to validate

1. **A representative work-item lifecycle can be agreed across the affected teams.** Validate the lifecycle stages, ownership hand-offs, and exception categories with business and operations representatives; otherwise consistent status measures may not be comparable.
2. **The core platform can exchange the minimum information needed for an initial usable capability through at least one supported integration mechanism.** Confirm available interfaces, data ownership, and constraints with the core-platform owner; this is not stated in the scenario.
3. **A baseline can be established for manual intervention and turnaround using operational records or a time-boxed sample.** Confirm definitions, data quality, and the reporting owner before setting reduction targets.
4. **Business and operations representatives can review AI-assisted outputs, and an accountable owner can define approval and escalation rules.** Validate governance, review capacity, and what decisions must remain human-controlled before introducing AI-assisted processing.
5. **The first 12-week release can be bounded to an initial usable capability rather than full replacement of all channels and processes.** Agree the minimum scope and rollout boundaries with business stakeholders; scope is not specified in the scenario.

## Success measures

Targets are not provided in the scenario. Agree numeric targets after establishing baselines and confirming definitions with the business owner.

| Measure | Definition / method | Baseline | Target | Data source / owner |
|---|---|---|---|---|
| Manual intervention rate | Work items requiring manual intervention ÷ total work items, reported for a consistent period and work-item scope. | 10–12% (scenario-provided; validate scope and measurement period). | TBD — validate with the business owner. | Operational work-item records; owner TBD. |
| End-to-end status and ownership visibility | Share of in-scope work items for which current status and accountable owner can be retrieved across the agreed lifecycle; test by sampling records or operational queries. | Not provided; establish baseline. | TBD — validate with the business owner. | Case/work-item records and operations sampling; owner TBD. |
| Turnaround time | Elapsed time from agreed start to completion, reported using an agreed statistic (for example median and/or percentile) and segmented by work-item type. | Not provided; establish baseline. | TBD — validate with the business owner. | Timestamped operational records; owner TBD. |
| Integration change lead time | Elapsed time from approval of an in-scope channel/integration change to production availability; define start/end points consistently. | Not provided; establish baseline. | TBD — validate with the business owner. | Change-management records; owner TBD. |
| Decision-history completeness | Share of sampled in-scope work items with retrievable status changes, decisions, and accountable actors recorded to the agreed audit standard. | Not provided; establish baseline. | TBD — validate with the business owner. | Work-item/audit records and sample review; owner TBD. |
| Business-processing continuity | Whether normal processing continues during rollout and modernization, measured against business-agreed disruption and service thresholds. | Thresholds and baseline not provided. | No unacceptable interruption; define the acceptable threshold with the business owner. | Service/incident records and business continuity reporting; owner TBD. |

## Open questions

- What business domain and work-item types are in scope for the first usable capability?
- Which lifecycle stages, status definitions, and ownership hand-offs must be visible end to end?
- What core-platform interfaces and operational constraints are available to Phase 1?
- What are current volumes, peak patterns, service expectations, and turnaround baselines?
- Which decisions, if any, may be AI-assisted, and which must always require human approval?

## Handoff to D2

- Compare options against incremental modernization, core-platform preservation, continuity, a usable capability in about 12 weeks, and improved integration flexibility, visibility, auditability, and future scale.
- Treat core interface availability, first-release scope, operational baselines, and AI decision boundaries as unresolved; make option dependencies explicit rather than assuming them.
- Do not frame Phase 1 as a big-bang core replacement. Show the trade-offs and conditions under which each credible incremental option works.
