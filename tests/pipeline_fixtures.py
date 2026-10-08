"""Deterministic warehouse scenario responses; no external model calls."""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parent.parent
SCENARIO='<html><section id="challenge"><h1>Warehouse request coordination</h1><p>Requests cross inventory and delivery systems. Keep inventory records authoritative, continue dispatch, and improve ownership and hand-offs. Initial scope and timing require business agreement.</p></section></html>'

def response(stage):
    data={'markdown':MARKDOWN[stage],'artifacts':[]}
    if stage=='D4':
        source=ROOT/'poc/referral-coordination'
        artifacts=[]
        for name in ['index.html','styles.css','workflow.js','app.js']:
            content=(source/name).read_text(encoding='utf-8')
            if name=='index.html':content=content.replace('Save referral','Save request')
            artifacts.append({'path':'poc/application/'+name,'content':content})
        artifacts += [
          {'path':'poc/application/config.js','content':'''window.WorkspaceConfig={title:'Warehouse requests',subtitle:'Track warehouse hand-offs.',itemLabel:'Request',storageKey:'warehouse-test',coordinator:'Dispatch coordinator',followUpMinutes:10,fields:[{key:'specialty',label:'Category'},{key:'receiver',label:'Warehouse'}],examples:[]};'''},
          {'path':'poc/README.md','content':'# Warehouse requests\nOpen application/index.html. Add an ID, category and warehouse. Correct missing details, record an external hand-off reference and receipt. Data stays in the browser. No messages are sent.\nValidation: node tests/workflow.cjs; the pipeline browser harness runs tests/browser.cjs. Use fictional data. Reset requires RESET; export first.\n'},
          {'path':'poc/tests/workflow.cjs','content':'''const assert=require('node:assert/strict');const W=require('../application/workflow.js');let now=1000000;const data=new Map();const storage={getItem:k=>data.get(k)||null,setItem:(k,v)=>data.set(k,v)};const config={storageKey:'w',coordinator:'Dispatch',followUpMinutes:1,fields:[{key:'category',label:'Category'}]};const w=new W(config,storage,()=>now);w.add({id:'ORDER-1',category:''},'Operator');assert.equal(w.status(w.state.records[0]),'Needs information');assert.throws(()=>w.handoff('ORDER-1','Operator','H1'));w.edit('ORDER-1',{category:'Equipment'},'Operator');w.handoff('ORDER-1','Operator','H1');now+=60000;assert.equal(w.status(w.state.records[0]),'Follow-up overdue');w.approveRetry('ORDER-1','Operator','Provider contacted');w.receipt('ORDER-1','Operator','ACK1');const restored=new W(config,storage,()=>now);assert.equal(restored.status(restored.state.records[0]),'Receipt recorded');console.log('Persistence, correction, timeout, review and receipt assertions passed.');'''},
          {'path':'poc/tests/browser.cjs','content':'''module.exports=async({page,assert})=>{await page.locator('#add').click();const form=page.locator('#editor');await form.locator('[name=id]').fill('ORDER-UI');await form.locator('[name=receiver]').fill('Warehouse A');await form.locator('[name=actor]').fill('Operator');await form.getByRole('button',{name:'Save request'}).click();assert.match(await page.locator('.record').innerText(),/Needs information/);await page.getByRole('button',{name:'Edit details'}).click();await form.locator('[name=specialty]').fill('Equipment');await form.locator('[name=actor]').fill('Operator');await form.getByRole('button',{name:'Save request'}).click();assert.match(await page.locator('.record').innerText(),/Ready for hand-off/);await page.reload();assert.equal(await page.locator('.record').count(),1);assert.match(await page.locator('#history').innerText(),/Details updated/);};'''}]
        data['artifacts']=artifacts
        data['poc']={'entrypoint':'poc/application/index.html','engine_tests':[{'path':'poc/tests/workflow.cjs','runtime':'node'}],'browser_test':'poc/tests/browser.cjs'}
    return data

