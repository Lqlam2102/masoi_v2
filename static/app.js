'use strict';

// ══════════════════════════════════════════
//  ROLE METADATA — icon, name, faction, description, rules, tip
// ══════════════════════════════════════════
const ROLE_META = {
  villager: {
    name: 'Dân Thường', icon: '👨‍🌾', faction: 'village',
    short: 'Không có kỹ năng đặc biệt',
    desc: 'Bạn là một người dân bình thường của làng. Nhiệm vụ duy nhất là lắng nghe, quan sát và dùng lá phiếu để loại trừ Sói.',
    rules: [
      { icon: '🗳️', text: '<strong>Bỏ phiếu ban ngày</strong> để treo cổ người bị nghi là Sói.' },
      { icon: '🌙', text: '<strong>Không có hành động ban đêm.</strong>' },
    ],
    tip: '💡 Ghi nhớ ai bảo vệ ai, ai im lặng bất thường — đó là manh mối quý giá.',
  },
  seer: {
    name: 'Tiên Tri', icon: '🔮', faction: 'village',
    short: 'Soi một người mỗi đêm, biết phe của họ',
    desc: 'Bạn có khả năng thần bí — mỗi đêm có thể nhìn thấu tâm can một người và biết họ thuộc phe Dân hay phe Sói.',
    rules: [
      { icon: '🌙', text: '<strong>Mỗi đêm</strong> chọn 1 người để soi.' },
      { icon: '📜', text: 'Kết quả chỉ cho biết <strong>phe</strong> (Dân hoặc Sói), không biết vai cụ thể.' },
      { icon: '🤫', text: 'Kết quả chỉ mình bạn biết — bạn quyết định khi nào tiết lộ.' },
    ],
    tip: '💡 Đừng lộ bài quá sớm — Sói sẽ ưu tiên giết bạn ngay khi biết bạn là Tiên Tri.',
  },
  guard: {
    name: 'Bảo Vệ', icon: '🛡️', faction: 'village',
    short: 'Bảo vệ 1 người khỏi bị Sói cắn mỗi đêm',
    desc: 'Bạn là chiến binh thầm lặng của làng. Mỗi đêm đứng canh trước cửa nhà một người để chặn đòn tấn công của Sói.',
    rules: [
      { icon: '🌙', text: '<strong>Mỗi đêm</strong> chọn 1 người để bảo vệ.' },
      { icon: '🔁', text: '<strong>Không được</strong> bảo vệ cùng một người hai đêm liên tiếp.' },
      { icon: '🏠', text: 'Được phép <strong>tự bảo vệ bản thân.</strong>' },
      { icon: '✅', text: 'Chỉ chặn được đòn của <strong>phe Sói</strong> (wolf, white_wolf). Độc Phù Thủy không chặn được.' },
    ],
    tip: '💡 Thường xuyên bảo vệ Tiên Tri hoặc người bị Sói nghi ngờ nhất. Hãy thay đổi mục tiêu để tránh bị đoán.',
  },
  witch: {
    name: 'Phù Thủy', icon: '🧙‍♀️', faction: 'village',
    short: '1 bình cứu + 1 bình độc, dùng cả ván',
    desc: 'Bạn là pháp sư quyền năng nhất làng, nắm giữ hai loại thuốc đặc biệt — một cứu sống, một giết chết.',
    rules: [
      { icon: '🧪', text: '<strong>Bình cứu:</strong> cứu người bị Sói cắn đêm đó. Dùng được <strong>1 lần cả ván.</strong>' },
      { icon: '☠️', text: '<strong>Bình độc:</strong> giết bất kỳ người sống nào. Dùng được <strong>1 lần cả ván.</strong>' },
      { icon: '👁️', text: 'Trước khi quyết định, bạn <strong>được biết ai bị Sói cắn</strong> đêm đó (kể cả khi Bảo Vệ đã đỡ).' },
      { icon: '🚫', text: 'Độc <strong>không bị chặn</strong> bởi Bảo Vệ, bình cứu, hay giáp Già Làng.' },
    ],
    tip: '💡 Hãy giữ bình độc đến cuối ván để dùng lúc quyết định. Bình cứu cứu người quan trọng như Tiên Tri.',
  },
  hunter: {
    name: 'Thợ Săn', icon: '🏹', faction: 'village',
    short: 'Khi chết vì bất kỳ lý do, được bắn 1 người',
    desc: 'Bạn là thợ săn kiêu hùng — ngay cả khi ngã xuống vẫn kịp bắn một phát cuối cùng.',
    rules: [
      { icon: '💀', text: '<strong>Khi chết</strong> (dù bị cắn, bị độc, bị treo cổ hay chết theo người yêu) được chọn 1 người để bắn.' },
      { icon: '🔫', text: 'Phát bắn <strong>không thể bị chặn</strong> bởi bất kỳ kỹ năng nào.' },
      { icon: '🌙', text: '<strong>Không có hành động ban đêm.</strong>' },
    ],
    tip: '💡 Đừng vội lộ vai — hãy để Sói đoán sai. Khi chết, bắn người bạn chắc chắn nhất là Sói.',
  },
  cupid: {
    name: 'Cupid', icon: '💘', faction: 'village',
    short: 'Đêm đầu ghép 2 người thành cặp đôi',
    desc: 'Bạn là thần Tình Yêu — đêm đầu tiên bắn mũi tên vàng ghép hai người thành cặp đôi bất tử.',
    rules: [
      { icon: '🌙', text: '<strong>Đêm 1 duy nhất:</strong> chọn 2 người (có thể bao gồm chính mình) để ghép đôi.' },
      { icon: '💑', text: 'Một người trong cặp chết → <strong>người kia chết theo ngay lập tức.</strong>' },
      { icon: '🏆', text: 'Nếu 2 người cuối cùng còn sống là cặp đôi <strong>khác phe</strong> → <strong>cặp đôi thắng riêng.</strong>' },
    ],
    tip: '💡 Ghép người yêu bạn với mình để có "bảo hiểm". Ghép hai kẻ thù để tạo bất ổn cho cả hai phe.',
  },
  elder: {
    name: 'Già Làng', icon: '🧓', faction: 'village',
    short: 'Sống sót đòn Sói đầu tiên nhờ giáp',
    desc: 'Bạn là người trưởng lão đức độ — kinh nghiệm sống đã tạo nên một lớp giáp vô hình chống lại nanh vuốt của Sói.',
    rules: [
      { icon: '🛡️', text: '<strong>Đòn Sói (wolf, white_wolf) đầu tiên</strong> không giết bạn — chỉ phá giáp.' },
      { icon: '💀', text: 'Đòn Sói <strong>thứ hai, bình độc, bị treo cổ hoặc đạn Thợ Săn</strong> → chết ngay.' },
      { icon: '🌙', text: '<strong>Không có hành động ban đêm.</strong>' },
    ],
    tip: '💡 Bạn là mục tiêu ưu tiên của Sói từ đêm thứ hai. Hãy lộ bài sớm để dân làng bảo vệ bạn.',
  },
  fool: {
    name: 'Thằng Ngố', icon: '🃏', faction: 'village',
    short: 'Bị treo cổ → thắng ngay, ván kết thúc',
    desc: 'Bạn là kẻ lập dị của làng. Mục tiêu bí ẩn của bạn là... bị dân làng treo cổ. Trông ngốc, nhưng thực ra là thiên tài.',
    rules: [
      { icon: '🏆', text: 'Nếu <strong>bị dân làng treo cổ</strong> (ban ngày) → bạn <strong>thắng một mình</strong>, ván kết thúc ngay.' },
      { icon: '💀', text: 'Bị Sói cắn, bị độc, hay chết theo người yêu → <strong>không được thắng.</strong>' },
      { icon: '🌙', text: '<strong>Không có hành động ban đêm.</strong>' },
    ],
    tip: '💡 Hãy đóng giả Sói thật khéo để dân làng vote cho bạn. Nhưng đừng lộ bài trước khi bị treo!',
  },
  wolf: {
    name: 'Sói', icon: '🐺', faction: 'wolf',
    short: 'Cùng bầy chọn 1 người để cắn mỗi đêm',
    desc: 'Bạn là Sói hung tàn ẩn náu giữa dân làng. Ban ngày giả vờ ngây thơ, ban đêm cùng đồng bọn săn mồi.',
    rules: [
      { icon: '🌙', text: '<strong>Mỗi đêm</strong> bầy sói bỏ phiếu chọn 1 người dân để cắn chết.' },
      { icon: '👁️', text: 'Biết danh tính <strong>toàn bộ đồng đội sói.</strong>' },
      { icon: '🏆', text: 'Phe Sói thắng khi <strong>số Sói ≥ số người còn lại.</strong>' },
    ],
    tip: '💡 Đừng quá im lặng, hãy tham gia tranh luận để tránh bị nghi. Ưu tiên tiêu diệt Tiên Tri trước.',
  },
  wolf_seer: {
    name: 'Sói Tiên Tri', icon: '👁️', faction: 'wolf',
    short: 'Sói + soi biết chính xác vai người khác',
    desc: 'Bạn là Sói có năng lực thần bí — vừa cắn người cùng bầy, vừa có thể nhìn thấu vai chính xác của bất kỳ ai.',
    rules: [
      { icon: '🐺', text: '<strong>Vẫn bỏ phiếu cắn</strong> cùng bầy mỗi đêm.' },
      { icon: '🔍', text: 'Thêm: mỗi đêm soi 1 người, biết <strong>vai chính xác</strong> (không chỉ phe).' },
      { icon: '🤐', text: 'Kết quả soi chỉ mình bạn biết — dùng để định hướng bầy sói.' },
    ],
    tip: '💡 Dùng khả năng soi để xác nhận Tiên Tri, Bảo Vệ, Phù Thủy và loại trừ họ đúng thứ tự.',
  },
  white_wolf: {
    name: 'Sói Trắng', icon: '🤍', faction: 'wolf',
    short: 'Đêm chẵn giết thêm 1 Sói, thắng một mình',
    desc: 'Bạn là Sói phản bội — kẻ nằm vùng ngay trong đội ngũ Sói. Mục tiêu cuối cùng là trở thành người sống sót duy nhất.',
    rules: [
      { icon: '🐺', text: '<strong>Vẫn bỏ phiếu cắn</strong> cùng bầy mỗi đêm.' },
      { icon: '🌙', text: '<strong>Các đêm chẵn</strong> (đêm 2, 4, 6…) được <strong>giết thêm 1 Sói khác</strong>.' },
      { icon: '🏆', text: 'Nếu là <strong>người sống sót duy nhất</strong> → thắng một mình (cả Sói lẫn Dân đều thua).' },
    ],
    tip: '💡 Thời điểm tốt nhất để ra tay là đêm chẵn cuối khi chỉ còn 1 Sói thật — đó là lúc bạn kết thúc trò chơi.',
  },
};

