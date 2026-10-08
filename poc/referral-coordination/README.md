# Referral coordination — local application

Open `index.html` in Edge or Chrome. Keep the four supporting source files beside it. If a browser blocks local storage for file URLs, serve this directory locally instead; the application reports storage failures rather than pretending to save.

## Start the application

Open `poc/referral-coordination/index.html` from the project folder. Supporting files are `styles.css`, `config.js`, `workflow.js`, and `app.js`.

If necessary, run this command from your project root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m http.server 8765 --bind 127.0.0.1 --directory .\poc\referral-coordination
```

Open [the local application](http://127.0.0.1:8765/index.html). Keep that terminal running; press Ctrl+C to stop it. The server serves files locally, not a shared database or partner integration. Use the same browser profile, address, and port each time. File URLs and different server addresses have separate storage; records do not automatically move between them.

The workspace starts empty. **Add fictional examples** adds three optional examples; it never replaces existing records and does not duplicate examples already present.

## Workflow

1. Add a referral ID, specialty and receiving provider. Enter the responsible person. Incomplete details can be saved and corrected through **Edit details**.
2. Complete a hand-off through your approved external process, then use **Record hand-off** and enter its reference. This app does not send a message.
3. Use **Record receipt** when partner confirmation exists; enter the person and confirmation reference. Receipt is distinct from clinical acceptance or completed care.
4. A waiting referral becomes overdue when real time reaches its saved deadline. The default follow-up is 30 minutes. Change the setting before recording a hand-off; it applies only to future hand-offs. For a short review, set one minute and wait for the actual deadline.
5. An overdue hand-off can receive a late receipt or human-approved retry. Approval requires the person and follow-up reason. Record the next external hand-off separately.
6. Search/filter records, add administrative follow-up notes, inspect history, and export records. Refresh preserves the workspace in the same browser profile.

**Add fictional examples** is optional and never replaces existing records. No patient names, identifiers, clinical notes, or confidential information should be entered. Record IDs can themselves be identifying in real systems; use fictional or approved non-identifying inputs.

## Statuses and rules

| Status | Meaning / next action |
|---|---|
| Needs information | Specialty or receiving provider is missing. Edit details; hand-off is blocked. |
| Ready for hand-off | Required details are present. Complete the external hand-off, then record its reference. |
| Awaiting receipt | A hand-off is recorded; obtain partner confirmation. |
| Follow-up overdue | The saved deadline has passed without a recorded receipt. Follow up, record late receipt, or approve retry. |
| Retry approved | A person and reason are recorded. Complete and record another hand-off, or record a late receipt. |
| Receipt recorded | Partner receipt has been recorded by a person. Continue the next agreed care step outside this application. |

- Referral ID and responsible person are required to create a record. Specialty/provider may be left blank and completed later.
- ID cannot be changed through editing. Details cannot be edited after the first hand-off.
- Hand-off and receipt require a person and reference. Retry approval requires a person and reason and is allowed only when overdue.
- A late receipt may be recorded while overdue or after retry approval; after receipt, another hand-off is blocked.
- A duplicate ID with identical details retains the existing record. Different details for the same ID are rejected and logged; no silent overwrite occurs.
- The responsible role is supplied by configuration, currently **Care coordinator**. Role assignment and authenticated staff accounts are not implemented.
- The follow-up setting is a local working threshold, not a confirmed business service level. It must be a whole number from 1 to 10,080 minutes. Existing deadlines do not change when the setting changes.

## Fictional practice records

Enter **Alex Rao** as the responsible person. All IDs, providers, references, and follow-up statements below are fictional practice inputs. In actual operational use, references must come from actions and confirmations completed through approved external channels.

| Referral ID | Specialty | Receiving provider | Use case |
|---|---|---|---|
| PRACTICE-001 | Cardiology | Example Heart Centre | Normal hand-off and receipt |
| PRACTICE-002 | Leave blank | Example Skin Clinic | Missing-information correction |
| PRACTICE-003 | Orthopedics | Example Joint Centre | Overdue follow-up and retry |
| PRACTICE-004 | Neurology | Example Neuro Clinic | Late receipt |
| PRACTICE-005 | Dermatology | Example Skin Clinic | Duplicate and conflicting entry |

### 1. Normal path: PRACTICE-001

1. Click **Add referral**, enter the row's details and Alex Rao, then **Save referral**. Expect **Ready for hand-off**.
2. Click **Record hand-off**; enter Alex Rao and `PRACTICE-HANDOFF-001`. Click **Save**. Expect **Awaiting receipt**, attempt count 1.
3. Click **Record receipt**; enter Alex Rao and `PRACTICE-RECEIPT-001`. Expect **Receipt recorded**.
4. Inspect history for the person, timestamps, and references. Receipt does not mean clinical acceptance or completed care.

### 2. Missing information: PRACTICE-002

1. Add the record with specialty blank. Expect **Needs information** and no hand-off action.
2. Click **Edit details**, set specialty to `Dermatology`, and enter Alex Rao. Save. Expect **Ready for hand-off**.
3. Record hand-off reference `PRACTICE-HANDOFF-002` if continuing the flow.

### 3. Overdue follow-up and retry: PRACTICE-003

1. Before recording its hand-off, open **Follow-up settings**, choose `1` minute, enter Alex Rao, and save.
2. Add PRACTICE-003 and record hand-off `PRACTICE-HANDOFF-003-A`.
3. Leave receipt unrecorded and wait about one real minute. Expect **Follow-up overdue**. The browser checks deadlines each second; reopening recalculates from the saved time.
4. Click **Add follow-up note**; enter Alex Rao and `Contacted receiving office; receipt confirmation is pending.` Save.
5. Click **Approve retry**; enter Alex Rao and `Receiving office confirmed the first hand-off was not received and requested another attempt.` Expect **Retry approved**.
6. Record another hand-off with reference `PRACTICE-HANDOFF-003-B`. Expect attempt count 2 and **Awaiting receipt**.
7. Record receipt `PRACTICE-RECEIPT-003`. Expect **Receipt recorded** with one referral record and two attempts.

### 4. Late receipt: PRACTICE-004

1. With the one-minute setting, add PRACTICE-004 and record hand-off `PRACTICE-HANDOFF-004`.
2. Wait until overdue, then record receipt `PRACTICE-LATE-RECEIPT-004`.
3. Expect **Receipt recorded**, attempt count 1; no retry is necessary.
4. Optional variation: approve retry after overdue, then record a late receipt before a second hand-off. The receipt resolves the waiting state; another hand-off is no longer available.

### 5. Duplicate and conflict: PRACTICE-005

1. Add PRACTICE-005 with its listed details.
2. Add the exact same ID/details again. Expect one record and a duplicate-history entry.
3. Add the same ID but change provider to `Example Alternate Skin Clinic`. Expect conflict rejection; the original provider remains. Inspect history.

### 6. Required-input checks

- Try saving without ID/person, recording hand-off without a reference, or approving retry without a person/reason. The form blocks incomplete submissions; the engine also validates them.
- Confirm an incomplete referral cannot be handed off and an already handed-off referral has no **Edit details** action.
- A one-minute setting change after a hand-off does not change that referral's existing deadline. Set it before recording the hand-off you wish to observe.

### 7. Search, filtering, refresh, and export

- Search `PRACTICE-003` or `Cardiology` to find the relevant records.
- Select **Receipt recorded** to show only that status; choose **All statuses** and clear search to show everything.
- Refresh or close/reopen the same address in the same browser profile. Records/history should remain.
- Click **Export records** to download `coordination-records.json`, containing records, timestamps, history, and settings. File import/restore is not implemented; the export can be inspected and kept as a copy, but cannot automatically undo reset.
- After practising, restore **Follow-up settings** to `30` minutes. That affects future hand-offs only.

## Reset the workspace

**Reset workspace** is available in the toolbar.

1. Click **Reset workspace**. The dialog lists the record/history counts and default follow-up setting.
2. Use **Export records first** if you need a copy. Check that the download completed before proceeding. Import/restore is not implemented.
3. Type `RESET` exactly and click **Reset permanently**.
4. All records and action history in this application's local workspace are removed, the default follow-up setting is restored (currently 30 minutes), and search/status filters are cleared. Refresh stays empty.

**Cancel**, the close button, or Escape leaves data unchanged. Incorrect confirmation does not reset anything. Reset affects only this application's configured browser-storage namespace; it does not clear other sites, application files, or other browser profiles. Exported files are not deleted. There is no in-app undo, and reset does not change external systems. You can add new records or load the optional examples afterward.

If another tab changed the workspace, reset is rejected until reload. If storage cannot be written, reset fails without clearing the current records. Reset is disabled when saved data cannot be loaded safely; do not use browser-wide clearing as an automatic workaround.

## Persistence and limitations

Records, real timestamps, and action history are saved in browser local storage. Export before changing browser profiles or clearing browser data. No central server, multi-user access control, authenticated staff identity, protected audit trail, real partner/EHR transport, or clinical validation is provided. Closing and reopening recomputes overdue status from the saved deadline. Editing is blocked after a hand-off; conflicting re-entry preserves the original record and records the rejection. Concurrent-tab writes are rejected until the workspace is reloaded.

Browser storage is not an encrypted clinical record store or guaranteed backup. Private browsing, browser cleanup, a different profile, a changed address, or moving a file may make records unavailable. Overdue checks use the device clock, so incorrect device time affects deadlines. No notifications are sent while the application is closed; overdue state is shown on return. Action history lists recorded statements and can be altered through browser storage; it is not an authenticated or tamper-proof audit.

## Troubleshooting

| Symptom | What to do |
|---|---|
| Storage unavailable / save failed | Check browser permissions and available storage. Try the loopback server if file URLs are restricted. Existing data is not silently discarded. |
| Record seems missing | Clear filters; verify the same browser profile, URL, and port. Another browser/address has separate storage. |
| Another tab changed the workspace | Reload before saving. Re-enter the action against the latest record; the rejected action was not applied. |
| Saved data unsupported/unreadable | Preserve it and seek technical help; the application does not overwrite it automatically. |
| Not overdue after changing settings | Existing deadlines remain unchanged. The new setting applies only to future hand-offs. Check device time. |
| Partner has not actually received anything | This app records external hand-offs; it sends no messages. Use the approved external channel. |

## Other scenarios

`workflow.js` is a domain-neutral coordination engine. `config.js` supplies the item label, required fields, owner-role label, follow-up setting, storage namespace, and optional examples. Change that configuration and scenario-specific UI/help wording for a different domain. A different business lifecycle may also require different rules; do not assume this exact receipt/retry workflow fits every scenario. Agent 4's prompt chooses the appropriate proof from each scenario.

## Validation

Run `tests/test_coordination_workspace.cjs` from the project root using installed Node. Tests cover persistence/reload, correction, duplicate/conflict handling, real-time deadlines through an injectable clock, recorded evidence requirements, retry, late receipt, storage failure, tab conflicts, and configuration for another domain. Browser validation is separate in `tests/validate_coordination_browser.cjs`. Evidence belongs with this source application and does not update deliverable reports. First install Node packages with `npm ci` and the browser with `npm run install:browsers`, as described in the root README.

From the project root in PowerShell:

```powershell
node tests/test_coordination_workspace.cjs
node tests/validate_coordination_browser.cjs
```

The browser suite uses project-local Playwright and installed Chromium, with Edge or Codex tools only as optional fallbacks. It uses an isolated browser profile and a controlled test clock to check deadlines quickly; it does not alter the user's workspace or add a time-advance control to the app.

Expected: all checks pass. Engine/browser evidence files are `engine-validation.json` and `browser-validation.json` in this source directory; the browser suite refreshes `application-preview.png`. Confirmed reset, cancellation, invalid confirmation, persistence after reset, storage failure, and namespace isolation are included in the checks. These tests establish local software behavior only, not production or clinical readiness.

## Short presentation walkthrough

Start with the purpose: **staff can see referral progress, responsibility, and overdue follow-up without replacing clinical systems**. Show missing-information correction, a normal recorded hand-off/receipt, overdue follow-up and approved retry, then history and refresh persistence. Use the fictional practice values above. Explain that actual hand-offs happen through approved external channels and that receipt is not completed care. Finish with export and the reset confirmation dialog; reset only when you intend to discard the practice workspace.

## Current D4 source and report consistency

The current application supersedes the earlier `output/healthcare/poc-referral-validation.html` prototype. That earlier prototype's in-memory data, simulated ticks, and test counts must not be used to describe this application.

The current D4 generation source is `poc/referral-coordination/report-source/D4-template.md`, with artifact/evidence paths and report labels in `poc/referral-coordination/report-source/profile.json`. The renderer verifies the current source hashes against both evidence files before accepting PASS claims. It also checks artifact links and inserts counts/timestamps from evidence instead of copying old numbers.

From the project root, check consistency without changing outputs:

```powershell
.\.venv\Scripts\python.exe scripts/render_d4_review.py --check-only
```

The default mode is also check-only. Published D4 Markdown and report page 4 have now been regenerated from this application's source brief and matching evidence. They link to the current application and its evidence files; the earlier prototype remains a superseded artifact. Future source changes require evidence to be refreshed and checked before report regeneration; do not silently combine versions. Publishing requires the explicit `--publish` flag.
