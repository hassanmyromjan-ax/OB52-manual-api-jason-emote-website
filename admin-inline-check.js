
const $ = id => document.getElementById(id);
let STATE = null, timer = null;

async function api(path, method='GET', body=null) {
  const opt = {method, credentials:'same-origin', headers:{}};
  if (body) { opt.headers['Content-Type']='application/json'; opt.body=JSON.stringify(body); }
  const r = await fetch(BASE + path, opt);
  let d = {}; try { d = await r.json(); } catch(e) {}
  if (r.status === 401 && path !== '/api/login') { showLogin(); throw new Error('unauthorized'); }
  return d;
}
const BASE = location.pathname.replace(/\/+$/,'');

function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function showLogin(){ clearInterval(timer); $('login-view').classList.remove('hidden'); $('panel-view').classList.add('hidden'); }
function showPanel(){ $('login-view').classList.add('hidden'); $('panel-view').classList.remove('hidden'); }

async function login(){
  $('login-msg').textContent='';
  $('login-btn').disabled = true;
  try {
    const d = await api('/api/login','POST',{password:$('pw').value});
    if (d.ok) { $('pw').value=''; await refresh(); showPanel(); timer=setInterval(refresh,4000); }
    else $('login-msg').textContent = d.error || 'Login failed';
  } catch(e) {}
  $('login-btn').disabled = false;
}

async function refresh(){
  try {
    const d = await api('/api/state');
    if (!d.ok) return;
    STATE = d; render();
  } catch(e) {}
}

const STATUS_TXT = {online:'ONLINE', connecting:'CONNECTING', error:'PROBLEM / BAN?', offline:'OFFLINE'};

function serverName(id){ const s=(STATE.servers||[]).find(x=>x.id===id); return s?s.name:'?'; }

function applyScope(){
  const clone = STATE.scope === 'clone';
  $('clone-btn').classList.toggle('hidden', clone);
  if (!clone) { $('clone-btn').href = BASE + '/clones'; }
  if (clone) document.title = (STATE.clone_name || 'CLONE') + ' — ADMIN';
  $('panel-title').innerHTML = clone ? '<i class="fas fa-robot"></i> ' + esc(STATE.clone_name) + ' — ADMIN' : '<i class="fas fa-robot"></i> AX ADMIN PANEL';
  const ban = $('scope-banner'); let html = '';
  if (clone && STATE.expires_at) {
    const left = (STATE.expires_at*1000 - Date.now())/86400000;
    html += '⏳ মেয়াদ শেষ: <b>' + new Date(STATE.expires_at*1000).toLocaleString() + '</b> (' + (left>0 ? left.toFixed(1)+' দিন বাকি' : 'শেষ') + ')<br>';
  } else if (clone) { html += '⏳ মেয়াদ: <b>Unlimited</b><br>'; }
  if (STATE.shared) html += '🔗 এই ওয়েবসাইট <b>অরিজিনাল সার্ভারের bot</b> ব্যবহার করছে — এখানে আলাদা bot/server যোগ করার দরকার নেই।';
  ban.innerHTML = html; ban.classList.toggle('hidden', !html);
  ['add-card','bots-card','srv-card','backup-card'].forEach(id => $(id).classList.toggle('hidden', !!STATE.shared));
  $('login-mode-card').classList.toggle('hidden', clone);
  $('guest-api-card').classList.toggle('hidden', clone);
  $('admin-password-card').classList.toggle('hidden', clone);
  $('clone-auto-leave-card').classList.toggle('hidden', !clone || !!STATE.shared);
  $('json-active-section').classList.toggle('hidden', clone);
  $('json-pool-controls').classList.toggle('hidden', clone);
  if (clone && !STATE.shared) {
    $('clone-auto-leave').checked = STATE.site?.auto_leave !== false;
    $('clone-auto-leave-state').textContent = $('clone-auto-leave').checked ? 'ON' : 'OFF';
  }
}