// DEFAULT_SETUPS mirrors backend setup.py (5-18 players)
const DEFAULT_SETUPS = {
  5:  ['wolf','seer','guard','witch','villager'],
  6:  ['wolf','wolf','seer','guard','witch','villager'],
  7:  ['wolf','wolf','seer','guard','witch','hunter','villager'],
  8:  ['wolf','wolf','seer','guard','witch','hunter','villager','villager'],
  9:  ['wolf','wolf','wolf_seer','seer','guard','witch','hunter','villager','villager'],
  10: ['wolf','wolf','wolf_seer','seer','guard','witch','hunter','villager','villager','cupid'],
  11: ['wolf','wolf','wolf_seer','seer','guard','witch','hunter','villager','villager','cupid','elder'],
  12: ['wolf','wolf','wolf_seer','seer','guard','witch','hunter','villager','villager','cupid','elder','white_wolf'],
  13: ['wolf','wolf','wolf_seer','seer','guard','witch','hunter','villager','villager','cupid','elder','white_wolf','fool'],
  14: ['wolf','wolf','wolf_seer','seer','guard','witch','hunter','villager','villager','cupid','elder','white_wolf','fool','villager'],
  15: ['wolf','wolf','wolf','wolf_seer','seer','guard','witch','hunter','villager','villager','cupid','elder','white_wolf','fool','villager'],
  16: ['wolf','wolf','wolf','wolf_seer','seer','guard','witch','hunter','villager','villager','villager','cupid','elder','white_wolf','fool','villager'],
  17: ['wolf','wolf','wolf','wolf_seer','seer','guard','witch','hunter','villager','villager','villager','villager','cupid','elder','white_wolf','fool','villager'],
  18: ['wolf','wolf','wolf','wolf','wolf_seer','seer','guard','witch','hunter','villager','villager','villager','villager','cupid','elder','white_wolf','fool','villager'],
};

// All configurable roles (can have count > 0), in display order
const ALL_ROLE_IDS = [
  'wolf','wolf_seer','white_wolf',
  'seer','guard','witch','hunter','cupid','elder','fool','villager',
];

const PHASE_LABEL = {
  lobby:'🏠 Sảnh chờ', night_cupid:'🌙 Cupid hành động',
  night_seer:'🌙 Tiên Tri hành động', night_wolf_seer:'🌙 Sói Tiên Tri hành động',
  night_guard:'🌙 Bảo Vệ hành động', night_wolf:'🌙 Bầy Sói hành động',
  night_white_wolf:'🌙 Sói Trắng hành động', night_witch:'🌙 Phù Thủy hành động',
  night_result:'🌅 Bình minh', day_discuss:'☀️ Tranh luận',
  day_vote:'🗳️ Bỏ phiếu', day_result:'📋 Kết quả ngày',
  hunter_shot:'🏹 Thợ Săn bắn', game_over:'🏁 Kết thúc',
};

const SOURCE_LABEL = {
  wolf:'Sói cắn', white_wolf:'Sói Trắng giết', witch:'Phù Thủy đầu độc',
  hunter:'Thợ Săn bắn', lover:'Chết theo người yêu', lynch:'Dân làng treo cổ',
};

// Màn thông báo khi sang pha mới — [icon, tiêu đề, phụ đề].
const PHASE_OVERLAY = {
  night_cupid:      ['💘',   'Cupid thức giấc',      'Chọn cặp đôi định mệnh'],
  night_seer:       ['🔮',   'Tiên Tri thức giấc',   'Soi phe của một người'],
  night_wolf_seer:  ['🐺',   'Sói Tiên Tri thức giấc','Soi vai của một người'],
  night_guard:      ['🛡️',   'Bảo Vệ thức giấc',     'Chọn người để che chở'],
  night_wolf:       ['🐺',   'Bầy Sói thức giấc',    'Bầy Sói chọn con mồi đêm nay'],
  night_white_wolf: ['🤍',   'Sói Trắng thức giấc',  'Có thể cắn một con Sói khác'],
  night_witch:      ['🧙‍♀️', 'Phù Thủy thức giấc',   'Bình cứu hay bình độc?'],
  night_result:     ['🌅',   'Trời đang sáng…',      'Làng sắp biết chuyện đêm qua'],
  day_discuss:      ['☀️',   'Trời sáng rồi!',       'Cả làng thức dậy và tranh luận'],
  day_vote:         ['🗳️',   'Phiên toà bắt đầu',    'Bỏ phiếu treo cổ kẻ bị nghi ngờ'],
  day_result:       ['⚖️',   'Phán quyết',           'Dân làng đã quyết định'],
  hunter_shot:      ['🏹',   'Thợ Săn nổ súng',      'Viên đạn cuối trước khi ngã xuống'],
};

function isNightPhase(p) { return !!p && p.startsWith('night_') && p !== 'night_result'; }

function phaseSound(prev, next) {
  if (isNightPhase(next) && !isNightPhase(prev)) return 'nightfall';
  if (next === 'night_wolf' || next === 'night_white_wolf') return 'howl';
  if (next === 'night_result') return 'dawn';
  if (next === 'day_vote') return 'gavel';
  if (next === 'hunter_shot') return 'shot';
  return null;
}

// ── State ──
let ws = null, myId = null, myToken = null, myRoom = null, isHost = false;
let gameState = null, selectedTargets = [], currentPrompt = null, witchAction = null;
let countdownTimer = null, deadlineEnd = null, countdownTotal = 0, lastTickAt = null;
let prevPhase = null, promptKey = null;
// Phải khớp DEFAULT_TIMERS ở app/room.py.
let timers = { night_phase: 60, day_discuss: 180, day_vote: 75, hunter_shot: 45 };

// roleCounts: {role_id: number}  — host's current config
let roleCounts = {};
// current player count in room
let playerCount = 0;

const $ = id => document.getElementById(id);

// ══════════════════════════════════════════
//  SCREEN
// ══════════════════════════════════════════
function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  $(id).classList.add('active');
}

// ══════════════════════════════════════════
//  TOAST
// ══════════════════════════════════════════
let _toastTimer = null;
function showToast(msg, type = '') {
  const el = $('toast');
  el.textContent = msg;
  el.className = 'toast show' + (type ? ' toast-' + type : '');
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => el.classList.remove('show'), 3200);
}

// ══════════════════════════════════════════
//  WEBSOCKET
// ══════════════════════════════════════════
// Đã join thành công trong LẦN kết nối này chưa — dùng để phân biệt
// "rớt mạng giữa ván" (nên thử lại) với "token hỏng" (phải về màn hình chính).
let sessionJoined = false;

