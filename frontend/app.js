const API = 'http://localhost:8000', DEPTH = 3, ALPHA_BETA = true;
const N = 15, CELL = 40, M = 20, H = 1, A = 2;
const $ = id => document.getElementById(id);
const cv = $('cv'), ctx = cv.getContext('2d');
let b, hist, over, busy, winLine, aiFirst = false;
 
function init() {
  b = new Array(N * N).fill(0); hist = []; over = false; busy = false; winLine = null;
  setStatus('Ваш хід (✕)'); draw();
  if (aiFirst) askAI();
}
const setStatus = t => $('status').textContent = t;
 
async function askAI() {
  busy = true; setStatus('ШІ думає…'); draw();
  try {
    const res = await fetch(API + '/api/move', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ board: b, depth: DEPTH, alpha_beta: ALPHA_BETA })
    });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    handle(await res.json());
  } catch (e) {
    setStatus('Помилка зв\'язку з бекендом: ' + e.message);
  }
  busy = false; draw();
}
 
function handle(d) {
  if (d.move) {
    const [r, c] = d.move; b[r * N + c] = A; hist.push(r * N + c);
  }
  if (d.winning_line) winLine = d.winning_line;
  const msg = { ongoing: 'Ваш хід (✕)', human_won: '🎉 Ви перемогли!', ai_won: 'Комп\'ютер переміг', draw: 'Нічия' };
  over = d.status !== 'ongoing';
  setStatus(msg[d.status]);
}
 
cv.addEventListener('click', e => {
  if (over || busy) return;
  const rc = cv.getBoundingClientRect();
  const c = Math.round(((e.clientX - rc.left) * cv.width / rc.width - M) / CELL);
  const r = Math.round(((e.clientY - rc.top) * cv.height / rc.height - M) / CELL);
  if (r < 0 || r >= N || c < 0 || c >= N || b[r * N + c]) return;
  b[r * N + c] = H; hist.push(r * N + c);
  askAI(); // бекенд перевірить перемогу людини і зробить хід ШІ
});
$('undo').onclick = () => {
  if (busy || !hist.length) return;
  over = false; winLine = null;
  let n = b[hist[hist.length - 1]] === A ? 2 : 1;
  while (n-- > 0 && hist.length) b[hist.pop()] = 0;
  setStatus('Ваш хід (✕)'); draw();
};
$('new').onclick = () => { if (!busy) init(); };
$('first').onclick = () => {
  if (busy) return;
  aiFirst = !aiFirst;
  $('first').textContent = 'Перший ходить: ' + (aiFirst ? 'Комп\'ютер' : 'Людина');
  init();
};
 
function draw() {
  const css = getComputedStyle(document.documentElement), g = k => css.getPropertyValue(k).trim();
  ctx.fillStyle = g('--board'); ctx.fillRect(0, 0, 600, 600);
  ctx.strokeStyle = g('--line'); ctx.lineWidth = 1; ctx.beginPath();
  for (let i = 0; i < N; i++) {
    ctx.moveTo(M + i * CELL, M); ctx.lineTo(M + i * CELL, M + 14 * CELL);
    ctx.moveTo(M, M + i * CELL); ctx.lineTo(M + 14 * CELL, M + i * CELL);
  }
  ctx.stroke(); ctx.fillStyle = g('--line');
  [3, 7, 11].forEach(a => [3, 7, 11].forEach(c => { ctx.beginPath(); ctx.arc(M + c * CELL, M + a * CELL, 3, 0, 7); ctx.fill(); }));
  ctx.lineCap = 'round'; ctx.lineWidth = 4;
  for (let i = 0; i < N * N; i++) {
    if (!b[i]) continue;
    const x = M + (i % N) * CELL, y = M + ((i / N) | 0) * CELL;
    ctx.beginPath();
    if (b[i] === H) {
      ctx.strokeStyle = g('--x');
      ctx.moveTo(x - 11, y - 11); ctx.lineTo(x + 11, y + 11); ctx.moveTo(x + 11, y - 11); ctx.lineTo(x - 11, y + 11);
    } else { ctx.strokeStyle = g('--o'); ctx.arc(x, y, 12, 0, 7); }
    ctx.stroke();
  }
  if (hist.length) {
    const i = hist[hist.length - 1];
    ctx.strokeStyle = g('--ac'); ctx.lineWidth = 2;
    ctx.strokeRect(M + (i % N) * CELL - 18, M + ((i / N) | 0) * CELL - 18, 36, 36);
  }
  if (winLine) {
    const s = [...winLine].sort((p, q) => p[0] - q[0] || p[1] - q[1]), f = s[0], l = s[s.length - 1];
    ctx.strokeStyle = g('--ac'); ctx.lineWidth = 6; ctx.beginPath();
    ctx.moveTo(M + f[1] * CELL, M + f[0] * CELL); ctx.lineTo(M + l[1] * CELL, M + l[0] * CELL); ctx.stroke();
  }
}
init();