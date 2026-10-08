### D1. Problem & success snapshot

#### Problem statement
Referrals span the electronic health record (EHR), portals, scheduling, diagnostic/insurance systems, partners, spreadsheets, and emails. Staff cannot consistently see progress or who acts next. The scenario reports **15–20% of referrals require manual follow-up or rework**. Patients face delays, repeated calls, and unclear next steps; coordinators chase missing information. The goal is clearer tracking and reliable hand-offs while preserving the EHR, care, privacy, and human oversight.

#### People and current process
| People / group | Current role | Difficulty / impact |
|---|---|---|
| Patients | Receive care and referral-related communication. | Delays, repeated calls, unclear next steps. |
| Primary-care teams | Initiate referrals and supply clinical context. | Limited visibility across hand-offs. |
| Care coordinators | Track progress, obtain missing details, coordinate hand-offs. | Manual chasing across systems. |
| Specialists | Receive referrals and provide specialist care. | Clinical context may be unavailable when needed. |
| External partner providers | Exchange referrals and updates with the network. | Connections are expensive to change; inconsistent shared status. |

Current process summary: primary care initiates referral → information moves between systems → coordinators resolve gaps → specialist/partner acts → progress and outcome are shared.

**Confirm these roles and process steps with the clinical and operational owners of the referral process.** Overall ownership is unspecified.

#### Key constraints
- Keep the EHR in Phase 1; an initial usable capability is expected in about **12 weeks**.
- Continue normal patient care and referral processing during modernization.
- Minimize and secure protected health information (PHI); keep actions traceable.
- Govern AI-assisted outputs; keep them reviewable and sufficiently explainable.
- Support interoperability standards and future partners; confirm available interfaces.
- Give patient-facing automation a safe route to a person for escalation.

#### Assumptions to validate
1. **A manageable first referral process can be selected.** Confirm scope and participants with clinical and operational owners.
2. **Selected systems can exchange essential details and updates.** Check interfaces, permitted data, and partner readiness.
3. **Teams can agree identifiers, statuses, and responsibilities.** Confirm matching and meanings while preserving clinical-record authority.
4. **Records or a sample can establish starting performance.** Check data quality, definitions, and reporting period.
5. **Governance can define escalation and permitted AI use.** Confirm review responsibilities and privacy boundaries before using AI in the running system.

#### Success measures
Baseline is starting performance; target is the improvement goal. Agree the referral group and reporting period. **Business stakeholders must confirm measure owners, baselines, and targets.** Proposed owners collect, validate, and report measures. Sources and owners are proposals; results are not yet demonstrated.

| Measure | Definition / method | Baseline | Target | Data source / owner |
|---|---|---|---|---|
| Less follow-up / rework | Referrals needing manual follow-up or rework ÷ all in-scope referrals. | Scenario: 15–20%; validate group/period. | To agree after baseline measurement. | Source (proposed): work-queue records. Owner (proposed): referral operations manager. |
| Faster turnaround | Median time from agreed start to agreed scheduling or completion milestone; define events first. | Not yet measured. | To agree after baseline measurement. | Source (proposed): referral/scheduling timestamps. Owner (proposed): referral operations manager. |
| Clearer status and responsibility | Sampled referrals with current status and responsible owner across agreed stages ÷ all sampled referrals. | Not yet measured. | To agree after baseline measurement. | Source (proposed): system/partner records. Owner (proposed): referral process owner. |
| Fewer incomplete hand-offs | Referrals unresolved beyond an agreed stage-specific follow-up window ÷ all in-scope referrals. | Not yet measured. | To agree after baseline measurement. | Source (proposed): referral/partner outcomes. Owner (proposed): referral process owner. |
| More complete action records | Sampled hand-offs recording status, time, actor/system, and required outcome ÷ all sampled hand-offs. | Not yet measured. | To agree after baseline measurement. | Source (proposed): audit records. Owner (proposed): referral operations manager, supported by audit/compliance. |

Rate measures are percentages. Receipt, scheduling, and clinical completion are distinct; receipt alone does not mean completed care.

#### Open questions
- Which urgent exceptions require immediate escalation, and to whom?
- Which consent, access, retention, and audit rules apply?
- What information and next-step updates should patients receive?

#### Handoff to D2
- Compare visibility, reliable hand-offs, easier integration changes, privacy, and continuity within the stated constraints.
- Carry scope, interface readiness, status meanings, measurement gaps, and governance dependencies forward as unconfirmed.