function connectWS(payload) {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  sessionJoined = false;
  ws = new WebSocket(`${proto}://${location.host}/ws`);
  ws.onopen = () => ws.send(JSON.stringify(payload));
  ws.onmessage = e => { try { handleServerMsg(JSON.parse(e.data)); } catch {} };
  ws.onclose = () => {
    if (!myToken) return;                       // tự rời phòng, không nối lại
    showToast('Mất kết nối. Đang thử lại…', 'error');
    setTimeout(() => { if (myToken) connectWS({ type: 'join', token: myToken }); }, 2500);
  };
  ws.onerror = () => showToast('Lỗi kết nối.', 'error');
}

/** Xoá sạch phiên hiện tại và quay về màn hình chính. */
function resetToHome(message) {
  if (ws) { try { ws.onclose = null; ws.close(); } catch {} ws = null; }
  myToken = null; myId = null; gameState = null; roleCounts = {};
  window._gameLog = []; prevPhase = null; promptKey = null; sessionJoined = false;
  localStorage.removeItem('masoi_token');
  SFX.setAmbience(null);
  clearCountdown(); dismissPrivateMessage(); clearChat();
  $('night-result-panel').style.display = 'none';
  $('action-panel').style.display = 'none';
  showScreen('screen-home');
  startRoomPolling();
  if (message) showToast(message, 'error');
}
function send(obj) { if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(obj)); }

// ══════════════════════════════════════════
//  SERVER MESSAGE HANDLER
// ══════════════════════════════════════════
function handleServerMsg(msg) {
  switch (msg.type) {
    case 'joined':       handleJoined(msg); break;
    case 'lobby':        handleLobby(msg); break;
    case 'state':        handleState(msg); break;
    case 'private':      handlePrivate(msg); break;
    case 'waiting':      handleWaiting(msg); break;
    case 'notice':       showToast('👑 ' + msg.text); break;
    case 'chat':         addChatMessage(msg); break;
    case 'chat_history': (msg.messages || []).forEach(m => addChatMessage(m, true)); break;
    case 'dawn':         handleDawn(msg); break;
    case 'night_result': handleNightResult(msg); break;
    case 'day_result':   handleDayResult(msg); break;
    case 'game_over':    handleGameOver(msg); break;
    case 'left':         /* handled by doLeave() flow, ignore */ break;
    // Lỗi trước khi join xong = token/phòng không còn hợp lệ. Thử lại vô ích,
    // phải xoá token, nếu không client kẹt vòng lặp nối lại mãi mãi.
    case 'error':
      SFX.play('error');
      if (sessionJoined) showToast(msg.message, 'error');
      else resetToHome(msg.message);
      break;
    case 'config_ok':    showToast('Đã lưu cài đặt ✓', 'success'); break;
  }
}

function handleJoined(msg) {
  sessionJoined = true;
  myId = msg.you.id; myToken = msg.token; myRoom = msg.room; isHost = msg.is_host;
  localStorage.setItem('masoi_token', myToken);
  $('lobby-code').textContent = myRoom;
  stopRoomPolling();
  // Vào giữa ván: để message `waiting` quyết định màn hình, đừng nhảy vào lobby.
  if (!msg.waiting) showScreen('screen-lobby');
}

// ══════════════════════════════════════════
//  SẢNH — DANH SÁCH PHÒNG ĐANG MỞ
// ══════════════════════════════════════════
let roomPollTimer = null;

async function refreshRooms() {
  let rooms = [];
  try {
    const res = await fetch('/api/rooms', { cache: 'no-store' });
    rooms = (await res.json()).rooms || [];
  } catch { return; }              // mất mạng thì giữ nguyên danh sách cũ

  $('room-count').textContent = rooms.length;
  const list = $('room-list');
  list.innerHTML = '';
  if (!rooms.length) {
    list.innerHTML = '<p class="room-empty">Chưa có phòng nào — hãy tạo phòng mới.</p>';
    return;
  }
  rooms.forEach(r => {
    const playing = r.status === 'playing';
    const full = r.players >= r.max;
    const row = document.createElement('div');
    row.className = 'room-row' + (playing ? ' room-playing' : '');
    row.innerHTML = `
      <div class="room-main">
        <div class="room-code">${esc(r.code)}</div>
        <div class="room-meta">
          ${r.host ? `👑 ${esc(r.host)} · ` : ''}${r.players}/${r.max} người
          ${r.waiting ? ` · ⏳ ${r.waiting} chờ` : ''}
        </div>
      </div>
      <div class="room-side">
        <span class="room-status ${playing ? 'rs-playing' : 'rs-open'}">
          ${playing ? `🌙 Đêm ${r.night}` : `🕐 Đang chờ`}
        </span>
        <button class="btn btn-sm ${playing ? 'btn-outline' : 'btn-primary'}" ${full ? 'disabled' : ''}>
          ${full ? 'Đầy' : (playing ? 'Chờ ván sau' : 'Vào')}
        </button>
      </div>`;
    if (!full) row.querySelector('button').addEventListener('click', () => joinRoom(r.code, playing));
    list.appendChild(row);
  });
}

function joinRoom(code, playing) {
  const name = $('input-name').value.trim();
  if (!name) { showToast('Nhập tên của bạn trước', 'error'); return; }
  SFX.unlock();
  if (playing) showToast('Ván đang chạy — bạn sẽ chờ tới ván sau', '');
  connectWS({ type: 'join', room: code, name });
}

function startRoomPolling() {
  stopRoomPolling();
  refreshRooms();
  roomPollTimer = setInterval(refreshRooms, 4000);
}
function stopRoomPolling() {
  clearInterval(roomPollTimer); roomPollTimer = null;
}

$('btn-refresh-rooms').addEventListener('click', () => { refreshRooms(); SFX.play('select'); });

// ══════════════════════════════════════════
//  MÀN HÌNH CHỜ VÁN SAU
// ══════════════════════════════════════════
function handleWaiting(msg) {
  stopRoomPolling();
  clearCountdown();
  SFX.setAmbience(null);
  $('wait-room').textContent = msg.room || myRoom || '----';
  $('wait-host').textContent = msg.host || '—';
  $('wait-playing').textContent = `${msg.playing} người`;
  $('wait-night').textContent = msg.night ? `Đêm ${msg.night}` : '—';
  const others = (msg.waiters || []);
  $('wait-count').textContent = others.length;
  const box = $('wait-others');
  box.innerHTML = others.length
    ? others.map(n => `<span class="wait-chip">${esc(n)}</span>`).join('')
    : '<span class="room-empty">Chỉ mình bạn</span>';
  showScreen('screen-wait');
}

function handleLobby(msg) {
  $('lobby-code').textContent = msg.room || myRoom;
  const players = msg.players || [];
  playerCount = players.length;
  $('lobby-count').textContent = playerCount;

  // Player list
  const list = $('lobby-players');
  list.innerHTML = '';
  players.forEach(p => {
    const li = document.createElement('li');
    li.className = 'player-item';
    const isMe = p.id === myId, isH = p.id === msg.host;
    li.innerHTML = `
      <div class="player-avatar">${initials(p.name)}</div>
      <div class="player-info">
        <div class="player-name">${esc(p.name)}${isMe ? ' <span style="font-size:11px;color:var(--accent)">(bạn)</span>' : ''}</div>
        <div class="player-role-tag">${isH ? '👑 Host' : ''}</div>
      </div>
      <span class="player-status ${p.online ? 'status-online' : 'status-offline'}">${p.online ? 'Online' : 'Offline'}</span>`;
    list.appendChild(li);
  });

  // Quyền host có thể đã chuyển sang mình sau khi host cũ rời phòng.
  if (msg.host) isHost = msg.host === myId;
  const hc = $('host-controls'), lw = $('lobby-waiting'), gc = $('role-guide-card');
  if (isHost) {
    hc.style.display = '';
    lw.style.display = 'none';
    gc.style.display = 'none';
    renderRoleConfig();
  } else {
    hc.style.display = 'none';
    lw.style.display = '';
    gc.style.display = '';
  }
  showScreen('screen-lobby');
}

function handleState(msg) {
  gameState = msg;
  showScreen('screen-game');
  renderGameScreen(msg);
}

function handlePrivate(msg) { showPrivateMessage(msg.text, msg.kind); }

function handleDawn(msg) {
  showPhaseOverlay('night_result', `Đêm ${msg.night} đã qua`, (msg.duration || 6) * 1000 - 800);
}

function handleNightResult(msg) {
  renderResultPanel(`🌅 Đêm ${msg.night} — Kết quả`, msg,
                    '✨ Đêm bình yên — không ai chết');
}

function handleDayResult(msg) {
  renderResultPanel('⚖️ Phán quyết của dân làng', msg,
                    '🤝 Dân làng không thống nhất — không ai bị treo cổ');
}

