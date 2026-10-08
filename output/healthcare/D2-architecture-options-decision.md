### D2. Architecture options & decision

#### Decision context
The network needs fewer referral corrections and delays, clearer status and responsibility, fewer incomplete hand-offs, and more complete action records. Keep the electronic health record (EHR), continue patient care, protect patient information, and aim for an initial usable capability in about **12 weeks**. D1's interfaces, process ownership, starting measurements, and targets remain unconfirmed. Compare two approaches; neither has demonstrated these improvements yet.

#### Option A — Shared referral coordination around the EHR
Add a shared capability that tracks referral progress across systems, shows who acts next, and directs problems to care coordinators. Connect it to the EHR and selected partners through replaceable connections. Clinical records stay in the EHR; the new capability tracks coordination.

**Potential benefit:** A shared view could reduce chasing and reveal delayed or incomplete hand-offs across organizations. Separate connections could make partner changes easier.

**Main trade-off / dependency:** Another capability must be operated and protected. Teams must agree identifiers, status meanings, responsibilities, and how conflicting updates are resolved. Usable interfaces and partner participation are prerequisites.

#### Option B — Improve referral coordination within the EHR
Improve referral tracking and work queues mainly inside the existing EHR, connecting selected partners directly. Staff use the EHR as the main coordination workspace; external providers retain their own systems.

**Potential benefit:** Could improve internal referral work while keeping staff close to the clinical record and limiting additional workspaces.

**Main trade-off / dependency:** The scenario says modifying the clinical core is expensive and risky. Feasibility depends on supported configuration and interfaces; partner-specific connections may preserve existing change difficulties. Existing access and audit controls still need assessment.

#### Trade-off comparison
| D1 outcome / criterion | Option A — Shared coordination | Option B — EHR-centered |
|---|---|---|
| Less follow-up / rework | Shared checks and coordinator tasks could expose missing details; depends on reliable updates. | EHR checks could reduce internal corrections; external chasing may remain. |
| Faster turnaround / fewer incomplete hand-offs | Cross-system tracking could reveal stalled referrals; staff and partners must act on them. | EHR queues could reveal internal delays; partner progress depends on available updates. |
| Clearer status and responsibility | Shared tracking could cover multiple organizations if statuses and roles are agreed. | Visibility could improve inside the EHR; external coverage depends on integrations. |
| More complete action records / privacy | Could record cross-system hand-offs; adds patient-data exposure and access/audit obligations. | Could use EHR records; audit completeness, access, and external records need checking. |
| Initial release / care continuity | Limit to one agreed process; test connections and safe fallback while retaining the EHR. | Limit to supported EHR changes; validate changes and rollback without disrupting care. |
| Partner changes / maintainability | Replaceable connections could isolate partner changes; mapping and upkeep remain necessary. | Direct connections may require repeated EHR or partner-specific changes. |
| Operating effort / growth | Adds shared tracking, support, and consistency work; capacity remains unproven. | Avoids a separate coordination workspace; depends more on EHR change cycles and capacity. |

#### Preferred direction
**Conditionally prefer Option A** for one agreed referral process. It more directly addresses D1's cross-system visibility, missing hand-offs, and manual chasing, while retaining the EHR. It does not guarantee faster referrals or lower rework.

**Accepted trade-offs:**
- Another capability to operate and support.
- Another patient-information boundary to protect and audit.
- Work to keep referral identities, statuses, and responsibilities consistent.

Keep clinical authority with authorized staff, preserve patient-care continuity, and provide human escalation. AI is optional and requires approved data use and review.

#### Decision dependencies and revisit triggers
- **Interfaces unavailable:** narrow the first process or reconsider a supported EHR-centered approach.
- **Roles or statuses unresolved:** defer shared coordination until clinical and operational owners agree them.
- **EHR changes demonstrably safer for this scope:** reconsider Option B for Phase 1.
- **Partner, privacy, or escalation requirements unmet:** defer the affected flow and agree a safe fallback.
- **12-week scope threatens care continuity:** reduce scope or revise sequencing.

#### Handoff to D3
- Show the retained EHR, shared tracking, coordinator tasks, partner connections, and clinical versus coordination data boundaries.
- Show access, audit, failure handling, and human escalation; validate actual interfaces and standards support before selecting mechanisms.
- Carry D1's measures and unresolved scope, ownership, privacy, and capacity questions into design validation.