// ===== SOCIAL LIST WIDGET: "ADD" বাটন → নাম → লিংক → ADD (add / edit / delete) =====
function makeSocialList(rootId, cfg){
  const root = document.getElementById(rootId);
  const MAX = cfg.max || 8;
  let items = [], editIdx = -1;
  root.innerHTML = `<div class="sl-items"></div>
    <button type="button" class="sm b-edit sl-add">＋ ${cfg.addText}</button>
    <div class="sl-form hidden">
      <label>${cfg.nameLabel}</label>
      <input type="text" class="sl-in-name" maxlength="40" placeholder="${cfg.namePh || ''}">
      <label>${cfg.linkLabel}</label>
      <input type="text" class="sl-in-link" maxlength="300" placeholder="https://...">
      <div class="row"><button type="button" class="sl-cancel">CANCEL</button><button type="button" class="sl-ok">ADD</button></div>
      <div class="msg sl-msg"></div>
    </div>`;
  const $q = s => root.querySelector(s);
  const listEl = $q('.sl-items'), form = $q('.sl-form'), addBtn = $q('.sl-add');
  const inName = $q('.sl-in-name'), inLink = $q('.sl-in-link'), okBtn = $q('.sl-ok'), msg = $q('.sl-msg');
  const escH = s => String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  function draw(){
    listEl.innerHTML = items.length ? items.map((x,i)=>`<div class="sl-item"><div class="sl-info"><div class="sl-name">${escH(x.name)}</div><div class="sl-link">${escH(x.link)}</div></div>
      <div class="sl-btns"><button type="button" class="b-edit" data-e="${i}" title="Edit">✎</button><button type="button" class="b-del" data-d="${i}" title="Delete">✕</button></div></div>`).join('')
      : `<div class="sl-empty">${cfg.emptyText || 'এখনো কিছু যোগ করা হয়নি'}</div>`;
    addBtn.classList.toggle('hidden', items.length >= MAX || !form.classList.contains('hidden'));
  }
  function openForm(i){
    editIdx = i;
    inName.value = i>=0 ? items[i].name : ''; inLink.value = i>=0 ? items[i].link : '';
    okBtn.textContent = i>=0 ? 'SAVE' : 'ADD'; msg.textContent = '';
    form.classList.remove('hidden'); addBtn.classList.add('hidden'); inName.focus();
  }
  function closeForm(){ form.classList.add('hidden'); editIdx = -1; draw(); }

  async function commit(next){
    const prev = items; items = next; draw();
    if (cfg.onChange) {
      const ok = await cfg.onChange(items.map(x=>({name:x.name, link:x.link})));
      if (ok === false) { items = prev; draw(); }
    }
  }
  addBtn.onclick = () => openForm(-1);
  $q('.sl-cancel').onclick = closeForm;
  okBtn.onclick = async () => {
    const name = inName.value.trim(), link = inLink.value.trim();
    if (!name) { msg.className='msg sl-msg bad'; msg.textContent='নাম দিন'; return; }
    if (!/^https?:\/\/[^\s'"<>\\]{3,300}$/.test(link)) { msg.className='msg sl-msg bad'; msg.textContent='সঠিক লিংক দিন (https:// দিয়ে শুরু)'; return; }
    const next = items.slice();
    if (editIdx >= 0) next[editIdx] = {name, link}; else next.push({name, link});
    form.classList.add('hidden'); editIdx = -1;
    await commit(next);
  };
  listEl.onclick = e => {
    const b = e.target.closest('button'); if (!b) return;
    if (b.dataset.e !== undefined) openForm(+b.dataset.e);
    else if (b.dataset.d !== undefined) { if (confirm('এটি মুছে ফেলবেন?')) commit(items.filter((_,i)=>i!==+b.dataset.d)); }
  };
  draw();
  return {
    set(list){ if (!form.classList.contains('hidden')) return; items = (list||[]).map(x=>({name:x.name, link:x.link})); draw(); },
    get(){ return items.slice(); }
  };
}

let TASKW = null, SOCW = null;
function initSiteWidgets(){
  TASKW = makeSocialList('task-widget', {addText:'ADD TASK LINK', nameLabel:'TASK NAME', namePh:'যেমন: JOIN TELEGRAM', linkLabel:'TASK LINK', emptyText:'কোনো টাস্ক লিংক নেই',
    onChange: items => saveSitePart({tasks: items})});
  SOCW = makeSocialList('social-widget', {addText:'ADD SOCIAL MEDIA', nameLabel:'SOCIAL MEDIA NAME', namePh:'যেমন: TELEGRAM / YOUTUBE', linkLabel:'LINK', emptyText:'কোনো Social Media বাটন নেই',
    onChange: items => saveSitePart({social_links: items})});
}
async function saveSitePart(body){
  const m=$('site-msg'); m.className='msg'; m.textContent='';
  try {
    const d = await api('/api/site','PUT',body);
    if (d.ok) { m.className='msg ok'; m.textContent='✔ সেভ হয়েছে'; if (d.site) STATE.site = d.site; return true; }
    m.className='msg bad'; m.textContent = d.error || 'Save failed'; refresh(); return false;
  } catch(e) { return false; }
}
function updateSiteToggles(){
  $('site-tasks-state').textContent = $('site-tasks-on').checked ? 'ON' : 'OFF';
  $('site-maint-state').textContent = $('site-maintenance').checked ? 'ON' : 'OFF';
}
async function saveMaintenance(){
  const ok = await saveSitePart({maintenance:$('site-maintenance').checked, notice:$('site-notice').value});
  if (ok) $('site-msg').textContent = '✔ Maintenance সেভ হয়েছে';
}

function render(){
  applyScope();
  if(STATE.site){
    const ae = document.activeElement && document.activeElement.id;
    if(!['site-notice'].includes(ae)){ $('site-notice').value = STATE.site.notice || ''; }
    $('site-maintenance').checked = STATE.site.maintenance === 'on';
    $('site-tasks-on').checked = STATE.site.tasks_enabled !== false;
    updateSiteToggles();
    if(TASKW) TASKW.set(STATE.site.tasks || []);
    if(SOCW) SOCW.set(STATE.site.social_links || []);
    $('api-name').value = STATE.site.api_name || 'AX-ROM';
  }

  // server dropdowns (add form keeps selection)
  const cur = $('bot-server').value;
  const opts = STATE.servers.map(s=>`<option value="${esc(s.id)}">${esc(s.name)}</option>`).join('');
  $('bot-server').innerHTML = opts || '<option value="">— আগে সার্ভার যোগ করুন —</option>';
  if (cur) $('bot-server').value = cur;
  const apiCur=$('api-server').value;
  const serverOpts=STATE.servers.map(s=>`<option value="${esc(s.id)}">${esc(s.name)}</option>`).join('');
  $('api-server').innerHTML=serverOpts;
  if(apiCur) $('api-server').value=apiCur;
  if(!['auth-mode','auto-leave'].includes(document.activeElement?.id)){ $('auth-mode').value=STATE.site?.auth_mode || 'manual'; $('auto-leave').checked=STATE.site?.auto_leave !== false; }
  const selectedApiServer=STATE.servers.find(s=>s.id===$('api-server').value) || STATE.servers[0];
  if(selectedApiServer){ $('api-server').value=selectedApiServer.id; if(!['api-url','api-name'].includes(document.activeElement?.id)) $('api-url').value=selectedApiServer.api_url || (STATE.site?.api_urls||{})[selectedApiServer.region] || ''; }
  const savedApis=(STATE.servers||[]).filter(s=>s.api_url);
  $('saved-api-list').innerHTML=savedApis.length ? '<b>SAVED SERVER API</b><br>'+savedApis.map(s=>`${esc(s.name)}: <code>${esc(s.api_url)}</code>`).join('<br>') : 'এখনো কোনো Server API Save করা হয়নি।';
  $('auto-leave-state').textContent=$('auto-leave').checked?'ON':'OFF';
  if (!$('new-region').options.length)
    $('new-region').innerHTML = STATE.regions.map(r=>`<option value="${r.code}" data-label="${esc(r.label)}">${esc(r.label)} (${r.code})</option>`).join('');

  // bots
  const manualBots=STATE.bots.filter(b=>b.source!=='json'); const jsonBots=STATE.bots.filter(b=>b.source==='json');
  $('bot-count').textContent = `(${manualBots.length})`; $('json-bot-count').textContent=`(${jsonBots.length})`;
  $('bot-list').innerHTML = manualBots.length ? manualBots.map(b=>`
    <div class="bot">
      <div class="bot-top">
        <span class="bot-name"><i class="fas fa-robot" style="color:var(--primary)"></i> ${esc(b.name)}</span>
        <span class="badge s-${esc(b.status)}">${STATUS_TXT[b.status]||esc(b.status)}</span>
      </div>
      <div class="meta">SERVER: ${esc(serverName(b.server_id))}<br>
        GUEST UID: ${esc(b.uid)}${b.bot_uid?` &nbsp;|&nbsp; GAME UID: ${esc(b.bot_uid)}`:''}
        ${b.team_code?` &nbsp;|&nbsp; TEAM CODE: <b>${esc(b.team_code)}</b> <button class="sm b-edit" onclick="copyTeamCode('${esc(b.team_code)}')">COPY</button>`:''}
        ${b.remaining_seconds!==null && b.remaining_seconds!==undefined?` &nbsp;|&nbsp; TIME LEFT: ${Math.floor(b.remaining_seconds/60)}m ${b.remaining_seconds%60}s`:''}
        ${b.queue?` &nbsp;|&nbsp; QUEUE: ${b.queue}`:''}${b.restarts?` &nbsp;|&nbsp; RESTARTS: ${b.restarts}`:''}</div>
      ${b.error && b.status!=='online' ? `<div class="err"><i class="fas fa-triangle-exclamation"></i> ${esc(b.error)}</div>`:''}
      <div class="acts">
        <button class="sm b-edit" onclick="openEdit('${esc(b.id)}')"><i class="fas fa-pen"></i> EDIT</button>
        <button class="sm b-rst" onclick="restartBot('${esc(b.id)}')"><i class="fas fa-rotate"></i> RESTART</button>
        <button class="sm b-del" onclick="delBot('${esc(b.id)}','${esc(b.name)}')"><i class="fas fa-trash"></i> DELETE</button>
      </div>
    </div>`).join('') : '<div class="meta">কোনো Manual/API bot নেই।</div>';
  $('json-bot-list').innerHTML = jsonBots.length ? jsonBots.map(b=>`
    <div class="bot"><div class="bot-top"><span class="bot-name"><i class="fas fa-file-code" style="color:var(--primary)"></i> ${esc(b.name)}</span><span class="badge s-${esc(b.status)}">${STATUS_TXT[b.status]||esc(b.status)}</span></div>
    <div class="meta">SERVER: ${esc(serverName(b.server_id))}<br>UID: ${esc(b.uid)} ${b.team_code?` | TEAM CODE: <b>${esc(b.team_code)}</b> <button class="sm b-edit" onclick="copyTeamCode('${esc(b.team_code)}')">COPY</button>`:''}<br>${b.remaining_seconds!==null&&b.remaining_seconds!==undefined?`TIME LEFT: ${Math.floor(b.remaining_seconds/60)}m ${b.remaining_seconds%60}s`:'WAITING FOR CONNECTION'}${b.error?`<div class="err">${esc(b.error)}</div>`:''}</div>
    <div class="acts"><button class="sm b-edit" onclick="openEdit('${esc(b.id)}')">EDIT</button><button class="sm b-rst" onclick="restartBot('${esc(b.id)}')">RESTART</button><button class="sm b-del" onclick="delBot('${esc(b.id)}','${esc(b.name)}')">DELETE</button></div></div>`).join(''):'<div class="meta">কোনো active JSON bot নেই।</div>';

  // servers
  $('srv-list').innerHTML = STATE.servers.map(s=>{
    const n = STATE.bots.filter(b=>b.server_id===s.id).length;
    const jc=(STATE.json_pool_counts||{})[s.id]||{total:0,active:0,available:0};
    return `<div class="srv" style="align-items:flex-start;gap:8px"><div style="flex:1"><b>${esc(s.name)}</b> <span style="color:#777;font-size:10px">[${esc(s.region)}] • ${n} active</span>
      <div class="meta">LOGIN: ${((STATE.scope==='clone'?STATE.public_auth_mode:STATE.site.auth_mode)||'manual').toUpperCase()}${STATE.scope==='clone'?'':` • JSON: ${jc.total} saved • ${jc.active} active • ${jc.available} available`}</div></div>
      <button class="sm b-del" onclick="delServer('${esc(s.id)}')"><i class="fas fa-trash"></i></button></div>`;
  }).join('') || '<div class="meta">কোনো সার্ভার নেই</div>';
  const jcur=$('json-server').value; $('json-server').innerHTML=STATE.servers.map(s=>`<option value="${esc(s.id)}">${esc(s.name)}</option>`).join(''); if(jcur) $('json-server').value=jcur;
}

async function addBot(){
  const m = $('add-msg'); m.className='msg'; m.textContent='';
  $('start-btn').disabled = true;
  try {
    const d = await api('/api/bots','POST',{server_id:$('bot-server').value,name:$('bot-name').value,uid:$('bot-uid').value,password:$('bot-pw').value});
    if (d.ok) { m.className='msg ok'; m.textContent='✔ Bot যোগ হয়েছে, চালু হচ্ছে...';
      $('bot-name').value=''; $('bot-uid').value=''; $('bot-pw').value=''; refresh(); }
    else { m.className='msg bad'; m.textContent = d.error||'Error'; }
  } catch(e) {}
  $('start-btn').disabled = false;
}

function openEdit(id){
  const b = STATE.bots.find(x=>x.id===id); if(!b) return;
  $('e-id').value=id; $('e-name').value=b.name; $('e-uid').value=b.uid; $('e-pw').value='';
  $('e-server').innerHTML = STATE.servers.map(s=>`<option value="${esc(s.id)}">${esc(s.name)}</option>`).join('');
  $('e-server').value=b.server_id; $('e-msg').textContent='';
  $('edit-modal').classList.add('show');
}
async function saveEdit(){
  const body={server_id:$('e-server').value,name:$('e-name').value,uid:$('e-uid').value};
  if($('e-pw').value) body.password=$('e-pw').value;
  const d = await api('/api/bots/'+$('e-id').value,'PUT',body);
  if(d.ok){ $('edit-modal').classList.remove('show'); refresh(); }
  else { $('e-msg').className='msg bad'; $('e-msg').textContent=d.error||'Error'; }
}
async function restartBot(id){ await api('/api/bots/'+id+'/restart','POST'); refresh(); }
async function delBot(id,name){
  if(!confirm(`"${name}" বট একেবারে ডিলেট করবেন? Main UI থেকেও মুছে যাবে।`)) return;
  const d = await api('/api/bots/'+id,'DELETE'); if(!d.ok) alert(d.error||'Error'); refresh();
}
async function addServer(){
  const m=$('srv-msg'); m.className='msg'; m.textContent='';
  const d = await api('/api/servers','POST',{name:$('new-srv-name').value,region:$('new-region').value});
  if(d.ok){ $('new-srv-name').value=''; m.className='msg ok'; m.textContent='✔ সার্ভার যোগ হয়েছে'; refresh(); }
  else { m.className='msg bad'; m.textContent=d.error||'Error'; }
}
async function delServer(id){
  if(!confirm('এই সার্ভার ডিলেট করবেন?')) return;
  const d = await api('/api/servers/'+id,'DELETE'); if(!d.ok) alert(d.error||'Error'); refresh();
}

initSiteWidgets();
$('site-save').onclick = saveMaintenance;

$('site-tasks-on').onchange = async () => { updateSiteToggles(); const ok = await saveSitePart({tasks_enabled:$('site-tasks-on').checked}); if(!ok) refresh(); };
$('site-maintenance').onchange = updateSiteToggles;
$('login-btn').onclick = login;
$('pw').addEventListener('keydown',e=>{ if(e.key==='Enter') login(); });
$('logout-btn').onclick = async()=>{ await api('/api/logout','POST'); showLogin(); };
async function updateOriginalServerMode(){
  const mode=$('auth-mode').value, auto_leave=$('auto-leave').checked, msg=$('login-config-msg');
  const d=await api('/api/site','PUT',{auth_mode:mode,auto_leave});
  msg.className=d.ok?'msg ok':'msg bad'; msg.textContent=d.ok?'✔ Original Website category and Auto Leave updated':(d.error||'Update failed');
  if(d.ok) refresh();
}
async function saveServerApi(){
  const id=$('api-server').value, msg=$('api-config-msg');
  const cfg=await api('/api/site','PUT',{api_name:$('api-name').value});
  if(!cfg.ok){msg.className='msg bad';msg.textContent=cfg.error||'API name save failed';return;}
  const d=await api('/api/servers/'+encodeURIComponent(id)+'/api-config','PUT',{api_url:$('api-url').value});
  msg.className=d.ok?'msg ok':'msg bad'; msg.textContent=d.ok?'✔ Guest API URL saved for selected server':(d.error||'Save failed');
  if(d.ok) refresh();
}
function copyTeamCode(code){navigator.clipboard.writeText(String(code)).then(()=>alert('Team Code copied')).catch(()=>alert(code));}
async function uploadJsonAccounts(){
  const file=$('json-file').files[0], msg=$('json-msg'); if(!file){msg.className='msg bad';msg.textContent='JSON file নির্বাচন করুন';return;}
  try{
    const raw=JSON.parse(await file.text()); const accounts=Array.isArray(raw)?raw:raw.accounts;
    if(!Array.isArray(accounts)) throw new Error('Format: {"accounts":[{"uid":"...","password":"..."}]}');
    const d=await api('/api/json-accounts','POST',{server_id:$('json-server').value,accounts});
    msg.className=d.ok?'msg ok':'msg bad'; msg.textContent=d.ok?`✔ ${d.count} accounts saved for selected server`:d.error||'Upload failed'; refresh();
  }catch(e){msg.className='msg bad';msg.textContent=e.message||'Invalid JSON file';}
}
async function jsonBulk(action){if(!confirm(action==='delete'?'সব active JSON bot delete করবেন?':'সব active JSON bot restart করবেন?'))return;const d=await api('/api/json-bots/bulk','POST',{action});alert(d.ok?`${d.count} JSON bot ${action} queued`:d.error||'Failed');refresh();}
async function saveCloneAutoLeave(){
  const msg=$('clone-auto-leave-msg');
  const d=await api('/api/site','PUT',{auto_leave:$('clone-auto-leave').checked});
  msg.className=d.ok?'msg ok':'msg bad'; msg.textContent=d.ok?'✔ Clone Auto Leave updated':(d.error||'Update failed');
  if(d.ok) refresh();
}
async function changeAdminPassword(){
  const msg=$('admin-password-msg');
  const body={current_password:$('admin-current-password').value,new_password:$('admin-new-password').value,confirm_password:$('admin-confirm-password').value};
  const d=await api('/api/password-change','POST',body);
  msg.className=d.ok?'msg ok':'msg bad'; msg.textContent=d.ok?'✔ Admin Password changed successfully':(d.error||'Password change failed');
  if(d.ok){$('admin-current-password').value='';$('admin-new-password').value='';$('admin-confirm-password').value='';}
}
$('clone-auto-leave').addEventListener('change',()=>{$('clone-auto-leave-state').textContent=$('clone-auto-leave').checked?'ON':'OFF';});
$('save-clone-auto-leave').onclick=saveCloneAutoLeave;
$('change-admin-password').onclick=changeAdminPassword;
$('save-login-config').onclick=updateOriginalServerMode;
$('auto-leave').addEventListener('change',()=>{$('auto-leave-state').textContent=$('auto-leave').checked?'ON':'OFF';});
$('save-api-config').onclick=saveServerApi;
$('api-server').addEventListener('change',()=>{const srv=STATE.servers.find(x=>x.id===$('api-server').value);if(srv){$('api-url').value=srv.api_url||(STATE.site?.api_urls||{})[srv.region]||'';}});
$('json-upload-btn').onclick=uploadJsonAccounts;
$('json-restart-all').onclick=()=>jsonBulk('restart');
$('json-delete-all').onclick=()=>jsonBulk('delete');
$('start-btn').onclick = addBot;
$('add-srv-btn').onclick = addServer;
$('e-cancel').onclick = ()=>$('edit-modal').classList.remove('show');
$('e-save').onclick = saveEdit;
$('new-region').addEventListener('change',()=>{ const o=$('new-region').selectedOptions[0]; if(o && !$('new-srv-name').value) $('new-srv-name').value=o.dataset.label; });


async function exportBackup(){
  const d = await api('/api/export'); const t = JSON.stringify(d);
  $('backup-text').value = t;
  try { await navigator.clipboard.writeText(t); $('bk-msg').className='msg ok'; $('bk-msg').textContent='✔ কপি হয়েছে — নিরাপদ জায়গায় রাখুন (এতে password আছে)'; }
  catch(e) { $('bk-msg').className='msg ok'; $('bk-msg').textContent='উপরের বক্সের লেখাটি কপি করে রাখুন (এতে password আছে)'; }
}
async function importBackup(){
  let obj; try { obj = JSON.parse($('backup-text').value); } catch(e) { $('bk-msg').className='msg bad'; $('bk-msg').textContent='ভুল JSON'; return; }
  if(!confirm('বর্তমান সব bot/server মুছে এই backup দিয়ে বদলানো হবে। চালিয়ে যাবেন?')) return;
  const d = await api('/api/import','POST',obj);
  if(d.ok){ $('bk-msg').className='msg ok'; $('bk-msg').textContent=`✔ ${d.servers} server, ${d.bots} bot ফিরিয়ে আনা হয়েছে`; $('backup-text').value=''; refresh(); }
  else { $('bk-msg').className='msg bad'; $('bk-msg').textContent=d.error||'Error'; }
}
$('exp-btn').onclick = exportBackup;
$('imp-btn').onclick = importBackup;

// start: already logged in?
(async()=>{ try{ const d=await api('/api/state'); if(d.ok){ STATE=d; render(); showPanel(); timer=setInterval(refresh,4000); return; } }catch(e){} showLogin(); })();