function renderResultPanel(title, msg, emptyText) {
  $('result-panel-title').textContent = title;
  const deaths = msg.deaths || [];
  const deathsEl = $('result-deaths');
  deathsEl.innerHTML = '';
  if (deaths.length > 0) {
    SFX.play('death');
    deaths.forEach(d => {
      const role = ROLE_META[d.role] || { name: d.role, icon: '❓' };
      const div = document.createElement('div');
      div.className = 'death-item';
      div.innerHTML = `<span class="death-icon">💀</span><div>
        <div class="death-name">${esc(d.name)}</div>
        <div class="death-role">${role.icon} ${role.name}</div>
        <div class="death-reason">${SOURCE_LABEL[d.source] || d.source}</div>
      </div>`;
      deathsEl.appendChild(div);
      logPush(`${d.name} chết — ${SOURCE_LABEL[d.source] || d.source}`);
    });
  } else {
    SFX.play('peace');
    deathsEl.innerHTML = `<p class="result-peace">${emptyText}</p>`;
    logPush(emptyText.replace(/^\S+\s/, ''));
  }
  const logEl = $('result-log');
  logEl.innerHTML = '';
  (msg.public_log || []).forEach(line => {
    const p = document.createElement('p'); p.textContent = line; logEl.appendChild(p);
  });
  $('action-panel').style.display = 'none';
  const panel = $('night-result-panel');
  panel.style.display = '';
  panel.classList.remove('result-flash');
  void panel.offsetWidth;             // ép trình duyệt chạy lại animation
  panel.classList.add('result-flash');
  panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function handleGameOver(msg) {
  clearCountdown();
  prevPhase = 'game_over';
  SFX.setAmbience(null);
  SFX.play(msg.winner === 'village' || msg.winner === 'lovers' ? 'winVillage' : 'winWolf');
  // Host mở được ván mới ngay trong phòng; người khác chờ host.
  $('btn-rematch').style.display = isHost ? '' : 'none';
  $('btn-rematch').disabled = false;
  $('over-wait-host').style.display = isHost ? 'none' : '';
  const note = $('over-waiting-note');
  note.style.display = msg.waiting ? '' : 'none';
  note.textContent = msg.waiting
    ? `⏳ ${msg.waiting} người đang chờ vào chơi ván sau`
    : '';
  const icon = { wolf:'🐺', village:'🌻', white_wolf:'🤍', lovers:'💑', fool:'🃏' }[msg.winner] || '🏁';
  $('winner-icon').textContent = icon;
  $('winner-label').textContent = msg.winner_label || 'Kết thúc';
  const list = $('over-roles');
  list.innerHTML = '';
  Object.entries(msg.roles || {}).forEach(([pid, role_id]) => {
    const meta = ROLE_META[role_id] || { name: role_id, icon: '❓' };
    const player = gameState?.players?.find(p => p.id === pid);
    const li = document.createElement('li');
    li.className = 'player-item';
    li.innerHTML = `<div class="player-avatar">${initials(player?.name || pid)}</div>
      <div class="player-info">
        <div class="player-name">${esc(player?.name || pid)}</div>
        <div class="player-role-tag">${meta.icon} ${meta.name}</div>
      </div>`;
    list.appendChild(li);
  });
  const logEl = $('over-log');
  logEl.innerHTML = '';
  (msg.full_log || []).forEach(line => {
    const div = document.createElement('div'); div.className = 'log-entry'; div.textContent = line; logEl.appendChild(div);
  });
  showScreen('screen-over');
}

// ══════════════════════════════════════════
//  GAME SCREEN RENDER
// ══════════════════════════════════════════
function renderGameScreen(msg) {
  // Host có thể đổi giữa chừng (người cũ rớt mạng) — bám theo state của server.
  if (msg.is_host !== undefined) isHost = msg.is_host;
  const phase = msg.phase || 'lobby';
  if (phase !== prevPhase) {
    onPhaseChange(prevPhase, phase, msg);
    prevPhase = phase;
  }
  $('game-phase-label').textContent = PHASE_LABEL[phase] || phase;
  $('game-night-label').textContent = msg.night > 0 ? `Đêm ${msg.night}` : '';
  document.body.className = phase.startsWith('night_') ? 'phase-night' : 'phase-day';
  const you = msg.you || {};
  const myRole = ROLE_META[you.role] || { name: '???', icon: '❓', faction: 'village' };
  $('my-role-icon').textContent = myRole.icon;
  $('my-role-name').textContent = myRole.name;
  const fb = $('my-faction-badge');
  fb.textContent = you.role ? (myRole.faction === 'wolf' ? 'Phe Sói' : 'Phe Dân') : '';
  fb.className = 'faction-badge faction-' + (myRole.faction === 'wolf' ? 'wolf' : 'village');
  $('my-alive-status').textContent = you.alive === false ? '💀' : '💚';
  renderPlayersGrid(msg);
  if (msg.deadline) startCountdown(msg.deadline, msg.duration); else clearCountdown();
  renderActionPanel(msg);
  renderVoteBoard(msg);
  renderChatPanel(msg);
  renderHostBar(msg);
  renderLog();
}

// ══════════════════════════════════════════
//  QUYỀN HOST — chốt pha sớm
// ══════════════════════════════════════════
const ADVANCE_LABEL = {
  day_discuss:  '⏭ Kết thúc thảo luận',
  day_vote:     '⏭ Chốt phiếu ngay',
  day_result:   '⏭ Sang đêm',
  night_result: '⏭ Công bố ngay',
  hunter_shot:  '⏭ Bỏ qua lượt bắn',
};

function renderHostBar(msg) {
  const bar = $('host-bar'), phase = msg.phase || '';
  // Chỉ pha đang có đồng hồ chạy mới chốt sớm được — khớp với server.
  const canAdvance = msg.is_host && msg.deadline && phase !== 'game_over';
  bar.style.display = canAdvance ? '' : 'none';
  if (!canAdvance) return;
  $('btn-force-advance').textContent =
    ADVANCE_LABEL[phase] || (phase.startsWith('night_') ? '⏭ Bỏ qua pha này' : '⏭ Kết thúc sớm');
}

$('btn-force-advance').addEventListener('click', () => {
  send({ type: 'advance' });
  SFX.play('confirm');
  $('btn-force-advance').disabled = true;
  setTimeout(() => { $('btn-force-advance').disabled = false; }, 1200);
});

// ══════════════════════════════════════════
//  BẢNG PHIẾU TRỰC TIẾP
//  Bầy Sói không nói chuyện ngoài đời được nên phải thấy nhau chọn ai.
// ══════════════════════════════════════════
function votersByTarget(votes) {
  const map = {};
  if (votes) {
    Object.entries(votes.by_voter || {}).forEach(([voter, target]) => {
      (map[target] = map[target] || []).push(voter);
    });
  }
  return map;
}

function nameOf(pid) {
  return gameState?.players?.find(p => p.id === pid)?.name || pid;
}

function renderVoteBoard(msg) {
  const board = $('vote-board'), votes = msg.votes;
  if (!votes) { board.style.display = 'none'; return; }
  board.style.display = '';
  board.classList.toggle('vote-board-wolf', votes.scope === 'wolf');

  $('vote-board-title').textContent = votes.scope === 'wolf'
    ? '🐺 Bầy Sói đang nhắm' : '🗳️ Phiếu treo cổ';

  const byTarget = votersByTarget(votes);
  const entries = Object.entries(votes.counts || {}).sort((a, b) => b[1] - a[1]);
  const top = entries[0];

  const status = $('vote-board-status');
  if (!entries.length) {
    status.textContent = 'Chưa ai chọn';
    status.className = 'vote-board-status status-idle';
  } else if (votes.decided) {
    status.textContent = `✅ Đang dẫn: ${nameOf(top[0])}`;
    status.className = 'vote-board-status status-ok';
  } else {
    status.textContent = '⚠️ Hoà phiếu — chưa thống nhất';
    status.className = 'vote-board-status status-warn';
  }

  const rows = $('vote-board-rows');
  rows.innerHTML = '';
  entries.forEach(([target, count]) => {
    const leading = votes.decided && target === top[0];
    const row = document.createElement('div');
    row.className = 'vote-row' + (leading ? ' vote-row-lead' : '');
    row.innerHTML = `
      <span class="vote-target">${esc(nameOf(target))}</span>
      <span class="vote-voters">${esc((byTarget[target] || []).map(nameOf).join(', '))}</span>
      <span class="vote-count">${count}</span>`;
    rows.appendChild(row);
  });

  const pending = votes.pending || [];
  $('vote-board-pending').textContent = pending.length
    ? `Chưa chọn: ${pending.map(nameOf).join(', ')}`
    : '';
}

// ══════════════════════════════════════════
//  CHUYỂN PHA — overlay + âm thanh
// ══════════════════════════════════════════
function onPhaseChange(prev, next, msg) {
  // Pha bình minh đã có overlay riêng do server báo trước (message `dawn`).
  if (next !== 'night_result') {
    showPhaseOverlay(next, next.startsWith('night_') || next.startsWith('day_')
      ? (msg.night > 0 ? `Đêm ${msg.night}` : '') : '');
  }
  const sound = phaseSound(prev, next);
  if (sound) SFX.play(sound);

  if (next === 'game_over') SFX.setAmbience(null);
  else if (next.startsWith('night_')) SFX.setAmbience('night');
  else SFX.setAmbience('day');

  // Sang pha mới thì lời phán cũ không còn liên quan.
  if (next === 'day_discuss') dismissPrivateMessage();
}

let _overlayTimer = null;
function showPhaseOverlay(phase, sub, holdMs) {
  const meta = PHASE_OVERLAY[phase];
  if (!meta) return;
  const [icon, title, defaultSub] = meta;
  $('phase-overlay-icon').textContent = icon;
  $('phase-overlay-title').textContent = title;
  $('phase-overlay-sub').textContent = sub ? `${sub} — ${defaultSub}` : defaultSub;
  const el = $('phase-overlay');
  el.classList.remove('show'); void el.offsetWidth;
  el.classList.add('show');
  el.setAttribute('aria-hidden', 'false');
  clearTimeout(_overlayTimer);
  _overlayTimer = setTimeout(() => {
    el.classList.remove('show');
    el.setAttribute('aria-hidden', 'true');
  }, Math.max(1400, holdMs || 2200));
}

function renderPlayersGrid(msg) {
  const grid = $('game-players');
  const prompt = msg.prompt;
  const candidates = new Set(prompt?.candidates || []);
  const byTarget = votersByTarget(msg.votes);
  grid.innerHTML = '';
  (msg.players || []).forEach(p => {
    const meta = ROLE_META[p.role] || { icon: '❓', name: p.role || '?' };
    const isMe = p.id === myId;
    const isSelectable = p.alive && candidates.has(p.id);
    const isSelected = selectedTargets.includes(p.id);
    const isWolf = p.role && ROLE_META[p.role]?.faction === 'wolf';
    const card = document.createElement('div');
    card.className = [
      'player-card',
      !p.alive ? 'dead' : '',
      isSelectable ? 'selectable' : '',
      isSelected ? 'selected-card' : '',
      isWolf && p.role ? 'wolf-revealed' : '',
    ].filter(Boolean).join(' ');
    card.dataset.pid = p.id;
    const voters = byTarget[p.id] || [];
    const wolfScope = msg.votes?.scope === 'wolf';
    card.innerHTML = `
      ${isMe ? '<span class="pc-you-tag">Bạn</span>' : ''}
      ${voters.length ? `<span class="pc-votes ${wolfScope ? 'pc-votes-wolf' : ''}" title="${esc(voters.map(nameOf).join(', '))}">${wolfScope ? '🐺' : '🗳️'} ${voters.length}</span>` : ''}
      <div class="pc-avatar ${!p.alive ? 'dead-avatar' : ''}">${p.alive ? initials(p.name) : '💀'}</div>
      <div class="pc-name">${esc(p.name)}</div>
      ${p.role ? `<div class="pc-role">${meta.icon} ${meta.name}</div>` : '<div class="pc-role" style="color:transparent">-</div>'}
      ${voters.length ? `<div class="pc-voters">${esc(voters.map(nameOf).join(', '))}</div>` : ''}`;
    if (isSelectable) card.addEventListener('click', () => toggleTarget(p.id, msg));
    grid.appendChild(card);
  });
}

function toggleTarget(pid, msg) {
  const prompt = msg.prompt; if (!prompt) return;
  const count = prompt.count || 1;
  const idx = selectedTargets.indexOf(pid);
  if (idx !== -1) selectedTargets.splice(idx, 1);
  else { if (selectedTargets.length >= count) selectedTargets = [pid]; else selectedTargets.push(pid); }
  SFX.play('select');
  renderPlayersGrid(msg);
  renderCandidateList(prompt, msg.players);
  updateConfirmBtn(prompt);
}

// Tiêu đề ô hành động theo vai, để người chơi biết mình đang được hỏi gì.
const PICK_TITLES = {
  seer:      ['🔮 Tiên Tri soi',    'Chọn 1 người để biết họ thuộc phe nào'],
  wolf_seer: ['🐺 Sói Tiên Tri soi', 'Chọn 1 người để biết vai chính xác của họ'],
  guard:     ['🛡️ Bảo Vệ che chở',  'Chọn 1 người để chặn đòn của Sói đêm nay'],
  wolf:      ['🐺 Bầy Sói cắn',     'Cả bầy phải thống nhất một con mồi'],
  white_wolf:['🤍 Sói Trắng',       'Chọn 1 con Sói khác để thịt (hoặc bỏ qua)'],
  cupid:     ['💘 Cupid ghép đôi',  'Chọn 2 người — họ sống chết cùng nhau'],
};

function renderActionPanel(msg) {
  const panel = $('action-panel'), prompt = msg.prompt;
  // Thợ Săn bắn khi ĐÃ chết — không được ẩn ô hành động theo trạng thái sống.
  if (prompt) $('night-result-panel').style.display = 'none';
  if (!prompt) { panel.style.display = 'none'; currentPrompt = null; promptKey = null; return; }
  // Người khác hành động cũng làm server broadcast lại state — không được xoá
  // lựa chọn đang dở của mình, chỉ reset khi thật sự sang lượt mới.
  const key = `${msg.phase}|${msg.night}|${prompt.action}`;
  if (key !== promptKey) {
    promptKey = key; selectedTargets = []; witchAction = null;
  }
  currentPrompt = prompt; panel.style.display = '';
  const witchPanel = $('witch-panel'), candidatesEl = $('action-candidates');
  if (prompt.action === 'witch') {
    renderWitchPanel(prompt, msg);
  } else {
    witchPanel.style.display = 'none'; candidatesEl.style.display = '';
    const titles = {
      vote:  ['🗳️ Bỏ phiếu treo cổ', 'Chọn người bạn nghi là Sói'],
      shoot: ['🏹 Thợ Săn bắn',       'Bạn vừa ngã xuống — kéo theo một người'],
      pick:  ['🎯 Chọn mục tiêu',     `Chọn ${prompt.count || 1} người`],
    };
    const [title, hint] =
      (prompt.action === 'pick' && PICK_TITLES[prompt.role]) || titles[prompt.action] || titles.pick;
    $('action-title').textContent = title; $('action-hint').textContent = hint;
    renderCandidateList(prompt, msg.players);
  }
  updateConfirmBtn(prompt);
}

function renderWitchPanel(prompt, msg) {
  $('witch-panel').style.display = '';
  $('action-candidates').style.display = 'none';
  $('action-title').textContent = '🧙‍♀️ Phù Thủy';
  $('action-hint').textContent = 'Chọn một bình để dùng, hoặc bấm “Bỏ qua” để giữ lại.';

  const bitten = prompt.bitten;
  const bittenName = msg.players?.find(p => p.id === bitten)?.name || bitten;
  $('witch-bitten-info').innerHTML = bitten
    ? `🩸 Bầy Sói cắn <strong>${esc(bittenName)}</strong> đêm nay`
    : '✨ Bầy Sói không cắn ai đêm nay';

  const healBtn = $('btn-witch-heal'), poisonBtn = $('btn-witch-poison');
  const choice = $('witch-choice');
  choice.style.display = 'none';
  $('witch-poison-target').style.display = 'none';

  // Luôn hiện cả hai bình, kèm lý do khi không dùng được — trước đây nút bị ẩn hẳn.
  healBtn.disabled = !prompt.can_heal;
  healBtn.classList.toggle('is-disabled', !prompt.can_heal);
  $('witch-heal-state').textContent = prompt.heal_used
    ? 'đã dùng hết' : (bitten ? 'còn 1 — cứu người bị cắn' : 'không có ai để cứu');

  poisonBtn.disabled = !prompt.can_poison;
  poisonBtn.classList.toggle('is-disabled', !prompt.can_poison);
  $('witch-poison-state').textContent = prompt.poison_used ? 'đã dùng hết' : 'còn 1';

  const setChoice = (html, cls) => {
    choice.className = 'witch-choice ' + cls;
    choice.innerHTML = html;
    choice.style.display = '';
    $('btn-confirm-action').disabled = false;
  };

  healBtn.onclick = () => {
    if (healBtn.disabled) return;
    witchAction = { heal: bitten, poison: null };
    healBtn.classList.add('is-armed'); poisonBtn.classList.remove('is-armed');
    SFX.play('heal');
    setChoice(`🧪 Sẽ cứu <strong>${esc(bittenName)}</strong>`, 'choice-heal');
  };
  poisonBtn.onclick = () => {
    if (poisonBtn.disabled) return;
    witchAction = null;
    poisonBtn.classList.add('is-armed'); healBtn.classList.remove('is-armed');
    choice.style.display = 'none';
    $('btn-confirm-action').disabled = true;
    $('witch-poison-target').style.display = '';
    renderWitchPoisonCandidates(prompt.candidates, msg.players, setChoice);
    SFX.play('select');
  };

  // State được broadcast lại khi người khác hành động — dựng lại lựa chọn đã chốt.
  if (witchAction?.heal) {
    healBtn.classList.add('is-armed');
    setChoice(`🧪 Sẽ cứu <strong>${esc(bittenName)}</strong>`, 'choice-heal');
  } else if (witchAction?.poison) {
    const name = msg.players?.find(p => p.id === witchAction.poison)?.name || witchAction.poison;
    poisonBtn.classList.add('is-armed');
    setChoice(`☠️ Sẽ đầu độc <strong>${esc(name)}</strong>`, 'choice-poison');
  }
}

function renderCandidateList(prompt, players) {
  const el = $('action-candidates'); el.innerHTML = '';
  if (!prompt?.candidates) return;
  prompt.candidates.forEach(pid => {
    const player = players?.find(p => p.id === pid), name = player?.name || pid;
    const isSelected = selectedTargets.includes(pid);
    const btn = document.createElement('button');
    btn.className = 'candidate-btn' + (isSelected ? ' selected' : '');
    btn.innerHTML = `<div class="cand-avatar">${initials(name)}</div><span class="cand-name">${esc(name)}</span><span class="cand-check">✓</span>`;
    btn.addEventListener('click', () => {
      const count = prompt.count || 1, idx = selectedTargets.indexOf(pid);
      if (idx !== -1) selectedTargets.splice(idx, 1);
      else { if (selectedTargets.length >= count) selectedTargets = [pid]; else selectedTargets.push(pid); }
      SFX.play('select');
      renderCandidateList(prompt, players); updateConfirmBtn(prompt);
      if (gameState) renderPlayersGrid(gameState);
    });
    el.appendChild(btn);
  });
}

function renderWitchPoisonCandidates(candidates, players, setChoice) {
  const el = $('witch-poison-candidates'); el.innerHTML = '';
  (candidates || []).forEach(pid => {
    const player = players?.find(p => p.id === pid), name = player?.name || pid;
    const btn = document.createElement('button');
    btn.className = 'candidate-btn';
    btn.innerHTML = `<div class="cand-avatar">${initials(name)}</div><span class="cand-name">${esc(name)}</span>`;
    btn.addEventListener('click', () => {
      witchAction = { heal: null, poison: pid };
      SFX.play('poison');
      $('witch-poison-target').style.display = 'none';
      setChoice(`☠️ Sẽ đầu độc <strong>${esc(name)}</strong>`, 'choice-poison');
    });
    el.appendChild(btn);
  });
}

function updateConfirmBtn(prompt) {
  const btn = $('btn-confirm-action');
  if (!prompt) { btn.disabled = true; return; }
  if (prompt.action === 'witch') btn.disabled = (witchAction === null);
  else btn.disabled = selectedTargets.length !== (prompt.count || 1);
}

function renderLog() {
  const log = window._gameLog || [];
  $('log-count').textContent = log.length;
  const logList = $('log-list'); logList.innerHTML = '';
  [...log].reverse().forEach(line => {
    const div = document.createElement('div'); div.className = 'log-entry'; div.textContent = line; logList.appendChild(div);
  });
}

function logPush(line) {
  if (!window._gameLog) window._gameLog = [];
  window._gameLog.push(line);
  renderLog();
}

function dismissPrivateMessage() {
  document.querySelectorAll('.private-msg').forEach(el => el.remove());
}

/**
 * Thông báo riêng. `kind === 'reveal'` là lời phán của Tiên Tri — phải nằm lại
 * trên màn hình cho tới khi người chơi tự tắt, không được tự mờ đi.
 */
function showPrivateMessage(text, kind) {
  dismissPrivateMessage();
  const isReveal = kind === 'reveal';
  const div = document.createElement('div');
  div.className = 'private-msg' + (isReveal ? ' private-reveal' : '');
  div.innerHTML = `
    <span class="private-icon">${isReveal ? '🔮' : '🔒'}</span>
    <span class="private-text"></span>
    <button class="private-close" aria-label="Đóng">✕</button>`;
  div.querySelector('.private-text').textContent = text;
  div.querySelector('.private-close').addEventListener('click', () => div.remove());
  $('screen-game').insertBefore(div, $('my-role-card').nextSibling);
  if (isReveal) SFX.play('reveal');
  showToast((isReveal ? '🔮 ' : '🔒 ') + text);
  logPush(text);
}

// ══════════════════════════════════════════
//  CHAT
// ══════════════════════════════════════════
const CHAT_META = {
  wolf:    ['🐺 Bàn bạc bầy Sói', 'Chỉ phe Sói đọc được'],
  village: ['💬 Làng trò chuyện', 'Cả làng đọc được'],
};

function renderChatPanel(msg) {
  const panel = $('chat-panel'), phase = msg.phase || '';
  if (phase === 'lobby' || phase === 'game_over') { panel.style.display = 'none'; return; }
  panel.style.display = '';

  const channel = msg.chat_channel;
  const you = msg.you || {};
  const myFaction = ROLE_META[you.role]?.faction;
  // Kênh đang hiển thị: nói được thì theo kênh đó, không thì theo phe/pha.
  const shown = channel || (phase.startsWith('night_') && myFaction === 'wolf' ? 'wolf' : 'village');
  const [title, note] = CHAT_META[shown] || CHAT_META.village;
  panel.classList.toggle('chat-wolf', shown === 'wolf');
  $('chat-title').textContent = title;

  const input = $('chat-input'), sendBtn = $('chat-send');
  input.disabled = sendBtn.disabled = !channel;
  if (channel) {
    $('chat-note').textContent = note;
    input.placeholder = channel === 'wolf'
      ? 'Bàn với đồng đội sói…' : 'Nhắn cho cả làng…';
  } else if (you.alive === false) {
    $('chat-note').textContent = 'Người chết chỉ được nghe';
    input.placeholder = 'Bạn đã chết — không nhắn được';
  } else {
    $('chat-note').textContent = 'Đêm xuống — cả làng đang ngủ';
    input.placeholder = 'Chờ trời sáng để nói…';
  }
}

function addChatMessage(msg, silent) {
  const list = $('chat-messages');
  const mine = msg.from_id === myId;
  const near = list.scrollHeight - list.scrollTop - list.clientHeight < 60;
  const div = document.createElement('div');
  div.className = 'chat-msg' + (mine ? ' chat-mine' : '') +
                  (msg.channel === 'wolf' ? ' chat-msg-wolf' : '');
  div.innerHTML = `<span class="chat-from"></span><span class="chat-text"></span>`;
  div.querySelector('.chat-from').textContent = mine ? 'Bạn' : msg.from_name;
  div.querySelector('.chat-text').textContent = msg.text;
  list.appendChild(div);
  while (list.children.length > 120) list.removeChild(list.firstChild);
  if (near || mine) list.scrollTop = list.scrollHeight;
  if (!silent && !mine) SFX.play('select');
}

function clearChat() { $('chat-messages').innerHTML = ''; }

$('chat-form').addEventListener('submit', e => {
  e.preventDefault();
  const input = $('chat-input'), text = input.value.trim();
  if (!text) return;
  send({ type: 'chat', text });
  input.value = '';
});

// ══════════════════════════════════════════
//  COUNTDOWN
// ══════════════════════════════════════════
function startCountdown(ts, total) {
  clearCountdown();
  deadlineEnd = ts;
  countdownTotal = total || Math.max(1, ts - Date.now() / 1000);
  updateCountdown();
  countdownTimer = setInterval(updateCountdown, 250);
}
function paintClocks(label, urgent) {
  document.querySelectorAll('[data-countdown]').forEach(el => {
    el.textContent = label;
    el.classList.toggle('urgent', urgent);
  });
}

function updateCountdown() {
  if (!deadlineEnd) return;
  const remaining = Math.max(0, deadlineEnd - Date.now() / 1000);
  const bar = $('countdown-bar');
  bar.style.width = Math.min(100, (remaining / (countdownTotal || 1)) * 100) + '%';
  const urgent = remaining <= 10;
  bar.classList.toggle('urgent', urgent);
  paintClocks(remaining > 0 ? formatClock(remaining) : '', urgent);

  // Nhịp tim 10 giây cuối — mỗi giây một tiếng, không lặp trong cùng một giây.
  const sec = Math.ceil(remaining);
  if (urgent && remaining > 0 && sec !== lastTickAt) {
    lastTickAt = sec;
    SFX.play(sec <= 3 ? 'alarm' : 'tick');
  }
  if (remaining <= 0) clearCountdown();
}
function formatClock(sec) {
  const s = Math.ceil(sec);
  return s >= 60 ? `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}` : `${s}s`;
}
function clearCountdown() {
  clearInterval(countdownTimer); countdownTimer = null; deadlineEnd = null;
  lastTickAt = null; countdownTotal = 0;
  const bar = $('countdown-bar');
  bar.style.width = '100%'; bar.classList.remove('urgent');
  paintClocks('', false);
}

// ══════════════════════════════════════════
//  ROLE CONFIG (host lobby)
// ══════════════════════════════════════════

function loadPreset(n) {
  const preset = DEFAULT_SETUPS[n] || DEFAULT_SETUPS[5];
  roleCounts = {};
  preset.forEach(id => { roleCounts[id] = (roleCounts[id] || 0) + 1; });
}

function totalRoles() {
  return Object.values(roleCounts).reduce((s, v) => s + v, 0);
}

function renderRoleConfig() {
  const n = playerCount || 5;
  // Load preset if roleCounts empty
  if (Object.keys(roleCounts).length === 0) loadPreset(n);

  // Update hint
  const total = totalRoles();
  const diff = total - n;
  let hintText = n > 0 ? `${n} người chơi — cần đúng ${n} vai` : 'Đang chờ người chơi…';
  if (n > 0 && diff !== 0) {
    hintText = diff > 0
      ? `⚠️ Đang thừa ${diff} vai (cần bỏ bớt)`
      : `⚠️ Đang thiếu ${Math.abs(diff)} vai`;
  } else if (n > 0 && diff === 0) {
    hintText = `✅ ${n} người — bộ vai hợp lệ`;
  }
  $('cfg-player-hint').textContent = hintText;

  // Render role rows
  const list = $('role-config-list');
  list.innerHTML = '';
  ALL_ROLE_IDS.forEach(id => {
    const meta = ROLE_META[id];
    const count = roleCounts[id] || 0;
    const isWolf = meta.faction === 'wolf';

    // Min counts per role (can't go below 0, wolf needs at least 1 if present)
    const minCount = 0;
    const maxCount = Math.max(n || 18, 1);

    const row = document.createElement('div');
    row.className = `role-cfg-row${count > 0 ? ' has-count' : ' disabled-row'}`;

    row.innerHTML = `
      <span class="role-cfg-icon">${meta.icon}</span>
      <div class="role-cfg-info">
        <div class="role-cfg-name">
          ${esc(meta.name)}
          ${isWolf ? '<span class="wolf-tag">Sói</span>' : ''}
        </div>
        <div class="role-cfg-sub">${esc(meta.short)}</div>
      </div>
      <div class="role-cfg-right">
        <div class="role-cfg-stepper">
          <button class="cfg-step-btn" data-role="${id}" data-dir="-1" ${count <= minCount ? 'disabled' : ''}>−</button>
          <span class="cfg-count-badge ${count === 0 ? 'zero' : ''}">${count}</span>
          <button class="cfg-step-btn" data-role="${id}" data-dir="1" ${count >= maxCount ? 'disabled' : ''}>+</button>
        </div>
        <button class="btn-role-info-sm" data-role="${id}" title="Xem luật ${meta.name}">?</button>
      </div>`;
    list.appendChild(row);
  });

  // Steppers
  list.querySelectorAll('.cfg-step-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const id = btn.dataset.role, dir = parseInt(btn.dataset.dir, 10);
      roleCounts[id] = Math.max(0, (roleCounts[id] || 0) + dir);
      renderRoleConfig();
      sendConfig();
    });
  });

  // Info buttons
  list.querySelectorAll('.btn-role-info-sm').forEach(btn => {
    btn.addEventListener('click', () => openRoleModal(btn.dataset.role));
  });

  // Preview chips
  renderRolePreview();

  // Enable/disable start button
  const startBtn = $('btn-start');
  if (n >= 5 && diff === 0) {
    startBtn.disabled = false;
    startBtn.textContent = '🌙 Bắt đầu ván';
  } else if (n < 5) {
    startBtn.disabled = true;
    startBtn.textContent = `🌙 Cần ít nhất 5 người`;
  } else {
    startBtn.disabled = true;
    startBtn.textContent = diff > 0 ? `🌙 Bỏ bớt ${diff} vai` : `🌙 Thêm ${Math.abs(diff)} vai`;
  }
}

