### D4. Focused POC / validation

#### Question and hypothesis
**Question:** Can local coordination keep referrals visible through missing information, delayed receipts, and human-approved retry, while preserving records across refresh?

**Hypothesis:** Staff can correct incomplete entries, record external hand-offs and receipt references, see overdue follow-up from saved deadlines, and retain attributable action history in the same browser.

#### Scope and safety
The working local application covers D3's referral entry, shared tracking, and staff follow-up. Records persist in browser storage; deadlines use device time. Partner/EHR exchange and patient updates are excluded. No clinical decisions or runtime AI. Use fictional or approved non-identifying data; typed names are recorded labels, not authenticated identities.

#### Prototype
Open [Referral coordination](../../poc/referral-coordination/index.html); keep its four supporting files together. See the [usage and practice guide](../../poc/referral-coordination/README.md).

1. Add a referral with missing specialty; correct it through **Edit details**.
2. **Record hand-off** with a person/reference from an external action; the application sends no messages.
3. Set a short follow-up before a new hand-off, wait for its deadline, and approve retry with a person/reason. Record the next external hand-off separately.
4. **Record receipt** with partner confirmation; inspect history and refresh to verify persistence.
5. Export if needed. Reset requires typing `RESET`; it clears local records/history and restores defaults. Export has no automatic import/restore.

Receipt is not completed care. The default follow-up is 30 minutes, a configurable local setting pending business agreement.

#### Test method
Run `tests/test_coordination_workspace.cjs` and `tests/validate_coordination_browser.cjs` with the bundled Node runtime. Timing tests use a controlled clock; the application itself uses real time and has no time-advance control.

| Case | Expected behavior | Observed result |
|---|---|---|
| Entry and correction | Missing information blocks hand-off; corrections revalidate without duplication. | PASS |
| References, deadlines, and retry | Required evidence/person; overdue follow-up; reasoned retry and late receipt. | PASS |
| Persistence and conflicts | Refresh retains data; duplicate/conflicting entries preserve originals; stale writes rejected. | PASS |
| Storage failures and reset | Failed writes preserve data; cancellation retains records; confirmed reset remains cleared. | PASS |
| Export and presentation | Export includes records/history/settings; search/filter and mobile layout work. | PASS |

#### Results and learning
**17 rule tests and 13 browser checks passed.** Engine run: 08 Oct 2026, 10:35 AM IST; browser run: 08 Oct 2026, 10:36 AM IST. [Rule evidence](../../poc/referral-coordination/engine-validation.json) and [browser evidence](../../poc/referral-coordination/browser-validation.json) match the current source hashes.

Results support D2's coordination concept and D1's visibility, hand-off, and action-record measures. They show local software behavior, not reduced rework, faster care, verified partner delivery, or representative-user usability.

#### Limitations and what remains unproven
- Browser persistence is not protected central storage or a tamper-proof audit. Cleanup/reset can remove data; export is not a tested restore.
- No authenticated users, enforced consent, clinical validation, real interfaces, patient matching, or patient notifications. Recorded receipt is a person's statement.
- No production capacity, outage recovery, business-outcome or AI-performance evidence. Device time affects deadlines; overdue status appears on reopening, without closed-app alerts.

#### Handoff to D5
Require real interface proof, accountable roles, appropriate storage/access/audit, recovery testing, and safe escalation before an operational pilot. Use D1 baselines and agreed targets; D2 remains conditional.
