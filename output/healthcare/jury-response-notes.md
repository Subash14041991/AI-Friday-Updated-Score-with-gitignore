# Jury response notes

## Opening explanation

The patient problem is fragmented referral ownership and status. Our conditional choice is a thin orchestration boundary around the retained EHR. The synthetic prototype now tests receipt, duplicates, timeout ownership and human retry; it does not prove clinical outcomes or real interoperability. Discovery gates control a proposed twelve-week pilot.

## Why introduce a hub instead of changing the EHR?

Cross-network ownership and status span multiple systems. A hub can isolate partner changes, but adds a PHI boundary and operating responsibility. Prefer EHR-centered enhancement if discovery demonstrates it is safer and sufficient for the first pathway.

## What interoperability standard have you implemented?

None. The POC uses a proposed local coordination contract. Discovery must verify supported FHIR profiles, existing HL7 messages or approved proprietary interfaces, matching, terminology and lifecycle semantics. Standards names do not establish conformance.

## What did the POC actually prove?

Eight engine assertion tests plus browser smoke checks passed. Required fields block sending, duplicates retain one record, missing receipt gets an owned exception, and retry needs a recorded reviewer/reason. Receipt is never clinical acceptance. Evidence files record execution; mock partners and volatile history limit the claim.

## What happens if the partner goes down?

The simulation creates a coordinator-owned overdue task; human follow-up permits retry with the same identity. Production needs agreed thresholds, durable state, idempotency contracts, reconciliation, monitoring and a tested downtime path before pilot.

## Where is AI used?

Codex assisted this revision's code, test, contract and planning drafts. Deterministic tests and a browser smoke check validate software behaviors. No runtime AI, clinical validation or clinical sign-off is claimed. Actual clinical/privacy/partner owners must approve the pathway and data handling.

## Can you guarantee twelve weeks or improved outcomes?

No. Weeks 1–4 establish scope/interfaces/governance, 5–8 build the thin slice, 9–10 validate safety and continuity, 11–12 pilot if gates pass. Unsupported interfaces or unresolved safety findings trigger scope reduction or replanning. Measure baselines before agreeing targets.