function renderRolePreview() {
  const chips = $('role-preview-chips');
  chips.innerHTML = '';
  ALL_ROLE_IDS.forEach(id => {
    const count = roleCounts[id] || 0;
    if (count === 0) return;
    const meta = ROLE_META[id];
    const chip = document.createElement('span');
    chip.className = `role-chip ${meta.faction === 'wolf' ? 'chip-wolf' : 'chip-village'}`;
    chip.innerHTML = `${meta.icon} ${meta.name}${count > 1 ? ` ×${count}` : ''}`;
    chips.appendChild(chip);
  });
  if (chips.children.length === 0) {
    chips.innerHTML = '<span style="color:var(--text-muted);font-size:12px">Chưa có vai nào</span>';
  }
}

function sendConfig() {
  // Build disabled_roles list (roles with count 0)
  const disabledList = ALL_ROLE_IDS.filter(id => !roleCounts[id] || roleCounts[id] === 0);
  send({
    type: 'config',
    roles: Object.fromEntries(ALL_ROLE_IDS.map(id => [id, !!(roleCounts[id] && roleCounts[id] > 0)])),
    timers: {
      night_phase: timers.night_phase,
      day_discuss: timers.day_discuss,
      day_vote: timers.day_vote,
      hunter_shot: timers.hunter_shot,
    },
  });
}

