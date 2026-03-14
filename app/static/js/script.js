// THEME
const themeBtn = document.getElementById('themeBtn');
let isLight = false;
themeBtn.onclick = () => {
  isLight = !isLight;
  document.body.classList.toggle('light-mode', isLight);
  themeBtn.innerHTML = isLight
    ? '<i class="bi bi-moon-fill me-1"></i> Dark Mode'
    : '<i class="bi bi-sun-fill me-1"></i> Light Mode';
};

const txt           = document.getElementById('txt');
const checkBtn      = document.getElementById('checkBtn');
const resultBox     = document.getElementById('resultBox');
const resultIcon    = document.getElementById('resultIcon');
const resultLabelEl = document.getElementById('resultLabelEl');
const resultPct     = document.getElementById('resultPct');
const probFill      = document.getElementById('probFill');
const resultPreview = document.getElementById('resultPreview');
const btnWrong      = document.getElementById('btnWrong');
const notifArea     = document.getElementById('notifArea');
const countBadge    = document.getElementById('countBadge');
const emptyState    = document.getElementById('emptyState');
const histBody      = document.getElementById('histBody');
const searchBox     = document.getElementById('searchBox');
const exportBtn     = document.getElementById('exportBtn');

let notifCount = 0, lastText = '', lastLabel = '';
let historyData = [], currentFilter = 'all';

// MANUAL CHECK
checkBtn.onclick = async () => {
  const text = txt.value.trim();
  if (!text) { txt.focus(); return; }
  checkBtn.disabled = true;
  checkBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Analyzing...';
  try {
    const res = await fetch('/predict', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({text})
    });
    const j = await res.json();
    showResult(text, j.label, j.prob);
  } catch(e) { alert('Server error!'); }
  checkBtn.innerHTML = '<i class="bi bi-shield-check me-1"></i>Analyze for Spam';
  checkBtn.disabled = false;
};
txt.addEventListener('keydown', e => { if ((e.ctrlKey||e.metaKey) && e.key==='Enter') checkBtn.click(); });

function showResult(text, label, prob) {
  lastText = text; lastLabel = label;
  const isSpam = label === 'SPAM';
  const pct = Math.round((prob||0) * 100);
  resultBox.className = `result-box show ${isSpam ? 'is-spam' : 'is-safe'}`;
  resultIcon.textContent = isSpam ? '🚨' : '✅';
  resultLabelEl.textContent = isSpam ? 'SPAM DETECTED' : 'SAFE EMAIL';
  resultLabelEl.style.color = isSpam ? 'var(--spam)' : 'var(--safe)';
  resultPct.textContent = `${pct}% spam`;
  resultPct.className = `result-pct ${isSpam ? 'spam' : 'safe'}`;
  probFill.style.width = `${pct}%`;
  probFill.style.background = isSpam
    ? 'linear-gradient(90deg,#ff4757,#ff6b81)'
    : 'linear-gradient(90deg,#2ed573,#7bed9f)';
  resultPreview.textContent = `"${text.substring(0,120)}${text.length>120?'…':''}"`;
  btnWrong.disabled = false;
  btnWrong.innerHTML = '<i class="bi bi-flag me-1"></i>Wrong? Report it';
  btnWrong.style.color = '';
}

// FEEDBACK
btnWrong.onclick = async () => {
  if (!lastText) return;
  const trueLabel = lastLabel === 'SPAM' ? 'ham' : 'spam';
  btnWrong.disabled = true;
  btnWrong.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
  await fetch('/feedback', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({text: lastText, label: trueLabel})
  });
  btnWrong.innerHTML = '✓ Saved! Run retrain.py to improve';
  btnWrong.style.color = 'var(--safe)';
};

// LIVE STREAM
const evtSource = new EventSource('/stream');
evtSource.onmessage = e => {
  const obj = JSON.parse(e.data);
  addNotification(obj);
  addToHistory(obj);
  updateStats();
};

