const $ = s => document.querySelector(s);
const escape = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let records = [], selected = null, current = null, navigationVersion = 0;
async function api(path, data) {
  const response = await fetch(path, data ? {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)} : {});
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'Request failed');
  return result;
}
function notice(message) { $('#notice').textContent = message; }
function field(name, label, type='text', options=[]) {
  const id = `f-${name}`;
  const element = type === 'textarea' ? `<textarea id="${id}" name="${name}" required maxlength="4000"></textarea>` : type === 'select' ? `<select id="${id}" name="${name}" required><option value="">Choose…</option>${options.map(([value,title])=>`<option value="${escape(value)}">${escape(title)}</option>`).join('')}</select>` : `<input id="${id}" name="${name}" type="${type}" required maxlength="4000">`;
  return `<label for="${id}">${escape(label)}${element}</label>`;
}
const definitions = {
  update_case:['Correct case facts / ownership',[['title','Case title'],['problem','Expected vs observed condition','textarea'],['owner','Accountable owner'],['due','Due date','date']]],
  add_evidence:['Record evidence',[['title','Evidence title'],['source','Source / traceable record reference'],['observation','Objective observation','textarea']]],
  review_evidence:['Review evidence',[['id','Evidence','evidence'],['status','Review decision','status'],['rationale','Review rationale / limitations','textarea']]],
  contain:['Define containment',[['scope','Suspect population and boundaries','textarea'],['identification','Physical identification / hold control','textarea'],['owner','Accountable owner'],['due','Due date','date']]],
  confirm_containment:['Confirm containment executed',[['id','Containment record','containment'],['proof','Accepted execution evidence','proof']]],
  release_containment:['Record containment disposition',[['id','Containment record','containment'],['proof','Accepted release / disposition evidence','proof'],['disposition','Release authority, disposition and remaining controls','textarea']]],
  add_cause:['Propose cause',[['kind','Cause path','kind'],['claim','Cause hypothesis','textarea'],['mechanism','How this creates or lets the defect escape','textarea']]],
  verify_cause:['Verify cause',[['id','Cause','causes'],['proof','Accepted test evidence','proof'],['verification','Verification method / counterfactual test','textarea'],['result','Actual result and limitations','textarea']]],
  add_action:['Plan corrective action',[['cause','Verified cause','verified'],['title','Action'],['control','Control type','control'],['owner','Accountable owner'],['due','Due date','date'],['deliverable','Observable deliverable','textarea'],['metric','Effectiveness measure'],['target','Acceptance criterion'],['window','Required observation period / sample size']]],
  implement_action:['Verify implementation',[['id','Action','actions'],['proof','Accepted implementation evidence','proof']]],
  record_effectiveness:['Record effectiveness',[['id','Action','actions'],['proof','Accepted effectiveness evidence','proof'],['start','Observation start','date'],['end','Observation end','date'],['result','Measured result, sample size and comparison to target','textarea'],['outcome','Human judgment against planned criterion','outcome']]],
  close:['Close case',[['reason','Closure decision and remaining limitations','textarea']]],
  reopen:['Reopen case',[['reason','Reason for reopening','textarea']]]
};
function options(type,c) {
  const enums={status:['accepted','rejected','withdrawn'],kind:['occurrence','escape'],control:['prevention','detection'],outcome:['pass','fail']};
  if (enums[type]) return enums[type].map(v=>[v,v]);
  let list = c[type] || [];
  if (type === 'proof') list = c.evidence.filter(e=>e.status === 'accepted');
  if (type === 'verified') list = c.causes.filter(e=>c.evidence.some(p=>p.id === e.proof && p.status === 'accepted'));
  return list.map(v=>[v.id,`${v.title || v.claim || v.scope} (${v.id.slice(0,8)})`]);
}
function showOperation() {
  const c = current.case, operation = $('#operation').value;
  $('#fields').innerHTML = definitions[operation][1].map(([name,label,type='text']) => ['text','date','textarea'].includes(type) ? field(name,label,type) : field(name,label,'select',options(type,c))).join('');
  if (operation === 'update_case') for (const key of ['title','problem','owner','due']) document.querySelector(`[name="${key}"]`).value=c[key];
  $('#operation-help').textContent = operation === 'review_evidence' ? 'Accepted means you reviewed this record. The software cannot establish physical truth. Withdrawal immediately invalidates dependent closure readiness.' : operation === 'record_effectiveness' ? 'Compare actual results with the measure, acceptance criterion and sample window planned on the action. A checkbox alone is not effectiveness.' : 'Record what happened and link the relevant proof. All successful changes are retained in the event history.';
}
function card(title, content) {return `<section class="card"><h2>${title}</h2>${content}</section>`;}
function rows(items, render) {return items.length ? items.map(i=>`<article class="record">${render(i)}</article>`).join('') : '<p class="muted">No records yet.</p>';}
function render(c,gaps,history) {
  const accepted = id => c.evidence.some(e=>e.id === id && e.status === 'accepted');
  $('#main').innerHTML = `<p class="eyebrow">INVESTIGATION WORKSPACE · ${escape(c.id.slice(0,8))}</p><h1>${escape(c.title)}</h1><p class="subtitle">${escape(c.problem)}</p><div class="meta"><span class="pill ${c.closed?'green':'orange'}">${c.closed?'Closed':'Open investigation'}</span><span class="pill">Owner: ${escape(c.owner)}</span><span class="pill">Due: ${escape(c.due)}</span><span class="pill">Revision ${c.version}</span></div><div class="flow"><span>01 · Evidence</span><span>02 · Failure mechanism</span><span>03 · Verified cause</span><span>04 · Corrective action</span><span>05 · Effectiveness</span></div><div class="grid"><div>${card('Closure readiness',gaps.length?`<p class="muted">Close these evidence gaps before closing the case.</p><ul>${gaps.map(g=>`<li>${escape(g)}</li>`).join('')}</ul>`:'<p class="pill green">Required records present. Human closure review required.</p>')}${card('Containment',rows(c.containment,i=>`<h3>${escape(i.scope)}</h3><p>${escape(i.identification)}</p><small>${escape(i.owner)} · ${escape(i.due)}</small><p>${accepted(i.proof)?'Execution proof accepted':'Execution proof missing'} · ${accepted(i.release_proof)?'Disposition proof accepted':'Disposition pending'}</p><p>${escape(i.disposition || '')}</p>`))}${card('Occurrence & escape causes',rows(c.causes,i=>`<span class="pill ${accepted(i.proof)?'green':'orange'}">${escape(i.kind)} · ${accepted(i.proof)?'Verified record':'Hypothesis'}</span><h3>${escape(i.claim)}</h3><p><b>Mechanism:</b> ${escape(i.mechanism)}</p><p>${escape(i.verification || 'Verification not recorded')}</p><p>${escape(i.result || '')}</p>`))}${card('Corrective actions',rows(c.actions,i=>`<span class="pill">${escape(i.control)}</span><h3>${escape(i.title)}</h3><small>${escape(i.owner)} · ${escape(i.due)} · Cause ${escape(i.cause.slice(0,8))}</small><p><b>Deliverable:</b> ${escape(i.deliverable)}</p><p><b>Effectiveness plan:</b> ${escape(i.metric)}; target ${escape(i.target)}; ${escape(i.window)}</p><p>${accepted(i.proof)?'Implementation evidence accepted':'Implementation pending'}</p><p><b>Result:</b> ${escape(i.effectiveness?.result || 'Not yet demonstrated')} ${i.effectiveness?'('+escape(i.effectiveness.outcome)+')':''}</p>`))}</div><div>${card(c.closed?'Reopen investigation':'Update the investigation',`<form id="update">${field('actor','Recorded by')}<label>What happened?<select id="operation" name="operation">${Object.entries(definitions).filter(([k])=>c.closed?k==='reopen':k!=='reopen').map(([k,[label]])=>`<option value="${k}">${label}</option>`).join('')}</select></label><p class="muted" id="operation-help"></p><div id="fields"></div><button class="primary" type="submit">Save record</button></form>`)}${card('Evidence register',`<p class="muted">Sources are references and text observations in v0.1. Files are not uploaded or preserved.</p>${rows(c.evidence,i=>`<span class="pill ${i.status==='accepted'?'green':'orange'}">${escape(i.status)}</span><h3>${escape(i.title)}</h3><small>${escape(i.id.slice(0,8))} · ${escape(i.source)}</small><p>${escape(i.observation)}</p>${i.reviewer?`<p>Reviewed by ${escape(i.reviewer)}: ${escape(i.rationale)}</p>`:''}`)}`)}${card('Event history',`<p class="muted">Append-only through this app. Operator names are self-reported. Database administrators can alter the file.</p>${rows(history.slice().reverse(),i=>`<small>${escape(i.at)}</small><p><b>${escape(i.operation.replaceAll('_',' '))}</b> · ${escape(i.actor)}</p><details><summary>Inspect recorded change</summary><pre>${escape(JSON.stringify(JSON.parse(i.command),null,2))}</pre></details>`)}`)}<button id="print">Print investigation</button></div></div>`;
  $('#operation').value=c.closed?'reopen':'add_evidence'; $('#operation').onchange=showOperation; showOperation();
  $('#update').onsubmit=async e=>{e.preventDefault();const payload=Object.fromEntries(new FormData(e.target));payload.version=c.version;try{await api(`/api/cases/${c.id}`,payload);notice('Record saved.');await load(c.id);}catch(error){notice(error.message);}};
  $('#print').onclick=()=>window.print();
}
function sidebar() {
  const query=$('#search').value.toLowerCase();
  $('#cases').innerHTML=records.filter(r=>`${r.case.title} ${r.case.owner}`.toLowerCase().includes(query)).map(r=>`<button data-case="${escape(r.case.id)}" class="${selected===r.case.id?'active':''}">${escape(r.case.title)}<small>${r.case.closed?'Closed':r.gaps.length+' closure gaps'} · ${escape(r.case.owner)}</small></button>`).join('');
  document.querySelectorAll('[data-case]').forEach(b=>b.onclick=()=>load(b.dataset.case));
}
async function load(id) {
  const version = ++navigationVersion;
  const nextRecords = await api('/api/cases');
  if (version !== navigationVersion) return;
  records=nextRecords; selected=id || records[0]?.case.id; sidebar();
  if(selected){
    const next = await api(`/api/cases/${selected}`);
    if (version !== navigationVersion) return;
    current=next; render(current.case,current.gaps,current.history);
  }
  else newCase();
}
function newCase() {
  ++navigationVersion;
  selected=null;sidebar();$('#main').innerHTML=`<p class="eyebrow">START WITH AN OBSERVABLE GAP</p><h1>New corrective-action case</h1><p class="subtitle">Describe what happened, who owns the investigation and when the next decision is due. Add containment and evidence after saving.</p>${card('Problem definition',`<form id="create">${field('title','Case title')}${field('problem','Expected condition vs observed condition, extent and timing','textarea')}<div class="two">${field('owner','Accountable case owner')}${field('due','Due date','date')}</div>${field('actor','Recorded by')}<button class="primary">Create case</button></form>`)}`;
  $('#create').onsubmit=async e=>{e.preventDefault();try{const result=await api('/api/cases',Object.fromEntries(new FormData(e.target)));notice('Case created. Define containment next.');await load(result.case.id);}catch(error){notice(error.message);}};
}
$('#new').onclick=newCase;$('#search').oninput=sidebar;
load().catch(e=>notice(e.message));