// ── Config tabs ──
document.querySelectorAll('.cfg-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.cfg-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.cfg-tab-body').forEach(b => b.style.display = 'none');
    tab.classList.add('active');
    $(`cfg-tab-${tab.dataset.tab}`).style.display = '';
  });
});

// ── Timer steppers ──
document.querySelectorAll('.step-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const key = btn.dataset.timer, dir = parseInt(btn.dataset.dir, 10);
    const steps = { night_phase: 15, day_discuss: 30, day_vote: 15, hunter_shot: 15 };
    const mins  = { night_phase: 15, day_discuss: 30, day_vote: 15, hunter_shot: 15 };
    const maxes = { night_phase: 120, day_discuss: 600, day_vote: 180, hunter_shot: 120 };
    const step = steps[key] || 30, min = mins[key] || 15, max = maxes[key] || 600;
    timers[key] = Math.max(min, Math.min(max, (timers[key] || 60) + dir * step));
    $(`timer-${key}`).textContent = timers[key];
    sendConfig();
  });
});

// ── Preset button ──
$('btn-preset').addEventListener('click', () => {
  loadPreset(playerCount || 5);
  renderRoleConfig();
  sendConfig();
  showToast('Đã khôi phục bộ vai mặc định', 'success');
});

// ══════════════════════════════════════════
//  MODAL — ROLE DETAIL
// ══════════════════════════════════════════
function openRoleModal(roleId) {
  const meta = ROLE_META[roleId];
  if (!meta) return;

  $('modal-role-icon').textContent = meta.icon;
  $('modal-role-title').textContent = meta.name;
  const factionEl = $('modal-role-faction');
  factionEl.textContent = meta.faction === 'wolf' ? 'Phe Sói' : 'Phe Dân';
  factionEl.className = `faction-badge ${meta.faction === 'wolf' ? 'faction-wolf' : 'faction-village'}`;
  $('modal-role-desc').textContent = meta.desc;

  const rulesEl = $('modal-role-rules');
  rulesEl.innerHTML = '';
  (meta.rules || []).forEach(r => {
    const div = document.createElement('div');
    div.className = 'rule-item';
    div.innerHTML = `<span class="rule-icon">${r.icon}</span><span class="rule-text">${r.text}</span>`;
    rulesEl.appendChild(div);
  });

  $('modal-role-tip').textContent = meta.tip || '';
  $('modal-role').style.display = 'flex';
  document.body.style.overflow = 'hidden';
}