function addNotification(obj) {
  notifCount++;
  countBadge.textContent = notifCount;
  emptyState.style.display = 'none';
  const isSpam = obj.label === 'SPAM';
  const pct = Math.round((obj.prob||0) * 100);
  const div = document.createElement('div');
  div.className = `notif-item ${isSpam ? 'spam-notif' : 'safe-notif'}`;
  div.innerHTML = `
    <div class="notif-row1">
      <span class="notif-badge ${isSpam?'spam':'safe'}">${isSpam?'⚠ SPAM':'✓ SAFE'}</span>
      <span class="notif-subject">${esc(obj.subject||'(no subject)')}</span>
      <span class="notif-time">${obj.time}</span>
    </div>
    <div class="notif-from"><i class="bi bi-envelope me-1"></i>${esc(obj.from||'')}</div>
    <div class="notif-bar">
      <div class="notif-bar-fill" style="width:${pct}%;background:${isSpam?'var(--spam)':'var(--safe)'}"></div>
    </div>
    <button class="btn-wrong-sm" data-text="${escAttr(obj.text)}" data-pred="${obj.label}">
      <i class="bi bi-flag me-1"></i>Wrong Prediction
    </button>`;
  div.querySelector('.btn-wrong-sm').onclick = async function() {
    const trueLabel = this.dataset.pred==='SPAM'?'ham':'spam';
    this.disabled=true; this.innerHTML='<span class="spinner-border spinner-border-sm"></span>';
    await fetch('/feedback',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({text:this.dataset.text,label:trueLabel})});
    this.textContent='✓ Saved'; this.style.color='var(--safe)';
  };
  notifArea.insertBefore(div, notifArea.firstChild);
  if (Notification.permission==='granted') new Notification('SpamGuardian: '+obj.label,{body:obj.subject});
}

// HISTORY
function addToHistory(obj) { historyData.unshift(obj); renderHistory(); }
function renderHistory() {
  const q = searchBox.value.toLowerCase();
  const rows = historyData.filter(d => {
    const mf = currentFilter==='all'||
      (currentFilter==='spam'&&d.label==='SPAM')||
      (currentFilter==='safe'&&d.label==='SAFE');
    const ms = !q||(d.subject||'').toLowerCase().includes(q)||(d.from||'').toLowerCase().includes(q);
    return mf && ms;
  });
  if (!rows.length) {
    histBody.innerHTML='<tr><td colspan="5" style="text-align:center;padding:24px;color:var(--text2)">No results found</td></tr>';
    return;
  }
  histBody.innerHTML = rows.map(d => {
    const isSpam = d.label==='SPAM';
    const pct = Math.round((d.prob||0)*100);
    return `<tr>
      <td style="color:var(--text2);white-space:nowrap;font-family:'JetBrains Mono',monospace;font-size:0.78rem">${d.time}</td>
      <td style="color:var(--text2);max-width:150px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(d.from||'')}</td>
      <td style="max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(d.subject||'(no subject)')}</td>
      <td><span class="hist-badge ${isSpam?'spam':'safe'}">${d.label}</span></td>
      <td><span class="conf-val" style="color:${isSpam?'var(--spam)':'var(--safe)'}">${pct}%</span></td>
    </tr>`;
  }).join('');
}
searchBox.addEventListener('input', renderHistory);
document.querySelectorAll('.filter-btn').forEach(btn => {
  btn.onclick = () => {
    document.querySelectorAll('.filter-btn').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    currentFilter = btn.dataset.filter;
    renderHistory();
  };
});

// EXPORT
exportBtn.onclick = () => {
  if (!historyData.length) { alert('No history to export!'); return; }
  const csv = ['Time,From,Subject,Label,Confidence']
    .concat(historyData.map(d =>
      `"${d.time}","${(d.from||'').replace(/"/g,'""')}","${(d.subject||'').replace(/"/g,'""')}","${d.label}","${Math.round((d.prob||0)*100)}%"`
    )).join('\n');
  const a = document.createElement('a');
  a.href = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csv);
  a.download = `spamguardian_${new Date().toISOString().slice(0,10)}.csv`;
  a.click();
};

// STATS
async function updateStats() {
  try {
    const r = await fetch('/stats');
    const s = await r.json();
    document.getElementById('statTotal').textContent = s.total;
    document.getElementById('statSpam').textContent  = s.spam;
    document.getElementById('statSafe').textContent  = s.safe;
    const rate = s.total>0 ? Math.round(s.spam/s.total*100) : 0;
    document.getElementById('statRate').textContent  = rate+'%';
  } catch(e) {}
}
setInterval(updateStats, 8000);
updateStats();

// UTILS
function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function escAttr(s){ return String(s).replace(/"/g,'&quot;').replace(/'/g,'&#39;').replace(/\n/g,' '); }

if (Notification && Notification.permission==='default') Notification.requestPermission();

// SCROLL REVEAL
const observer = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) e.target.classList.add('visible');
  });
}, { threshold: 0.1 });

document.querySelectorAll('.stat-card, .panel, .history-panel')
  .forEach(el => observer.observe(el));