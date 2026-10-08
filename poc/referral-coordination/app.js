'use strict';
const config=window.WorkspaceConfig;
const $=id=>document.getElementById(id);
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const date=value=>value?new Date(value).toLocaleString():'—';
let workspace,editing=null,actionType=null,actionId=null,lastSignature='';
$('title').textContent=config.title;$('subtitle').textContent=config.subtitle;document.title=config.title;
$('add').textContent=`Add ${config.itemLabel.toLowerCase()}`;
$('id-caption').textContent=config.itemLabel+' ID';
$('history-id').textContent=config.itemLabel;
$('search').placeholder=config.searchHint||'ID or record details';
$('footer').textContent=config.footer||'Source records remain in their existing systems. A recorded receipt is not final business completion.';
$('records').setAttribute('aria-label',config.itemLabel+' records');
$('field-inputs').innerHTML=config.fields.map(f=>`<label>${esc(f.label)}<input name="${esc(f.key)}" maxlength="150"></label>`).join('');
function message(text,error=false){$('message').hidden=false;$('message').textContent=text;$('message').className=error?'error':'';}
function nextAction(r,status){
  if(status==='Needs information')return 'Obtain the missing details, then save changes.';
  if(status==='Ready for hand-off')return 'Complete the hand-off through the approved channel, then record its reference.';
  if(status==='Awaiting receipt')return 'Obtain partner confirmation and record its reference.';
  if(status==='Follow-up overdue')return 'Follow up with the provider. Record a receipt or approve a retry with a reason.';
  if(status==='Retry approved')return 'Record the next hand-off, or record a late partner confirmation if already received.';
  return config.receiptNextAction||'Follow the next agreed process step. Receipt is not final completion.';
}
function render(){
  if(!workspace)return;
  const all=workspace.state.records;
  const status=r=>workspace.status(r);
  lastSignature=all.map(r=>r.id+':'+status(r)).join('|');
  const counts=[['Total records',all.length],['Needs information',all.filter(r=>status(r)==='Needs information').length],['Overdue follow-up',all.filter(r=>status(r)==='Follow-up overdue').length],['Receipts recorded',all.filter(r=>status(r)==='Receipt recorded').length]];
  $('metrics').innerHTML=counts.map(([label,count])=>`<div class="metric"><strong>${count}</strong><span>${label}</span></div>`).join('');
  $('saved').textContent=`Local storage · Follow-up ${workspace.state.followUpMinutes} min · ${date(workspace.state.events.at(-1)?.at)}`;
  const search=$('search').value.toLowerCase().trim(),filter=$('filter').value;
  const records=all.filter(r=>(!filter||status(r)===filter)&&(!search||[r.id,...Object.values(r.fields)].join(' ').toLowerCase().includes(search)));
  $('records').innerHTML=records.length?records.map(r=>{
    const state=status(r),missing=workspace.missing(r);
    const type=state==='Needs information'?'warning':state==='Follow-up overdue'?'overdue':state==='Receipt recorded'?'received':state==='Awaiting receipt'?'waiting':'';
    const btn=(act,label)=>`<button class="${act==='handoff'?'':'secondary'}" data-action="${act}" data-id="${esc(r.id)}">${label}</button>`;
    let buttons=r.stage==='open'?btn('edit','Edit details'):'';
    if(['open','retry'].includes(r.stage)&&!missing.length)buttons+=btn('handoff','Record hand-off');
    if(['sent','retry'].includes(r.stage))buttons+=btn('receipt','Record receipt');
    if(state==='Follow-up overdue')buttons+=btn('retry','Approve retry');
    buttons+=btn('note','Add follow-up note');
    const timing=r.stage==='sent'?`<div><dt>Receipt follow-up due</dt><dd>${esc(date(r.dueAt))}</dd></div>`:'';
    return `<article class="record" data-record-id="${esc(r.id)}"><div class="record-head"><h2>${esc(r.id)}</h2><span class="tag ${type}">${esc(state)}</span></div><dl class="details">${config.fields.map(f=>`<div><dt>${esc(f.label)}</dt><dd>${esc(r.fields[f.key]||'Missing')}</dd></div>`).join('')}<div><dt>Responsible role</dt><dd>${esc(r.owner)}</dd></div><div><dt>Hand-off attempts</dt><dd>${r.attempts}</dd></div>${timing}</dl>${missing.length?`<p class="hint">Missing: ${esc(missing.join(', '))}</p>`:''}<div class="next"><strong>Next action:</strong> ${esc(nextAction(r,state))}</div>${r.note?`<p class="hint">Latest note: ${esc(r.note)}</p>`:''}<div class="buttons">${buttons}</div></article>`;
  }).join(''):`<div class="empty">${all.length?'No records match these filters.':`No records yet. Add a ${esc(config.itemLabel.toLowerCase())} to start, or load fictional examples.`}</div>`;
  $('history').innerHTML=[...workspace.state.events].reverse().map(e=>`<tr><td>${esc(date(e.at))}</td><td>${esc(e.id)}</td><td>${esc(e.action)}</td><td>${esc(e.actor)}</td><td>${esc(e.detail)}</td></tr>`).join('')||'<tr><td colspan="5">No recorded actions yet.</td></tr>';
}
function openEditor(id=null){
  editing=id;const form=$('edit-form');form.reset();$('edit-error').textContent='';
  $('edit-title').textContent=id?'Edit details':`Add ${config.itemLabel.toLowerCase()}`;
  form.elements.id.readOnly=!!id;
  if(id){const r=workspace.state.records.find(r=>r.id===id);form.elements.id.value=id;for(const f of config.fields)form.elements[f.key].value=r.fields[f.key];}
  $('editor').showModal();
}
function openAction(type,id=null){
  actionType=type;actionId=id;$('action-form').reset();$('action-error').textContent='';
  const info={
    handoff:['Record hand-off','Confirm that you completed the hand-off outside this application. This action records it; it sends no message.','Hand-off reference'],
    receipt:['Record partner receipt','Use a reference from an actual partner confirmation. This application records your statement; it does not verify it with the partner.','Partner confirmation reference'],
    retry:['Approve retry','Record the follow-up performed and why another attempt is appropriate. Approval does not itself perform the hand-off.','Follow-up and retry reason'],
    note:['Add follow-up note',config.noteHelp||'Record administrative coordination details only; do not include identifying or confidential information.','Coordination note'],
    settings:['Follow-up settings','Applies to future hand-offs only. Existing deadlines stay unchanged. This is a local working setting; agree the operational threshold with the business.','']
  }[type];
  $('action-title').textContent=info[0]+(id?' · '+id:'');$('action-help').textContent=info[1];$('detail-caption').textContent=info[2];
  $('detail-label').hidden=type==='settings';$('minutes-label').hidden=type!=='settings';
  $('action-form').elements.detail.required=type!=='settings';$('action-form').elements.minutes.required=type==='settings';
  $('action-form').elements.minutes.value=workspace.state.followUpMinutes;
  $('action-submit').textContent=type==='retry'?'Approve retry':'Save';$('action').showModal();
}
try{workspace=new CoordinationWorkspace(config,window.localStorage);render();}
catch(error){message(error.message,true);for(const id of ['add','examples','export','settings','reset'])$(id).disabled=true;}
$('add').onclick=()=>openEditor();$('settings').onclick=()=>openAction('settings');
$('search').oninput=render;$('filter').onchange=render;
document.querySelectorAll('[data-close]').forEach(button=>button.onclick=()=>button.closest('dialog').close());
$('edit-form').onsubmit=event=>{
  event.preventDefault();const form=event.target,input=Object.fromEntries(new FormData(form));
  try{
    if(editing){workspace.edit(editing,input,input.actor);message('Changes saved locally.');}
    else{const result=workspace.add(input,input.actor);message(result.created?'Record saved locally.':result.conflict?'Conflicting details were not saved. Review the existing record.':'This record already exists; the original was retained.',result.conflict);}
    $('editor').close();render();
  }catch(error){$('edit-error').textContent=error.message;}
};
$('records').onclick=event=>{const button=event.target.closest('[data-action]');if(!button)return;button.dataset.action==='edit'?openEditor(button.dataset.id):openAction(button.dataset.action,button.dataset.id);};
$('action-form').onsubmit=event=>{
  event.preventDefault();const input=Object.fromEntries(new FormData(event.target));
  try{
    if(actionType==='settings')workspace.setFollowUp(input.minutes,input.actor);
    else if(actionType==='handoff')workspace.handoff(actionId,input.actor,input.detail);
    else if(actionType==='receipt')workspace.receipt(actionId,input.actor,input.detail);
    else if(actionType==='retry')workspace.approveRetry(actionId,input.actor,input.detail);
    else workspace.note(actionId,input.actor,input.detail);
    $('action').close();message('Action saved locally.');render();
  }catch(error){$('action-error').textContent=error.message;}
};
$('examples').onclick=()=>{
  try{
    let added=0;
    for(const sample of config.examples)if(!workspace.state.records.some(r=>r.id===sample.id)){workspace.add(sample,'Example-data loader');added++;}
    message(`${added} fictional examples added. Existing records were retained.`);render();
  }catch(error){message(error.message,true);render();}
};
$('export').onclick=()=>{
  const data=new Blob([JSON.stringify(workspace.state,null,2)],{type:'application/json'});
  const url=URL.createObjectURL(data),link=document.createElement('a');link.href=url;link.download='coordination-records.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
};
$('reset').onclick=()=>{
  $('reset-form').reset();$('reset-error').textContent='';
  $('reset-summary').textContent=`This will delete ${workspace.state.records.length} record(s) and ${workspace.state.events.length} history entry/entries, and restore the ${config.followUpMinutes}-minute follow-up setting.`;
  $('reset-dialog').showModal();
};
$('reset-export').onclick=()=>$('export').click();
$('reset-form').onsubmit=event=>{
  event.preventDefault();
  try{
    workspace.reset(event.target.elements.confirmation.value);
    $('search').value='';$('filter').value='';$('reset-dialog').close();
    message('Workspace reset. Records and history were cleared; default follow-up settings restored.');render();
  }catch(error){$('reset-error').textContent=error.message;}
};
window.addEventListener('storage',event=>{
  if(event.key!==config.storageKey)return;
  if($('editor').open||$('action').open||$('reset-dialog').open){message('Another tab changed this workspace. Reload before saving your action.',true);return;}
  try{workspace.load();message('Changes from another tab loaded.');render();}catch(error){message(error.message,true);}
});
setInterval(()=>{
  if(workspace && workspace.state.records.map(r=>r.id+':'+workspace.status(r)).join('|')!==lastSignature)render();
},1000);