function closeRoleModal() {
  $('modal-role').style.display = 'none';
  document.body.style.overflow = '';
}

$('btn-modal-role-close').addEventListener('click', closeRoleModal);
$('modal-role').addEventListener('click', e => { if (e.target === $('modal-role')) closeRoleModal(); });

// ── Game screen role info button ──
$('btn-my-role-info').addEventListener('click', () => {
  const roleId = gameState?.you?.role;
  if (roleId) openRoleModal(roleId);
});

// ══════════════════════════════════════════
//  MODAL — ROLE GUIDE (all roles)
// ══════════════════════════════════════════
let guideFilter = 'all';

function openGuideModal() {
  renderGuideList();
  $('modal-guide').style.display = 'flex';
  document.body.style.overflow = 'hidden';
}

function closeGuideModal() {
  $('modal-guide').style.display = 'none';
  document.body.style.overflow = '';
}

function renderGuideList() {
  const list = $('guide-role-list');
  list.innerHTML = '';
  ALL_ROLE_IDS.forEach(id => {
    const meta = ROLE_META[id];
    if (guideFilter !== 'all' && meta.faction !== guideFilter) return;
    const isWolf = meta.faction === 'wolf';

    const card = document.createElement('div');
    card.className = `guide-role-card${isWolf ? ' wolf-card' : ''}`;

    card.innerHTML = `
      <div class="guide-role-summary">
        <span class="guide-role-emoji">${meta.icon}</span>
        <div class="guide-role-meta">
          <div class="guide-role-meta-name">
            ${esc(meta.name)}
            <span class="faction-badge ${isWolf ? 'faction-wolf' : 'faction-village'}" style="font-size:10px;padding:1px 6px">
              ${isWolf ? 'Sói' : 'Dân'}
            </span>
          </div>
          <div class="guide-role-meta-short">${esc(meta.short)}</div>
        </div>
        <span class="guide-expand-icon">▼</span>
      </div>
      <div class="guide-role-detail">
        <p style="margin-bottom:10px">${esc(meta.desc)}</p>
        <div class="guide-detail-rules">
          ${(meta.rules || []).map(r =>
            `<div class="rule-item"><span class="rule-icon">${r.icon}</span><span class="rule-text">${r.text}</span></div>`
          ).join('')}
        </div>
        ${meta.tip ? `<div class="modal-role-tip" style="margin-top:10px">${esc(meta.tip)}</div>` : ''}
      </div>`;

    // Toggle expand
    card.querySelector('.guide-role-summary').addEventListener('click', () => {
      card.classList.toggle('expanded');
    });

    list.appendChild(card);
  });
}