MARKDOWN={
'D1':'''### D1. Problem & success snapshot
#### Problem statement
Warehouse teams chase request updates across systems. Improve progress visibility and clear responsibilities.
#### People and current process
| People / group | Current role | Difficulty / impact |
|---|---|---|
| Requesters | Submit requests. | Unclear next steps. |
| Dispatch staff | Coordinate hand-offs. | Missing details and delayed updates. |
Confirm roles with process owners.
#### Key constraints
- Keep source inventory records and continue dispatch.
#### Assumptions to validate
1. One manageable request process can be selected.
2. Supported interfaces can exchange updates.
3. Business owners can establish starting measurements.
#### Success measures
| Measure | Definition / method | Baseline | Target | Data source / owner |
|---|---|---|---|---|
| Less rework | Reworked requests / all requests. | Not yet measured | To agree | Proposed: request records / operations lead |
| Faster hand-off | Median start-to-receipt time; agree events. | Not yet measured | To agree | Proposed: timestamps / operations lead |
| Visible ownership | Owned sampled requests / all sampled requests. | Not yet measured | To agree | Proposed: records / process owner |
| Complete history | Complete sampled histories / all sampled histories. | Not yet measured | To agree | Proposed: history / process owner |
#### Open questions
- Which partners and first process are in scope?
#### Handoff to D2
- Compare continuity, visibility, integration and operating effort.
''',
'D2':'''### D2. Architecture options & decision
#### Decision context
Improve request progress while retaining inventory records.
#### Option A — Shared coordination
Add shared tracking around existing systems. Potential benefit: cross-system visibility. Trade-off: another capability to operate.
#### Option B — Existing-system enhancement
Improve tracking in the current system. Potential benefit: familiar workspace. Trade-off: partner coverage depends on interfaces.
#### Trade-off comparison
| Criterion | Option A | Option B |
|---|---|---|
| Rework | Shared checks may reveal gaps. | Internal checks may help. |
| Turnaround | Cross-system delays visible. | Internal delays visible. |
| Ownership | Shared status if agreed. | Stronger inside current system. |
| History | New history needs controls. | Existing history needs assessment. |
| Continuity | Requires fallback. | Requires safe change control. |
| Operating effort | Additional capability. | Existing-system dependency. |
#### Preferred direction
Conditionally prefer A for the agreed first process. Accept additional operating work and consistent-update requirements. Keep source records authoritative.
#### Decision dependencies and revisit triggers
- Missing interfaces: narrow scope or revisit B.
#### Handoff to D3
- Show request entry, shared tracking, existing records and staff follow-up.
''',
'D3':'''### D3. Target-state architecture
#### Architecture view
```mermaid
flowchart LR
subgraph Users["People"]
Requester["Requesters"]
Staff["Dispatch staff"]
end
subgraph New["Proposed coordination"]
Entry["Request entry"]
Tracking["Shared tracking"]
end
Core["Existing inventory system"]
Requester -->|"Submit"| Entry
Entry -->|"Register"| Tracking
Tracking <-->|"Details and status"| Core
Tracking <-->|"Follow-up and review"| Staff
```
Requesters submit; tracking exchanges updates and directs problems to staff. Controls apply across flows.
#### Major components and responsibilities
| Component | Responsibility | Ownership |
|---|---|---|
| Entry | Receive requests. | Does not own inventory. |
| Tracking | Progress and follow-up. | Coordination state only. |
| Existing system | Inventory records. | Source authority retained. |
#### Integration and data
- Confirm interfaces and retain minimal tracking data.
#### AI and human control
No runtime AI. Staff review exceptions.
#### Security and resilience
- Validate access, history, safe retry and fallback.
#### Design assumptions and validation points
- Confirm roles, interfaces and volume.
#### Alignment to D2
Implements conditional A and supports D1 visibility and history measures.
''',
'D4':'''### D4. Focused POC / validation
#### Question and hypothesis
Can local tracking keep requests visible through missing information and preserve actions across refresh? Hypothesis: correction, explicit hand-off rules and local persistence support the selected workflow.
#### Scope and safety
Fictional requests only. No live delivery or authenticated users.
#### Prototype
Open [Warehouse requests](poc/application/index.html). Read [setup instructions](poc/README.md). Add an incomplete request, correct it, record external references and refresh.
#### Test method
Run the supplied engine assertions and browser checks with the documented harness. Expected behavior: missing details block hand-off, correction revalidates, refresh preserves records.
#### Results and learning
NOT RUN. Expected rules require execution evidence before results are claimed.
#### Limitations and what remains unproven
Local storage is not protected central storage. No real integration, authenticated identity, or proven business improvements.
#### Handoff to D5
Confirm interfaces, roles, access, recovery and baseline measures before pilot.
''',
'D5':'''### D5. Delivery & risk plan
#### Now / Next / Later roadmap
Business owners must confirm scope, owners, timing, baselines and targets. Timing is to agree.
| Phase | Outcome / key work | Condition to proceed | Accountable owner |
|---|---|---|---|
| Now | Discover interfaces and select scope. | Agree roles and measures. | Proposed: process owner |
| Next | Build connected tracking and test recovery. | Prove interfaces, access, history and fallback. | Proposed: delivery lead |
| Later | Review measures and expand carefully. | Stable operations and evidence. | Proposed: process owner |
#### Top five risks and mitigations
| Risk / consequence | Mitigation / early warning | Accountable owner |
|---|---|---|
| Ownerless requests stall. | Agree roles; missing owner requires review. | Proposed: operations lead |
| Interfaces unavailable. | Verify early; failure narrows scope. | Proposed: integration lead |
| Conflicting statuses. | Validate meanings; conflict requires review. | Proposed: data owner |
| Data loss or exposure. | Protect access and test restore; failed recovery blocks pilot. | Proposed: security lead |
| Transition overload. | Narrow scope and train staff; unmonitored work delays rollout. | Proposed: operations lead |
#### AI-use reflection
AI assistance requires human review. Runtime AI is excluded. Automated software checks are distinct from business acceptance.
#### Delivery guardrails
- Keep source records and normal dispatch.
- Use agreed access controls and human escalation.
- Evaluate outcomes against established baselines.
'''}
