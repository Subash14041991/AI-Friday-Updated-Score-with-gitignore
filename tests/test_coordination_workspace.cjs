const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {createHash}=require('node:crypto');
const Workspace=require('../poc/referral-coordination/workflow.js');
const config={storageKey:'test',coordinator:'Coordinator',followUpMinutes:30,fields:[{key:'specialty',label:'Specialty'},{key:'receiver',label:'Receiver'}]};
class Storage{constructor(){this.data=new Map();this.fail=false;}getItem(k){return this.data.get(k)??null;}setItem(k,v){if(this.fail)throw new Error('full');this.data.set(k,v);}}
function setup(){let now=Date.UTC(2026,9,8,4,0);const storage=new Storage();const w=new Workspace(config,storage,()=>now);return {w,storage,advance:ms=>now+=ms};}
const input={id:'R1',specialty:'Cardiology',receiver:'Provider'};
const record=w=>w.state.records.find(r=>r.id==='R1');
const results=[];
function test(name,fn){fn();results.push({name,result:'PASS'});}
test('Incomplete entry can be corrected; hand-off blocked until complete',()=>{
  const {w}=setup();w.add({...input,specialty:''},'Person');assert.equal(w.status(record(w)),'Needs information');
  assert.throws(()=>w.handoff('R1','Person','H1'),/not ready/);w.edit('R1',input,'Person');assert.equal(w.status(record(w)),'Ready for hand-off');
});
test('Records and history persist across reload',()=>{
  const {w,storage}=setup();w.add(input,'Person');const restored=new Workspace(config,storage);assert.equal(restored.state.records.length,1);assert.equal(restored.state.events[0].actor,'Person');
});
test('Actual elapsed time determines overdue state and recovery after closing',()=>{
  const {w,storage,advance}=setup();w.add(input,'Person');w.handoff('R1','Person','H1');advance(30*60000-1);assert.equal(w.status(record(w)),'Awaiting receipt');advance(1);assert.equal(w.status(record(w)),'Follow-up overdue');
  const restored=new Workspace(config,storage,()=>record(w).dueAt+1);assert.equal(restored.status(record(restored)),'Follow-up overdue');
});
test('Retry requires overdue state, actor and reason; same record receives second attempt',()=>{
  const {w,advance}=setup();w.add(input,'Person');w.handoff('R1','Person','H1');assert.throws(()=>w.approveRetry('R1','Person','Reason'),/overdue/);advance(30*60000);
  assert.throws(()=>w.approveRetry('R1','','Reason'),/person/);assert.throws(()=>w.approveRetry('R1','Person',''),/reason/);w.approveRetry('R1','Person','Provider contacted');w.handoff('R1','Person','H2');assert.equal(record(w).attempts,2);assert.equal(w.state.records.length,1);
});
test('External action recording requires references; receipt is not completion',()=>{
  const {w}=setup();w.add(input,'Person');assert.throws(()=>w.receipt('R1','Person','ACK'),/after hand-off/);assert.throws(()=>w.handoff('R1','Person',''),/reference/);
  w.handoff('R1','Person','H1');assert.throws(()=>w.receipt('R1','Person',''),/reference/);w.receipt('R1','Person','ACK');assert.equal(w.status(record(w)),'Receipt recorded');assert.match(w.state.events.at(-1).detail,/does not mean final business completion/);const count=w.state.events.length;assert.throws(()=>w.receipt('R1','Person','ACK'));assert.equal(w.state.events.length,count);
});
test('Late receipt after retry approval cancels the need for a new hand-off',()=>{
  const {w,advance}=setup();w.add(input,'Person');w.handoff('R1','Person','H1');advance(30*60000);w.approveRetry('R1','Person','Followed up');w.receipt('R1','Person','Late ACK');assert.equal(w.status(record(w)),'Receipt recorded');assert.throws(()=>w.handoff('R1','Person','H2'),/not ready/);
});
test('Duplicate identity retains original; conflicting details explicitly rejected',()=>{
  const {w}=setup();w.add(input,'Person');assert.equal(w.add(input,'Person').created,false);const result=w.add({...input,receiver:'Different'},'Person');assert.equal(result.conflict,true);assert.equal(record(w).fields.receiver,'Provider');assert.equal(w.state.records.length,1);assert.equal(w.state.events.at(-1).action,'Conflicting entry rejected');
});
test('Post-hand-off edits blocked; follow-up notes remain attributable',()=>{
  const {w,storage}=setup();w.add(input,'Person');w.handoff('R1','Person','H1');assert.throws(()=>w.edit('R1',{...input,receiver:'Other'},'Person'),/cannot be edited/);w.note('R1','Reviewer','Called receiving office');const restored=new Workspace(config,storage);assert.equal(record(restored).note,'Called receiving office');assert.equal(restored.state.events.at(-1).actor,'Reviewer');
});
test('Changing threshold affects future hand-offs only',()=>{
  const {w}=setup();w.add(input,'Person');w.handoff('R1','Person','H1');const due=record(w).dueAt;w.setFollowUp(1,'Person');assert.equal(record(w).dueAt,due);assert.throws(()=>w.setFollowUp(0,'Person'));assert.throws(()=>w.setFollowUp(1.5,'Person'));w.add({...input,id:'R2'},'Person');w.handoff('R2','Person','H2');const r=w.state.records.find(r=>r.id==='R2');assert.equal(r.dueAt-r.sentAt,60000);
});
test('Storage failure leaves in-memory and saved records unchanged',()=>{
  const {w,storage}=setup();w.add(input,'Person');const before=JSON.stringify(w.state);storage.fail=true;assert.throws(()=>w.note('R1','Person','Unsaved'),/Could not save/);assert.equal(JSON.stringify(w.state),before);assert.equal(storage.getItem('test'),before);
});
test('Concurrent tab writes rejected until reload',()=>{
  const {w,storage}=setup();w.add(input,'Person');const second=new Workspace(config,storage);w.note('R1','First','First note');assert.throws(()=>second.note('R1','Second','Overwrite'),/Another tab/);second.load();assert.equal(record(second).note,'First note');second.note('R1','Second','Reviewed');
});
test('Unreadable saved data preserved; unavailable storage reported',()=>{
  const storage=new Storage();storage.setItem('test','not JSON');assert.throws(()=>new Workspace(config,storage),/preserved/);assert.equal(storage.getItem('test'),'not JSON');assert.throws(()=>new Workspace(config,{getItem(){throw new Error('blocked');}}),/unavailable/);
});
test('Required actor and source ID rejected before saving',()=>{
  const {w}=setup();assert.throws(()=>w.add(input,''),/person/);assert.throws(()=>w.add({...input,id:' '},'Person'),/record ID/);assert.equal(w.state.records.length,0);
});
test('Same engine supports a non-healthcare configuration',()=>{
  const c={storageKey:'orders',coordinator:'Dispatch team',followUpMinutes:10,fields:[{key:'destination',label:'Warehouse'},{key:'category',label:'Order category'}]};
  const w=new Workspace(c,new Storage());w.add({id:'ORDER-1',destination:'Warehouse A',category:''},'Operator');assert.equal(w.status(w.state.records[0]),'Needs information');w.edit('ORDER-1',{destination:'Warehouse A',category:'Equipment'},'Operator');w.handoff('ORDER-1','Operator','Dispatch ref');assert.equal(w.state.records[0].owner,'Dispatch team');
});
test('Reset requires explicit confirmation and remains cleared after reload',()=>{
  const {w,storage}=setup();w.add(input,'Person');w.setFollowUp(1,'Person');const before=JSON.stringify(w.state);
  assert.throws(()=>w.reset(''),/RESET/);assert.throws(()=>w.reset('reset'),/RESET/);assert.equal(JSON.stringify(w.state),before);
  w.reset('RESET');assert.equal(w.state.records.length,0);assert.equal(w.state.events.length,0);assert.equal(w.state.followUpMinutes,30);
  const restored=new Workspace(config,storage);assert.equal(restored.state.records.length,0);assert.equal(restored.state.events.length,0);assert.equal(restored.state.followUpMinutes,30);
});
test('Reset storage failure preserves workspace and other namespaces',()=>{
  const {w,storage}=setup();w.add(input,'Person');storage.setItem('unrelated','retain');const before=JSON.stringify(w.state);storage.fail=true;
  assert.throws(()=>w.reset('RESET'),/Could not save/);assert.equal(JSON.stringify(w.state),before);assert.equal(storage.getItem('test'),before);
  storage.fail=false;w.reset('RESET');assert.equal(storage.getItem('unrelated'),'retain');
});
test('Reset rejects a stale tab instead of removing newer work',()=>{
  const {w,storage}=setup();w.add(input,'Person');const second=new Workspace(config,storage);w.note('R1','Person','Recent action');
  assert.throws(()=>second.reset('RESET'),/Another tab/);const restored=new Workspace(config,storage);assert.equal(record(restored).note,'Recent action');
});
const hashes={};for(const f of ['workflow.js','app.js','config.js','index.html','styles.css'])hashes[f]=createHash('sha256').update(fs.readFileSync(path.join(__dirname,'../poc/referral-coordination',f))).digest('hex');
fs.writeFileSync(path.join(__dirname,'../poc/referral-coordination/engine-validation.json'),JSON.stringify({executedAt:new Date().toISOString(),passed:results.length,results,artifactSha256:hashes,scope:'Local persistence and coordination rules; no external delivery or clinical validation.'},null,2)+'\n');
console.log(`${results.length} coordination tests passed.`);