document.querySelectorAll('.guide-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.guide-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    guideFilter = tab.dataset.faction;
    renderGuideList();
  });
});

$('btn-modal-guide-close').addEventListener('click', closeGuideModal);
$('modal-guide').addEventListener('click', e => { if (e.target === $('modal-guide')) closeGuideModal(); });
$('btn-open-guide').addEventListener('click', openGuideModal);

// ══════════════════════════════════════════
//  ACTION BUTTONS
// ══════════════════════════════════════════
$('btn-confirm-action').addEventListener('click', () => {
  const prompt = currentPrompt; if (!prompt) return;
  if (prompt.action === 'vote') {
    send({ type: 'vote', target: selectedTargets[0] || null });
  } else if (prompt.action === 'witch') {
    if (!witchAction) return;
    send({ type: 'action', phase: 'night_witch', targets: [], extra: { heal: witchAction.heal, poison: witchAction.poison } });
  } else {
    send({ type: 'action', phase: gameState?.phase || '', targets: selectedTargets, extra: {} });
  }
  SFX.play(prompt.action === 'shoot' ? 'shot' : 'confirm');
  selectedTargets = []; witchAction = null;
  $('btn-confirm-action').disabled = true;
  showToast('Đã gửi hành động ✓', 'success');
});

$('btn-skip-action').addEventListener('click', () => {
  const prompt = currentPrompt; if (!prompt) return;
  if (prompt.action === 'vote') send({ type: 'vote', target: null });
  else if (prompt.action === 'witch') send({ type: 'action', phase: 'night_witch', targets: [], extra: { heal: null, poison: null } });
  else send({ type: 'skip' });
  SFX.play('select');
  selectedTargets = []; witchAction = null;
  $('action-panel').style.display = 'none';
  showToast('Đã bỏ qua', '');
});

$('btn-result-ok').addEventListener('click', () => { $('night-result-panel').style.display = 'none'; });

// ══════════════════════════════════════════
//  ÂM THANH
// ══════════════════════════════════════════
function renderSoundBtn() {
  const btn = $('btn-sound');
  btn.textContent = SFX.muted ? '🔇' : '🔊';
  btn.classList.toggle('is-muted', SFX.muted);
}
$('btn-sound').addEventListener('click', () => {
  SFX.unlock();
  SFX.setMuted(!SFX.muted);
  renderSoundBtn();
  if (!SFX.muted) {
    SFX.play('confirm');
    const phase = gameState?.phase;
    if (phase && phase !== 'game_over') {
      SFX.setAmbience(phase.startsWith('night_') ? 'night' : 'day');
    }
  }
  showToast(SFX.muted ? '🔇 Đã tắt âm thanh' : '🔊 Đã bật âm thanh');
});
renderSoundBtn();

// Trình duyệt chỉ cho phát tiếng sau thao tác đầu tiên của người dùng.
['pointerdown', 'keydown', 'touchstart'].forEach(evt =>
  window.addEventListener(evt, () => SFX.unlock(), { once: true, passive: true }));

// ══════════════════════════════════════════
//  HOME
// ══════════════════════════════════════════
$('btn-create').addEventListener('click', () => {
  const name = $('input-name').value.trim();
  if (!name) { showToast('Nhập tên của bạn trước', 'error'); return; }
  connectWS({ type: 'join', room: '', name });
});
$('btn-join').addEventListener('click', () => {
  const name = $('input-name').value.trim(), room = $('input-room').value.trim().toUpperCase();
  if (!name) { showToast('Nhập tên của bạn trước', 'error'); return; }
  if (!room) { showToast('Nhập mã phòng', 'error'); return; }
  connectWS({ type: 'join', room, name });
});
$('input-room').addEventListener('keydown', e => { if (e.key === 'Enter') $('btn-join').click(); });
$('input-name').addEventListener('keydown', e => {
  if (e.key === 'Enter') { if ($('input-room').value.trim()) $('btn-join').click(); else $('btn-create').click(); }
});

// ══════════════════════════════════════════
//  LOBBY
// ══════════════════════════════════════════
$('btn-copy-code').addEventListener('click', () => {
  const code = $('lobby-code').textContent;
  navigator.clipboard.writeText(code).then(() => showToast(`Đã sao chép: ${code}`, 'success'));
});
$('btn-start').addEventListener('click', () => send({ type: 'start' }));

// ══════════════════════════════════════════
//  LEAVE ROOM
// ══════════════════════════════════════════
let _leaveContext = 'lobby'; // 'lobby' | 'game'

const LEAVE_TEXT = {
  game: ['Rời ván chơi?',
         'Ván đang chạy. Bạn sẽ mất kết nối nhưng ghế ngồi vẫn giữ — có thể vào lại bằng mã phòng và token.',
         'Rời ván'],
  wait: ['Thôi không chờ nữa?',
         'Bạn sẽ ra khỏi hàng chờ và không được xếp ghế ở ván sau.',
         'Rời hàng chờ'],
  lobby: ['Rời phòng?',
          'Bạn sẽ bị xóa khỏi phòng. Muốn vào lại phải nhập mã phòng mới.',
          'Rời phòng'],
};

function openLeaveModal(context) {
  _leaveContext = context;
  const [title, body, confirm] = LEAVE_TEXT[context] || LEAVE_TEXT.lobby;
  $('modal-leave-title').textContent = title;
  $('modal-leave-body').textContent = body;
  $('btn-leave-confirm').textContent = confirm;
  $('modal-leave').style.display = 'flex';
  document.body.style.overflow = 'hidden';
}

function closeLeaveModal() {
  $('modal-leave').style.display = 'none';
  document.body.style.overflow = '';
}

async function doLeave() {
  closeLeaveModal();
  send({ type: 'leave' });
  // Chờ server xử lý `leave` rồi mới đóng socket.
  await new Promise(r => setTimeout(r, 150));
  resetToHome();
}

$('btn-leave-lobby').addEventListener('click', () => openLeaveModal('lobby'));
$('btn-leave-game').addEventListener('click',  () => openLeaveModal('game'));
$('btn-leave-cancel').addEventListener('click', closeLeaveModal);
$('modal-leave').addEventListener('click', e => { if (e.target === $('modal-leave')) closeLeaveModal(); });
$('btn-leave-confirm').addEventListener('click', doLeave);

// ══════════════════════════════════════════
//  GAME OVER
// ══════════════════════════════════════════
$('btn-play-again').addEventListener('click', () => resetToHome());

$('btn-rematch').addEventListener('click', () => {
  send({ type: 'rematch' });
  SFX.play('confirm');
  $('btn-rematch').disabled = true;
});

$('btn-leave-wait').addEventListener('click', () => openLeaveModal('wait'));

// ══════════════════════════════════════════
//  HELPERS
// ══════════════════════════════════════════
function initials(name) {
  if (!name) return '?';
  const p = name.trim().split(/\s+/);
  return p.length === 1 ? p[0][0].toUpperCase() : (p[0][0] + p[p.length - 1][0]).toUpperCase();
}
function esc(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ══════════════════════════════════════════
//  AUTO-RECONNECT
// ══════════════════════════════════════════
window.addEventListener('load', () => {
  const token = localStorage.getItem('masoi_token');
  if (token) { myToken = token; connectWS({ type: 'join', token }); }
  else startRoomPolling();
});

// Quay lại tab thì làm mới danh sách phòng ngay, khỏi đợi nhịp poll.
document.addEventListener('visibilitychange', () => {
  if (document.hidden) return;
  if ($('screen-home').classList.contains('active')) refreshRooms();
});
