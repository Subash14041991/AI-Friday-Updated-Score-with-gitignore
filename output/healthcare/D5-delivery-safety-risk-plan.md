### D5. Delivery & risk plan

#### Now / Next / Later roadmap
**Business stakeholders must confirm owners, scope, timing, baselines, and targets.** The scenario's approximately **12-week initial capability** is a planning constraint, not a guarantee. This proposed sequence follows D2's conditional shared-coordination direction; reduce scope or revisit it if critical dependencies fail.

| Phase | Outcome / key work | Condition to proceed | Accountable owner |
|---|---|---|---|
| Now | Select one referral process and partners; agree roles, statuses, interfaces, privacy, and D1 measurement definitions. Review the local POC's persistence, correction, deadlines, recorded references, export, and reset. | Confirm viable exchange, safe escalation, and scope. Establish baselines and agree targets before evaluating improvement. | Proposed: referral process owner. |
| Next | Build a limited connected capability around the retained electronic health record (EHR). Add authenticated access, protected storage/history, recovery, and operational monitoring; train coordinators and test a controlled pilot. | Prove interfaces, matching, recorded evidence, access controls, restoration, fallback, and care continuity. Clinical/privacy owners authorize pilot; assess D1 measures without assuming improvement. | Proposed: delivery lead. |
| Later | Review pilot measures/incidents; expand partners or referral types only where justified. Consider AI assistance separately if approved. | Stable workflow, effective controls, partner readiness, and evidence support expansion; otherwise correct gaps first. | Proposed: referral process owner. |

#### Top five risks and mitigations
Ordered by proposed practical priority; no measured risk scores are implied.

| Risk / consequence | Mitigation / early warning | Accountable owner |
|---|---|---|
| Unsafe or unowned hand-offs delay care. | Agree urgency, responsibility, and human escalation; test failure cases. **Warning:** no owner or escalation route—stop the affected flow. | Proposed: clinical pathway owner. |
| Interfaces or partner readiness prevent usable coordination. | Verify minimum exchange early. **Warning:** required details/status cannot be exchanged—narrow scope or revisit D2. | Proposed: integration lead. |
| Identity, status, or manually recorded receipt is wrong. | Validate matching and milestone meanings; check references against source evidence. **Warning:** conflict or unsupported confirmation—require review, not automatic completion. | Proposed: clinical informatics lead. |
| Patient data or history is exposed or lost. | Require controlled access, protected storage/audit, backup and tested restoration. **Warning:** shared unprotected browser data or unrecoverable deletion—keep it out of operational use. | Proposed: privacy/security lead. |
| Transition, staffing, or scope exceeds the delivery window. | Pilot one agreed process, train staff, retain fallback, and review dependencies. **Warning:** unmonitored parallel work or unresolved critical dependency—reduce scope before rollout. | Proposed: referral operations manager. |

#### AI-use reflection
AI helped draft the decision pack, simplify the diagram, build the application, and create automated checks; user review shaped wording and functionality. D4 records **17 rule tests and 13 browser checks**, which establish local behavior, not clinical or business approval. Clinical decisions, privacy acceptance, delivery commitments, and risk acceptance remain with accountable people; the application has no runtime AI.

#### Delivery guardrails
- Retain the EHR and continue normal patient care during Phase 1.
- Keep clinical records in source systems; use only approved necessary information for coordination.
- Browser persistence is not protected central storage; typed names are not authenticated users, and export without import is not a tested restore.
- Recorded receipt is not verified delivery or completed care; retain authorized human escalation and keep AI optional.
