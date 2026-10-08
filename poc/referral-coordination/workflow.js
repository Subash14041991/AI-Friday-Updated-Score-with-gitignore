/* Local coordination tracking. No transport, clinical rules, or identity service. */
(function(root){
  'use strict';
  class CoordinationWorkspace {
    constructor(config, storage, clock = () => Date.now()) {
      this.config=config; this.storage=storage; this.clock=clock; this.raw=null;
      this.state={version:1,revision:0,records:[],events:[],followUpMinutes:config.followUpMinutes};
      this.load();
    }
    load() {
      let raw;
      try { raw=this.storage.getItem(this.config.storageKey); }
      catch { throw new Error('Local storage is unavailable. Records cannot be saved in this browser.'); }
      if(raw!==null){
        let data;
        try {data=JSON.parse(raw);} catch {throw new Error('Saved data cannot be read. It has been preserved; do not overwrite it.');}
        if(data.version!==1 || !Array.isArray(data.records) || !Array.isArray(data.events) ||
          !Number.isInteger(data.revision) || !Number.isFinite(data.followUpMinutes) || data.followUpMinutes<1 ||
          data.followUpMinutes>10080 || data.records.some(r=>!r.id || !r.fields || typeof r.fields!=='object' ||
            !['open','sent','retry','received'].includes(r.stage) || !Array.isArray(r.receipts) ||
            (r.stage==='sent' && !Number.isFinite(r.dueAt))) ||
          new Set(data.records.map(r=>r.id)).size!==data.records.length){
          throw new Error('Saved data has an unsupported format. It has been preserved.');
        }
        this.state=data;
      } else this.state={version:1,revision:0,records:[],events:[],followUpMinutes:this.config.followUpMinutes};
      this.raw=raw;
    }
    transaction(change) {
      let current;
      try { current=this.storage.getItem(this.config.storageKey); }
      catch {throw new Error('Cannot access saved data. Nothing was changed.');}
      if(current!==this.raw) throw new Error('Another tab changed this workspace. Reload before saving; your action was not applied.');
      const draft=JSON.parse(JSON.stringify(this.state));
      const result=change(draft);
      draft.revision++;
      const raw=JSON.stringify(draft);
      try { this.storage.setItem(this.config.storageKey,raw); }
      catch { throw new Error('Could not save locally. Nothing was changed. Export existing records and check browser storage.'); }
      this.state=draft; this.raw=raw;
      return result;
    }
    actor(value){if(!String(value||'').trim()) throw new Error('Enter the responsible person.'); return String(value).trim();}
    required(value,label){if(!String(value||'').trim()) throw new Error(`Enter ${label}.`); return String(value).trim();}
    find(state,id){const r=state.records.find(r=>r.id===id);if(!r)throw new Error('Record not found.');return r;}
    log(state,id,action,actor,detail){state.events.push({sequence:state.events.length+1,at:this.clock(),id,action,actor,detail});}
    missing(record){return this.config.fields.filter(f=>!String(record.fields[f.key]||'').trim()).map(f=>f.label);}
    status(record) {
      if(record.stage==='received')return 'Receipt recorded';
      if(record.stage==='retry')return 'Retry approved';
      if(record.stage==='sent')return this.clock()>=record.dueAt?'Follow-up overdue':'Awaiting receipt';
      return this.missing(record).length?'Needs information':'Ready for hand-off';
    }
    add(input,actor){
      actor=this.actor(actor);const id=this.required(input.id,'a record ID');
      const fields={};for(const f of this.config.fields)fields[f.key]=String(input[f.key]||'').trim();
      return this.transaction(s=>{
        const existing=s.records.find(r=>r.id===id);
        if(existing){
          const same=this.config.fields.every(f=>existing.fields[f.key]===fields[f.key]);
          this.log(s,id,same?'Duplicate entry retained':'Conflicting entry rejected',actor,
            same?'Existing record retained.':'Different details were not saved; review the existing record.');
          return {id,created:false,conflict:!same};
        }
        s.records.push({id,fields,stage:'open',owner:this.config.coordinator,createdAt:this.clock(),
          updatedAt:this.clock(),attempts:0,sentAt:null,dueAt:null,receipts:[],note:''});
        this.log(s,id,'Record created',actor,this.missing(s.records.at(-1)).length?'Missing information requires follow-up.':'Required information is complete.');
        return {id,created:true,conflict:false};
      });
    }
    edit(id,input,actor){
      actor=this.actor(actor);
      return this.transaction(s=>{
        const r=this.find(s,id);if(r.stage!=='open')throw new Error('Details cannot be edited after a hand-off is recorded.');
        for(const f of this.config.fields)r.fields[f.key]=String(input[f.key]||'').trim();
        r.updatedAt=this.clock();this.log(s,id,'Details updated',actor,this.missing(r).length?'Information is still missing.':'Required information is complete.');
      });
    }
    handoff(id,actor,reference){
      actor=this.actor(actor);reference=this.required(reference,'a hand-off reference');
      return this.transaction(s=>{
        const r=this.find(s,id);
        if(!['open','retry'].includes(r.stage)||this.missing(r).length)throw new Error('This record is not ready for hand-off.');
        r.stage='sent';r.sentAt=this.clock();r.dueAt=r.sentAt+s.followUpMinutes*60000;r.attempts++;
        r.updatedAt=this.clock();
        this.log(s,id,'Hand-off recorded',actor,`Attempt ${r.attempts}; reference ${reference}. Completed outside this application.`);
      });
    }
    receipt(id,actor,reference){
      actor=this.actor(actor);reference=this.required(reference,'the partner confirmation reference');
      return this.transaction(s=>{
        const r=this.find(s,id);if(!['sent','retry'].includes(r.stage))throw new Error('Receipt can only be recorded after hand-off.');
        if(r.receipts.some(x=>x.reference===reference))throw new Error('This receipt reference is already recorded.');
        r.stage='received';r.updatedAt=this.clock();r.receipts.push({reference,at:this.clock(),actor});
        this.log(s,id,'Receipt recorded',actor,`Partner confirmation: ${reference}. Receipt does not mean final business completion.`);
      });
    }
    approveRetry(id,actor,reason){
      actor=this.actor(actor);reason=this.required(reason,'the follow-up and retry reason');
      return this.transaction(s=>{
        const r=this.find(s,id);if(this.status(r)!=='Follow-up overdue')throw new Error('Retry approval requires an overdue hand-off.');
        r.stage='retry';r.updatedAt=this.clock();this.log(s,id,'Retry approved',actor,reason);
      });
    }
    note(id,actor,text){
      actor=this.actor(actor);text=this.required(text,'a coordination note');
      return this.transaction(s=>{const r=this.find(s,id);r.note=text;r.updatedAt=this.clock();this.log(s,id,'Follow-up recorded',actor,text);});
    }
    setFollowUp(minutes,actor){
      actor=this.actor(actor);minutes=Number(minutes);
      if(!Number.isInteger(minutes)||minutes<1||minutes>10080)throw new Error('Choose a whole number from 1 to 10080 minutes.');
      return this.transaction(s=>{s.followUpMinutes=minutes;this.log(s,'Workspace','Follow-up setting changed',actor,`${minutes} minutes; future hand-offs only.`);});
    }
    reset(confirmation){
      if(confirmation!=='RESET')throw new Error('Type RESET exactly to clear this workspace.');
      return this.transaction(s=>{s.records=[];s.events=[];s.followUpMinutes=this.config.followUpMinutes;});
    }
  }
  root.CoordinationWorkspace=CoordinationWorkspace;
  if(typeof module!=='undefined')module.exports=CoordinationWorkspace;
})(typeof globalThis!=='undefined'?globalThis:window);
