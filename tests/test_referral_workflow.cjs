const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {createHash} = require('node:crypto');
const workflowPath = process.argv[2] ? path.resolve(process.argv[2]) : path.join(__dirname, '../output/healthcare/referral-workflow.js');
const evidencePath = process.argv[3] ? path.resolve(process.argv[3]) : path.join(__dirname, '../output/healthcare/validation-results.json');
const Workflow = require(workflowPath);
const results = [];
function test(name, fn) { fn(); results.push({name, expected: 'Assertions pass', actual: 'PASS'}); }
const valid = {id: 'REF-SYN-001', specialty: 'Cardiology', receiver: 'Partner Alpha'};
test('Complete referral: intake, send and acknowledgement', () => {
  const w = new Workflow(); const r = w.intake(valid);
  assert.equal(r.status, 'Ready to send'); assert.equal(w.send(r.key), true);
  assert.equal(w.acknowledge(r.key, 'ACK-001'), true);
  assert.equal(r.status, 'Partner acknowledged'); assert.equal(r.owner, 'Coordinator');
});
test('Missing fields remain assigned to coordinator and cannot send', () => {
  for (const field of ['id', 'specialty', 'receiver']) {
    const w = new Workflow(); const r = w.intake({...valid, [field]: ''});
    assert.deepEqual(r.missing, [field]); assert.equal(r.owner, 'Coordinator');
    assert.equal(w.send(r.key), false);
  }
});
test('Duplicate referral preserves one record and original payload', () => {
  const w = new Workflow(); w.intake(valid); w.intake({...valid, specialty: 'Other'});
  assert.equal(w.records.size, 1); assert.equal(w.records.get(valid.id).payload.specialty, 'Cardiology');
  assert.equal(w.events.at(-1).action, 'Duplicate ignored');
});
test('Timeout creates an owned exception without inferred completion', () => {
  const w = new Workflow(); const r = w.intake(valid); w.send(r.key); w.advance();
  assert.equal(r.status, 'Acknowledgement overdue'); assert.equal(r.owner, 'Coordinator');
});
test('Human approval needs actor and reason; retry retains correlation ID', () => {
  const w = new Workflow(); const r = w.intake(valid); w.send(r.key); w.advance();
  assert.equal(w.resolve(r.key, '', 'Partner contacted'), false);
  assert.equal(w.resolve(r.key, 'Synthetic reviewer', ''), false);
  assert.equal(w.resolve(r.key, 'Synthetic reviewer', 'Mock partner confirms safe retry'), true);
  assert.equal(w.send(r.key), true); assert.equal(r.attempts, 2);
  assert.equal(w.records.size, 1); assert.equal(w.acknowledge(r.key, 'ACK-RETRY'), true);
});
test('Acknowledgement before send and duplicate acknowledgement are rejected', () => {
  const w = new Workflow(); w.intake(valid); assert.equal(w.acknowledge(valid.id, 'ACK'), false);
  w.send(valid.id); w.acknowledge(valid.id, 'ACK');
  const count = w.events.length; assert.equal(w.acknowledge(valid.id, 'ACK'), false);
  assert.equal(w.events.length, count);
});
test('Late acknowledgement reconciles an overdue referral', () => {
  const w = new Workflow(); const r = w.intake(valid); w.send(r.key); w.advance();
  assert.equal(w.acknowledge(r.key, 'ACK-LATE'), true); assert.equal(r.status, 'Partner acknowledged');
});
test('Audit sequence captures human actor and reason', () => {
  const w = new Workflow(); w.intake(valid); w.send(valid.id); w.advance();
  w.resolve(valid.id, 'Synthetic reviewer', 'Partner contacted');
  assert.deepEqual(w.events.map(e => e.sequence), [1,2,3,4]);
  assert.equal(w.events.at(-1).actor, 'Synthetic reviewer'); assert.equal(w.events.at(-1).detail, 'Partner contacted');
});
const evidence = {executedAt: new Date().toISOString(), scope: 'Executed JavaScript engine assertions; browser UI, real interfaces and clinical behavior are not validated.', passed: results.length, results};
evidence.artifactSha256 = {'referral-workflow.js': createHash('sha256').update(fs.readFileSync(workflowPath)).digest('hex')};
fs.writeFileSync(evidencePath, JSON.stringify(evidence, null, 2) + '\n');
console.log(`${results.length} workflow tests passed; validation-results.json written.`);
