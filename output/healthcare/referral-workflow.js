/* Synthetic coordination contract; not a FHIR implementation. No network or PHI. */
(function (root) {
  'use strict';
  class Workflow {
    constructor() { this.records = new Map(); this.events = []; this.clock = 0; }
    log(id, action, actor, detail) {
      this.events.push({sequence: this.events.length + 1, tick: this.clock, id, action, actor, detail});
    }
    intake(payload) {
      const missing = ['id', 'specialty', 'receiver'].filter(key => !String(payload[key] || '').trim());
      const key = payload.id || `MISSING-${this.records.size + 1}`;
      if (this.records.has(key)) { this.log(key, 'Duplicate ignored', 'adapter', 'Existing record retained'); return this.records.get(key); }
      const record = {key, payload: {...payload}, missing, status: missing.length ? 'Needs information' : 'Ready to send', owner: 'Coordinator', attempts: 0, sentAt: null};
      this.records.set(key, record);
      this.log(key, 'Intake', 'adapter', missing.length ? `Missing: ${missing.join(', ')}` : 'Administrative fields complete');
      return record;
    }
    send(key) {
      const record = this.records.get(key);
      if (!record || !['Ready to send', 'Retry approved'].includes(record.status)) return false;
      record.status = 'Awaiting acknowledgement'; record.owner = 'Integration operations';
      record.attempts++; record.sentAt = this.clock;
      this.log(key, 'Mock send', 'adapter', `Attempt ${record.attempts}; correlation ID ${key}`);
      return true;
    }
    acknowledge(key, eventId) {
      const record = this.records.get(key);
      if (!record || !record.attempts || !eventId) return false;
      if (this.events.some(event => event.action === 'Partner acknowledged' && event.detail === eventId)) return false;
      if (!['Awaiting acknowledgement', 'Acknowledgement overdue'].includes(record.status)) return false;
      record.status = 'Partner acknowledged'; record.owner = 'Coordinator';
      this.log(key, 'Partner acknowledged', 'mock partner', eventId); return true;
    }
    advance(ticks = 3) {
      this.clock += ticks;
      for (const record of this.records.values()) {
        if (record.status === 'Awaiting acknowledgement' && this.clock - record.sentAt >= 3) {
          record.status = 'Acknowledgement overdue'; record.owner = 'Coordinator';
          this.log(record.key, 'Timeout escalated', 'timer', 'No completion inferred; human follow-up required');
        }
      }
    }
    resolve(key, actor, reason) {
      const record = this.records.get(key);
      if (!record || !String(actor || '').trim() || !String(reason || '').trim() || record.status !== 'Acknowledgement overdue') return false;
      record.status = 'Retry approved'; record.owner = 'Integration operations';
      this.log(key, 'Human retry approval', actor.trim(), reason.trim()); return true;
    }
  }
  root.ReferralWorkflow = Workflow;
  if (typeof module !== 'undefined') module.exports = Workflow;
})(typeof globalThis !== 'undefined' ? globalThis : window);
