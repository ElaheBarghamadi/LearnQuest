(function () {
'use strict';

const $ = (s, r) => (r || document).querySelector(s);
const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
const FA = '۰۱۲۳۴۵۶۷۸۹';
const faNum = (s) => String(s).replace(/\d/g, (d) => FA[+d]);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) =>
    ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));

async function api(url, opts) {
    const res = await fetch(url, opts);
    let data = null;
    try { data = await res.json(); } catch (e) { /* بدنه خالی */ }
    return { ok: res.ok, status: res.status, data };
}
// Django protects every state-changing endpoint.  Read the token supplied by
// base.html (with a cookie fallback) so group management does not silently fail.
function csrfToken() {
    const injected = document.querySelector('#lqCsrf')?.value;
    if (injected) return injected;
    const row = document.cookie.split('; ').find((item) => item.startsWith('csrftoken='));
    return row ? decodeURIComponent(row.split('=').slice(1).join('=')) : '';
}
const post = (url, body) => api(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken() },
    credentials: 'same-origin',
    body: body ? JSON.stringify(body) : '{}',
});

function toast(msg, kind) {
    const t = document.createElement('div');
    t.className = 'ms-toast' + (kind === 'error' ? ' error' : kind === 'ok' ? ' ok' : '');
    t.textContent = msg;
    $('#msToasts').appendChild(t);
    setTimeout(() => { t.style.opacity = '0'; t.style.transition = '.4s'; }, 3400);
    setTimeout(() => t.remove(), 3900);
}

const PALETTE = [
    ['#0ea5a4', '#0284c7'], ['#8b5cf6', '#6366f1'], ['#f59e0b', '#ef4444'],
    ['#ec4899', '#8b5cf6'], ['#10b981', '#0ea5e9'], ['#f97316', '#f59e0b'],
];
function avatarStyle(key) {
    let h = 0;
    for (const ch of String(key)) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
    const [a, b] = PALETTE[h % PALETTE.length];
    return `background:linear-gradient(135deg,${a},${b})`;
}
function avatarHTML(key, label, online, imageUrl = '') {
    const dot = online === undefined ? '' :
        `<span class="dot${online ? ' on' : ''}"></span>`;
    const face = imageUrl ? `<img src="${esc(imageUrl)}" alt="">` : esc(label);
    return `<div class="ms-avatar" style="${avatarStyle(key)}">${face}${dot}</div>`;
}

const state = {
    me: window.MS_ME,
    meName: window.MS_ME_NAME,
    convs: [],
    activeId: null,
    active: null,          // آبجکت conversation فعال
    participants: [],
    ws: null,
    wsFailCount: 0,
    pollTimer: null,
    typingTimer: null,
    typingSent: false,
    typingHideTimer: null,
    groupMembers: [],      // انتخاب‌شده‌ها برای گروه جدید
    addMembers: [],        // انتخاب‌شده‌ها برای افزودن عضو
};

function openModal(id) { $(id).classList.add('open'); }
function closeModal(el) { el.closest('.ms-modal-back')?.classList.remove('open'); }
$$('.ms-modal-back').forEach((m) => {
    m.addEventListener('click', (e) => { if (e.target === m) m.classList.remove('open'); });
});
$$('[data-close]').forEach((b) => b.addEventListener('click', () => closeModal(b)));

let confirmCb = null;
function confirmDialog(title, text, cb) {
    $('#confirmTitle').textContent = title;
    $('#confirmText').textContent = text;
    confirmCb = cb;
    openModal('#modalConfirm');
}
$('#confirmYes').addEventListener('click', () => {
    closeModal($('#confirmYes'));
    if (confirmCb) confirmCb();
});

function convLabel(c) {
    return c.is_group ? '👥' : (c.username || '؟').trim().charAt(0);
}
function renderConvList() {
    const box = $('#msConvs');
    if (!state.convs.length) {
        box.innerHTML = `<div class="ms-convs-empty"><div class="big">📭</div>
            هنوز گفت‌وگویی نداری!<br>با جستجوی کاربر یا ساخت گروه شروع کن.</div>`;
        return;
    }
    box.innerHTML = state.convs.map((c) => `
        <div class="ms-conv${c.id === state.activeId ? ' active' : ''}" data-id="${c.id}">
            ${avatarHTML(c.username + c.id, convLabel(c), c.is_group ? undefined : c.online)}
            <div class="meta">
                <div class="row1">
                    <span class="name">${esc(c.username)}</span>
                    <span class="time">${faNum(c.last_message_time || '')}</span>
                </div>
                <div class="row2">
                    <span class="preview">${esc(c.last_message || (c.is_group ? `${faNum(c.members_count)} عضو` : 'گفت‌وگوی جدید'))}</span>
                    ${c.unread_count ? `<span class="ms-badge">${faNum(c.unread_count)}</span>` : ''}
                </div>
            </div>
        </div>`).join('');
    $$('.ms-conv', box).forEach((el) =>
        el.addEventListener('click', () => openConv(+el.dataset.id)));
}

async function loadConversations() {
    const r = await api('/messenger/conversations/');
    if (!r.ok || !r.data?.success) { toast('خطا در دریافت گفت‌وگوها', 'error'); return; }
    state.convs = r.data.conversations;
    renderConvList();
    if (state.activeId) {
        state.active = state.convs.find((c) => c.id === state.activeId) || state.active;
    }
}

async function openConv(id) {
    if (state.activeId === id) return;
    state.activeId = id;
    history.replaceState(null, '', `/messenger/?c=${id}`);
    $('#msApp').classList.add('chat-open');
    renderConvList();

    const r = await api(`/messenger/messages/${id}/`);
    if (!r.ok || !r.data?.success) {
        toast(r.data?.error || 'خطا در دریافت پیام‌ها', 'error');
        state.activeId = null; return;
    }
    state.active = r.data.conversation;
    state.participants = r.data.participants || [];
    renderHead();
    renderMessages(r.data.messages);
    renderComposer();

    const c = state.convs.find((x) => x.id === id);
    if (c) { c.unread_count = 0; renderConvList(); }
    connectWS(id);
}

function renderHead() {
    const c = state.active;
    if (!c) return;
    $('#msChatEmpty').style.display = 'none';
    $('#msChatHead').style.display = 'flex';
    $('#msMessages').style.display = 'flex';
    const av = $('#msHeadAvatar');
    av.setAttribute('style', avatarStyle(c.username + c.id));
    av.innerHTML = esc(convLabel(c));
    const nameEl = $('#msHeadName');
    nameEl.innerHTML = c.is_group
        ? esc(c.username)
        : `<a href="/u/${encodeURIComponent(c.username)}/">${esc(c.username)}</a>`;
    const sub = $('#msHeadSub');
    const head = $('#msChatHead');
    head.classList.toggle('group-profile-trigger', Boolean(c.is_group));
    head.title = c.is_group ? 'برای دیدن اعضا و امکانات گروه بزن' : '';
    if (c.is_group) sub.innerHTML = `👥 ${faNum(c.members_count)} عضو <span class="ms-head-open">مشاهدهٔ گروه ←</span>`;
    else sub.innerHTML = c.online ? '<span class="on-txt">● آنلاین</span>'
        : `<span>آفلاین</span>`;
}

function renderComposer() {
    const blocked = state.active && !state.active.is_group && state.active.blocked_between;
    $('#msComposer').style.display = blocked ? 'none' : 'flex';
    $('#msBlockedNote').style.display = blocked ? 'flex' : 'none';
    if (blocked && state.active.blocked_by_me) {
        $('#msBlockedNoteText').innerHTML =
            '⛔ این کاربر را بلاک کردی. برای گفت‌وگو اول از بخش «بلاک‌شده‌ها» رفع بلاک کن.';
    } else {
        $('#msBlockedNoteText').textContent = '⛔ امکان ارسال پیام در این گفت‌وگو وجود ندارد';
    }
    autosize();
}

function dayKey(iso) { return (iso || '').slice(0, 10); }
function dayLabel(m) { return m.created_at_day || dayKey(m.created_at_full); }
function msgHTML(m) {
    if (m.is_system) {
        return `<div class="ms-msg system" data-id="${m.id}"><div class="bubble">${esc(m.content.replace(/^ℹ️\s*/, ''))}</div></div>`;
    }
    const ticks = m.is_mine
        ? `<span class="ticks${m.is_read ? ' read' : ''}" data-ticks="${m.id}">
             <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4">
             <path d="M2 12l5 5L18 6"/><path d="M9 12l5 5L25 6" transform="translate(-3 0)"/></svg></span>`
        : '';
    const groupIncoming = !m.is_mine && state.active?.is_group;
    const sender = groupIncoming
        ? `<a class="sender" href="/u/${encodeURIComponent(m.sender_username)}/">${esc(m.sender_username)}</a>` : '';
    const avatar = groupIncoming
        ? `<a class="ms-message-avatar" href="/u/${encodeURIComponent(m.sender_username)}/" title="${esc(m.sender_username)}">${avatarHTML(m.sender_username + m.sender_id, (m.sender_username || '؟').charAt(0), undefined, m.sender_avatar || '')}</a>` : '';
    return `<div class="ms-msg ${m.is_mine ? 'mine' : 'theirs'}${groupIncoming ? ' group-incoming' : ''}" data-id="${m.id}">${avatar}
        <div class="bubble">${sender}
            <div class="text">${esc(m.content)}</div>
            <span class="b-foot">${faNum(m.created_at)} ${ticks}</span>
        </div></div>`;
}
function renderMessages(messages) {
    const box = $('#msMessages');
    let html = '', lastDay = '';
    for (const m of messages) {
        const dl = dayLabel(m);
        if (dl !== lastDay) {
            html += `<div class="day-sep ms-day-sep">${faNum(dl)}</div>`;
            lastDay = dl;
        }
        html += msgHTML(m);
    }
    box.dataset.lastday = lastDay;
    box.innerHTML = html || `<div class="ms-convs-empty" style="margin:auto"><div class="big">🌱</div>اولین پیام را تو بفرست!</div>`;
    scrollBottom(true);
}
function appendMessage(m) {
    const box = $('#msMessages');
    if (box.querySelector(`[data-id="${m.id}"]`)) return;
    const empty = box.querySelector('.ms-convs-empty');
    if (empty) { box.innerHTML = ''; box.dataset.lastday = ''; }
    const dl = dayLabel(m);
    if (dl && dl !== box.dataset.lastday) {
        if (box.children.length) box.insertAdjacentHTML('beforeend', `<div class="day-sep ms-day-sep">${faNum(dl)}</div>`);
        box.dataset.lastday = dl;
    }
    box.insertAdjacentHTML('beforeend', msgHTML(m));
    const nearBottom = box.scrollHeight - box.scrollTop - box.clientHeight < 160;
    if (nearBottom || m.is_mine) scrollBottom();
    if (!m.is_mine) markRead();
}
function scrollBottom(instant) {
    const box = $('#msMessages');
    box.scrollTo({ top: box.scrollHeight, behavior: instant ? 'auto' : 'smooth' });
}
function markRead() {
    if (state.ws?.readyState === 1) state.ws.send(JSON.stringify({ type: 'mark_read' }));
}

function connectWS(convId) {
    disconnectWS();
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    const ws = new WebSocket(`${proto}://${location.host}/ws/chat/${convId}/`);
    state.ws = ws;
    window.LQ_ACTIVE_CHAT_ID = convId;
    const conn = $('#msConn');
    ws.onopen = () => {
        state.wsFailCount = 0;
        conn.textContent = '● متصل';
        conn.className = 'ms-conn ok show';
        setTimeout(() => conn.classList.remove('show'), 1800);
    };
    ws.onmessage = (ev) => {
        let d; try { d = JSON.parse(ev.data); } catch (e) { return; }
        handleWSEvent(d);
    };
    ws.onclose = (ev) => {
        if (state.activeId !== convId) return;
        window.LQ_ACTIVE_CHAT_ID = null;
        state.wsFailCount++;
        conn.textContent = 'اتصال قطع شد — تلاش مجدد…';
        conn.className = 'ms-conn show';
        if (state.wsFailCount >= 2) startPolling();   // fallback HTTP
        else setTimeout(() => state.activeId === convId && connectWS(convId), 2500);
    };
    ws.onerror = () => { try { ws.close(); } catch (e) {} };
}
function disconnectWS() {
    stopPolling();
    window.LQ_ACTIVE_CHAT_ID = null;
    if (state.ws) { try { state.ws.close(); } catch (e) {} state.ws = null; }
}
function startPolling() {
    stopPolling();
    state.pollTimer = setInterval(async () => {
        if (!state.activeId) return;
        const r = await api(`/messenger/messages/${state.activeId}/`);
        if (r.ok && r.data?.success && state.activeId === r.data.conversation_id) {
            const have = new Set($$('#msMessages [data-id]').map((x) => +x.dataset.id));
            for (const m of r.data.messages) if (!have.has(m.id)) appendMessage(m);
            loadConversations();
        }
    }, 3000);
}
function stopPolling() {
    if (state.pollTimer) { clearInterval(state.pollTimer); state.pollTimer = null; }
}

function handleWSEvent(d) {
    switch (d.type) {
        case 'new_message':
            appendMessage({
                id: d.message_id, sender_id: d.sender_id,
                sender_username: d.sender_username, sender_avatar: d.sender_avatar || '', content: d.content,
                created_at: d.created_at, created_at_full: new Date().toISOString(),
                created_at_day: d.created_at_day || '',
                is_mine: d.is_mine, is_read: false,
                is_system: (d.content || '').startsWith('ℹ️'),
            });
            loadConversations();
            break;
        case 'typing':
            showTyping(d.is_typing);
            break;
        case 'user_status':
            if (state.active && !state.active.is_group && d.user_id === state.active.user_id) {
                state.active.online = d.online; renderHead();
            }
            loadConversations();
            break;
        case 'messages_read':
            $$('.ms-msg.mine .ticks').forEach((t) => t.classList.add('read'));
            break;
        case 'error':
            toast(d.message || 'پیام ارسال نشد', 'error');
            break;
        case 'blocked':
            toast(d.message || 'امکان ارسال نیست', 'error');
            renderComposerBlockedNow();
            break;
    }
}
function showTyping(on) {
    const t = $('#msTyping');
    clearTimeout(state.typingHideTimer);
    if (on) {
        t.classList.add('show');
        state.typingHideTimer = setTimeout(() => t.classList.remove('show'), 2600);
    } else t.classList.remove('show');
}
function renderComposerBlockedNow() {
    if (!state.active) return;
    state.active.blocked_between = true;
    renderComposer();
}

const input = $('#msInput');
function autosize() {
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 120) + 'px';
}
input.addEventListener('input', () => {
    autosize();
    sendTyping();
});
input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendCurrent(); }
});
$('#btnSend').addEventListener('click', sendCurrent);

function sendTyping() {
    if (state.ws?.readyState !== 1) return;
    if (!state.typingSent) {
        state.ws.send(JSON.stringify({ type: 'typing', is_typing: true }));
        state.typingSent = true;
    }
    clearTimeout(state.typingTimer);
    state.typingTimer = setTimeout(() => {
        state.typingSent = false;
        if (state.ws?.readyState === 1)
            state.ws.send(JSON.stringify({ type: 'typing', is_typing: false }));
    }, 1600);
}

async function sendCurrent() {
    const content = input.value.trim();
    if (!content || !state.activeId) return;
    input.value = ''; autosize(); input.focus();

    if (state.ws?.readyState === 1) {
        state.ws.send(JSON.stringify({ type: 'send_message', content }));
    } else {
        const r = await post('/messenger/send/', { conversation_id: state.activeId, content });
        if (!r.ok || !r.data?.success) {
            toast(r.data?.error || 'پیام ارسال نشد', 'error');
            if (r.status === 403) renderComposerBlockedNow();
            return;
        }
        appendMessage(r.data.message);
        loadConversations();
    }
}

const EMOJIS = ['😀','😂','🤣','😊','😍','😘','😉','😎','🤩','🥳','😢','😭','😡','🤔','👍','👎','🙏','👏','💪','🔥','❤️','💔','🎉','✨','💯','⚡','🌹','🤝','😴','🙃'];
$('#btnEmoji').addEventListener('click', (e) => {
    e.stopPropagation();
    const p = $('#msEmojiPanel');
    if (p.style.display === 'none') {
        p.style.display = 'flex';
        p.style.cssText = 'position:absolute;bottom:106%;right:0;background:#fff;border-radius:16px;box-shadow:var(--ms-shadow);' +
            'padding:10px;display:grid;grid-template-columns:repeat(8,1fr);gap:2px;z-index:60;max-width:300px';
        p.innerHTML = EMOJIS.map((e2) =>
            `<button class="ms-emoji-btn" style="font-size:1.15rem">${e2}</button>`).join('');
        $$('button', p).forEach((b) => b.addEventListener('click', () => {
            const s = input.selectionStart || input.value.length;
            input.value = input.value.slice(0, s) + b.textContent + input.value.slice(s);
            input.focus(); autosize();
        }));
    } else p.style.display = 'none';
});
document.addEventListener('click', (e) => {
    const p = $('#msEmojiPanel');
    if (p && p.style.display !== 'none' && !p.contains(e.target)) p.style.display = 'none';
});

let searchTimer = null;
$('#msSearchInput').addEventListener('input', (e) => {
    clearTimeout(searchTimer);
    const q = e.target.value.trim();
    const box = $('#msSearchResults');
    if (q.length < 2) { box.classList.remove('open'); return; }
    searchTimer = setTimeout(async () => {
        const r = await api(`/messenger/search/?q=${encodeURIComponent(q)}`);
        if (!r.ok) return;
        const users = r.data?.users || [];
        box.innerHTML = users.length ? users.map((u) => `
            <div class="ms-search-hit" data-uid="${u.id}" data-name="${esc(u.username)}">
                ${avatarHTML(u.username + u.id, (u.username || '؟').charAt(0), u.online)}
                <div class="meta"><b>${esc(u.username)}</b>
                <small>${u.online ? '🟢 آنلاین' : 'آفلاین'}${u.blocked_by_me ? ' — ⛔ بلاک‌شده' : ''}</small></div>
                <span class="ms-mini-btn">گفت‌وگو</span>
            </div>`).join('')
            : `<div class="ms-search-hit" style="cursor:default"><small>کاربری پیدا نشد</small></div>`;
        box.classList.add('open');
        $$('.ms-search-hit[data-uid]', box).forEach((el) =>
            el.addEventListener('click', () => openDM(+el.dataset.uid)));
    }, 350);
});
document.addEventListener('click', (e) => {
    if (!$('#msSearchResults').contains(e.target) && e.target !== $('#msSearchInput'))
        $('#msSearchResults').classList.remove('open');
});

async function openDM(userId) {
    $('#msSearchResults').classList.remove('open');
    $('#msSearchInput').value = '';
    const r = await api(`/messenger/conversation/${userId}/`);
    if (!r.ok || !r.data?.success) {
        toast(r.data?.error || 'خطا در ساخت گفت‌وگو', 'error');
        return;
    }
    await loadConversations();
    await openConv(r.data.conversation.id);
}

function openGroupModal() {
    state.groupMembers = [];
    $('#groupName').value = '';
    $('#groupChips').innerHTML = '';
    const gr = $('#groupSearchResults');
    gr.innerHTML = '';
    gr.classList.remove('open');
    $('#groupMemberSearch').value = '';
    openModal('#modalGroup');
    setTimeout(() => $('#groupName').focus(), 120);
}
$('#btnNewGroup').addEventListener('click', openGroupModal);
$('#btnNewGroupEmpty').addEventListener('click', openGroupModal);

function renderChips(containerSel, arr, removeFn) {
    const box = $(containerSel);
    box.innerHTML = arr.map((u) => `
        <span class="ms-chip">${esc(u.username)}
        <button title="حذف" data-id="${u.id}">✕</button></span>`).join('');
    $$('button', box).forEach((b) => b.addEventListener('click', () => removeFn(+b.dataset.id)));
}
function removeGroupChip(id) {
    state.groupMembers = state.groupMembers.filter((x) => x.id !== id);
    renderChips('#groupChips', state.groupMembers, removeGroupChip);
}
function removeAddChip(id) {
    state.addMembers = state.addMembers.filter((x) => x.id !== id);
    renderChips('#addChips', state.addMembers, removeAddChip);
}
let gSearchTimer = null;
$('#groupMemberSearch').addEventListener('input', (e) => {
    clearTimeout(gSearchTimer);
    const q = e.target.value.trim();
    const box = $('#groupSearchResults');
    if (q.length < 2) { box.innerHTML = ''; box.classList.remove('open'); return; }
    gSearchTimer = setTimeout(async () => {
        const r = await api(`/messenger/search/?q=${encodeURIComponent(q)}`);
        const users = r.data?.users || [];
        box.classList.add('open');
        box.innerHTML = users.map((u) => `
            <div class="ms-search-hit" data-uid="${u.id}" data-uname="${esc(u.username)}">
                ${avatarHTML(u.username + u.id, (u.username || '؟').charAt(0), u.online)}
                <div class="meta"><b>${esc(u.username)}</b></div>
                <span class="ms-mini-btn">افزودن</span>
            </div>`).join('') || `<div class="ms-search-hit" style="cursor:default"><small>کاربری پیدا نشد</small></div>`;
        $$('.ms-search-hit[data-uid]', box).forEach((el) =>
            el.addEventListener('click', () => {
                const uid = +el.dataset.uid;
                if (!state.groupMembers.some((x) => x.id === uid))
                    state.groupMembers.push({ id: uid, username: el.dataset.uname });
                renderChips('#groupChips', state.groupMembers, removeGroupChip);
            }));
    }, 350);
});

$('#btnCreateGroup').addEventListener('click', async () => {
    const name = $('#groupName').value.trim();
    if (!name) { toast('نام گروه را بنویس', 'error'); return; }
    if (!state.groupMembers.length) { toast('حداقل یک عضو انتخاب کن', 'error'); return; }
    const btn = $('#btnCreateGroup');
    btn.disabled = true; btn.textContent = 'در حال ساخت…';
    const r = await post('/messenger/create-group/', {
        name,
        participant_ids: state.groupMembers.map((u) => u.id),
    });
    btn.disabled = false; btn.textContent = 'ساخت گروه 🎉';
    if (!r.ok || !r.data?.success) {
        toast(r.data?.error || 'گروه ساخته نشد', 'error');
        return;
    }
    document.querySelector('#modalGroup').classList.remove('open');
    toast('گروه ساخته شد 🎉', 'ok');
    await loadConversations();
    await openConv(r.data.conversation.id);
});

function openConversationInfo() {
    if (!state.active) return;
    if (state.active.is_group) renderGroupInfo();
    else renderUserInfo();
    openModal('#modalInfo');
}
$('#btnInfo').addEventListener('click', (event) => {
    event.stopPropagation();
    openConversationInfo();
});
// On group chats the complete white header is a clear, generously sized
// entry-point to members, invites and administration — not only the tiny info icon.
$('#msChatHead').addEventListener('click', (event) => {
    if (!state.active?.is_group || event.target.closest('button, a')) return;
    openConversationInfo();
});

function renderGroupInfo() {
    const c = state.active;
    $('#infoTitle').textContent = `👥 ${c.username}`;
    const memberFaces = state.participants.slice(0, 6).map((p, i) =>
        `<span class="ms-member-face" title="${esc(p.username)}" style="${avatarStyle(p.username + p.id)};z-index:${10 - i}">${esc((p.username || '؟').charAt(0))}</span>`).join('');
    const extraFaces = state.participants.length > 6
        ? `<span class="ms-member-face more">+${faNum(state.participants.length - 6)}</span>` : '';
    const inviteBlock = c.invite_url ? `
        <section class="ms-group-card invite-card">
            <div class="ms-group-card-title"><span class="ms-card-icon">🔗</span><div><b>دعوت با لینک</b><small>لینک را کپی کن یا مستقیم بفرست</small></div></div>
            <div class="ms-invite-box"><code>${esc(c.invite_url)}</code></div>
            <div class="ms-invite-actions">
                <button class="ms-btn primary" id="btnShareInvite">ارسال لینک ↗</button>
                <button class="ms-btn ghost" id="btnCopyInvite">کپی لینک</button>
            </div>
            ${c.is_owner ? `<a class="ms-text-action" href="#" id="btnRegenInvite">↻ ساخت لینک جدید و غیرفعال‌کردن قبلی</a>` : ''}
        </section>` : '';
    const members = state.participants.map((p) => `
        <div class="ms-member-row">
            ${avatarHTML(p.username + p.id, (p.username || '؟').charAt(0), p.online)}
            <div class="meta"><b><a href="/u/${encodeURIComponent(p.username)}/">${esc(p.username)}</a>
                ${p.is_owner ? '<span class="ms-role">👑 مدیر</span>' : ''}</b>
                <small>${p.online ? '● آنلاین' : 'آخرین وضعیت نامشخص'}</small></div>
            ${c.is_owner && !p.is_owner ? `<button class="ms-row-btn danger" data-kick="${p.id}" data-name="${esc(p.username)}">حذف</button>` : ''}
        </div>`).join('');

    $('#infoBody').innerHTML = `
        <section class="ms-group-hero">
            <div class="ms-avatar group-avatar" style="${avatarStyle(c.username + c.id)}">👥</div>
            <div class="ms-group-identity"><h3>${esc(c.username)}</h3><p>فضایی برای گفت‌وگوی اعضای گروه</p></div>
            <div class="ms-member-stack">${memberFaces}${extraFaces}</div>
            <div class="ms-group-count">${faNum(c.members_count)} عضو</div>
        </section>
        ${inviteBlock}
        ${c.is_owner ? `
        <section class="ms-group-card add-card">
            <div class="ms-group-card-title"><span class="ms-card-icon">➕</span><div><b>افزودن مستقیم عضو</b><small>کاربر را جست‌وجو و انتخاب کن</small></div></div>
            <div class="ms-search-wrap"><svg class="s-ico" width="16" height="16"><use href="#i-search"/></svg><input type="text" id="addMemberSearch" placeholder="نام کاربری…" autocomplete="off"></div>
            <div class="ms-search-results" id="addMemberResults"></div>
            <div class="ms-chips" id="addChips"></div>
            <button class="ms-btn primary" id="btnAddMembers" style="width:100%;margin-top:9px">افزودن اعضای انتخاب‌شده</button>
        </section>` : ''}
        <section class="ms-group-card members-card">
            <div class="ms-group-card-title"><span class="ms-card-icon">👤</span><div><b>اعضای گروه</b><small>${faNum(state.participants.length)} نفر در این گروه هستند</small></div></div>
            <div class="ms-members-list">${members}</div>
        </section>
        <button class="ms-btn danger" id="btnLeaveGroup" style="width:100%;margin-top:12px">🚶 ترک گروه</button>`;

    $('#btnShareInvite')?.addEventListener('click', async () => {
        const shareData = { title: `دعوت به گروه ${c.username}`, text: `به گروه «${c.username}» در لرن‌کوئست بپیوند!`, url: c.invite_url };
        try {
            if (navigator.share) await navigator.share(shareData);
            else {
                await navigator.clipboard.writeText(c.invite_url);
                toast('لینک دعوت کپی شد؛ حالا آن را هرجا خواستی بفرست 🔗', 'ok');
            }
        } catch (err) {
            if (err.name !== 'AbortError') toast('ارسال لینک انجام نشد', 'error');
        }
    });
    $('#btnCopyInvite')?.addEventListener('click', async (e) => {
        try {
            await navigator.clipboard.writeText(c.invite_url);
        } catch (err) {
            const tmp = document.createElement('textarea');
            tmp.value = c.invite_url; document.body.appendChild(tmp);
            tmp.select(); document.execCommand('copy'); tmp.remove();
        }
        e.target.textContent = '✓ کپی شد';
        e.target.classList.add('copied');
        setTimeout(() => { e.target.textContent = 'کپی'; e.target.classList.remove('copied'); }, 1800);
        toast('لینک دعوت کپی شد 🔗', 'ok');
    });
    $('#btnRegenInvite')?.addEventListener('click', async (e) => {
        e.preventDefault();
        const r = await post(`/messenger/group/${c.id}/regenerate-invite/`);
        if (r.ok && r.data?.success) {
            c.invite_url = r.data.invite_url;
            renderGroupInfo();
            toast('لینک جدید ساخته شد ✔ (لینک قبلی از کار افتاد)', 'ok');
        } else toast(r.data?.error || 'خطا', 'error');
    });
    $$('#infoBody [data-kick]').forEach((b) => b.addEventListener('click', () => {
        confirmDialog('حذف عضو', `«${b.dataset.name}» از گروه حذف شود؟`, async () => {
            const r = await post(`/messenger/group/${c.id}/remove-member/${b.dataset.kick}/`);
            if (r.ok && r.data?.success) {
                state.participants = state.participants.filter((p) => p.id !== +b.dataset.kick);
                c.members_count = r.data.members_count;
                renderHead(); renderGroupInfo(); reloadMessages();
                toast('عضو حذف شد', 'ok');
            } else toast(r.data?.error || 'خطا', 'error');
        });
    }));
    $('#btnLeaveGroup').addEventListener('click', () => {
        confirmDialog('ترک گروه', `گروه «${c.username}» را ترک می‌کنی؟`, async () => {
            const r = await post(`/messenger/group/${c.id}/leave/`);
            if (r.ok && r.data?.success) {
                document.querySelector('#modalInfo').classList.remove('open');
                toast('گروه را ترک کردی 👋');
                disconnectWS();
                state.activeId = null; state.active = null;
                $('#msApp').classList.remove('chat-open');
                $('#msChatEmpty').style.display = 'grid';
                $('#msChatHead').style.display = 'none';
                $('#msMessages').style.display = 'none';
                $('#msComposer').style.display = 'none';
                history.replaceState(null, '', '/messenger/');
                loadConversations();
            } else toast(r.data?.error || 'خطا', 'error');
        });
    });
    if (c.is_owner) wireAddMember(c);
}

function wireAddMember(c) {
    state.addMembers = [];
    const inp = $('#addMemberSearch');
    const box = $('#addMemberResults');
    let t = null;
    inp.addEventListener('input', () => {
        clearTimeout(t);
        const q = inp.value.trim();
        if (q.length < 2) { box.innerHTML = ''; box.classList.remove('open'); return; }
        t = setTimeout(async () => {
            const r = await api(`/messenger/search/?q=${encodeURIComponent(q)}`);
            const users = (r.data?.users || []).filter(
                (u) => !state.participants.some((p) => p.id === u.id));
            box.classList.add('open');
            box.innerHTML = users.map((u) => `
                <div class="ms-search-hit" data-uid="${u.id}" data-uname="${esc(u.username)}">
                    ${avatarHTML(u.username + u.id, (u.username || '؟').charAt(0), u.online)}
                    <div class="meta"><b>${esc(u.username)}</b></div>
                    <span class="ms-mini-btn">انتخاب</span>
                </div>`).join('') || `<div class="ms-search-hit" style="cursor:default"><small>موردی نیست</small></div>`;
            $$('.ms-search-hit[data-uid]', box).forEach((el) =>
                el.addEventListener('click', () => {
                    const uid = +el.dataset.uid;
                    if (!state.addMembers.some((x) => x.id === uid)) {
                        state.addMembers.push({ id: uid, username: el.dataset.uname });
                        renderChips('#addChips', state.addMembers, removeAddChip);
                        inp.value = ''; box.innerHTML = ''; box.classList.remove('open');
                        toast(`«${el.dataset.uname}» برای افزودن انتخاب شد`, 'ok');
                    }
                }));
        }, 350);
    });
    $('#btnAddMembers').addEventListener('click', async () => {
        if (!state.addMembers.length) { toast('ابتدا یک کاربر را از نتایج جست‌وجو انتخاب کن', 'error'); return; }
        const btn = $('#btnAddMembers');
        btn.disabled = true; btn.textContent = 'در حال افزودن…';
        const r = await post(`/messenger/group/${c.id}/add-members/`, {
            participant_ids: state.addMembers.map((u) => u.id),
        });
        btn.disabled = false; btn.textContent = 'افزودن اعضای انتخاب‌شده';
        if (r.ok && r.data?.success) {
            const added = r.data.added || [];
            if (!added.length) { toast('کاربران انتخاب‌شده از قبل عضو گروه هستند', 'error'); return; }
            toast(`${added.join('، ')} به گروه اضافه شدند ➕`, 'ok');
            state.addMembers = [];
            await reloadMessages();
            c.members_count = r.data.members_count; renderHead(); renderGroupInfo();
        } else toast(r.data?.error || 'افزودن عضو انجام نشد', 'error');
    });
}

function renderUserInfo() {
    const c = state.active;
    const initial = esc((c.username || '؟').charAt(0));
    const stateText = c.online ? 'اکنون آنلاین است' : 'در حال حاضر آفلاین است';
    $('#infoTitle').textContent = 'پروفایل گفتگو';
    $('#infoBody').innerHTML = `
        <section class="ms-profile-card">
            <div class="ms-profile-glow"></div>
            <div class="ms-profile-avatar" style="${avatarStyle(c.username + c.id)}">${initial}<span class="ms-profile-status ${c.online ? 'online' : ''}"></span></div>
            <div class="ms-profile-name">${esc(c.username)}</div>
            <div class="ms-profile-handle">@${esc(c.username)}</div>
            <div class="ms-profile-presence ${c.online ? 'online' : ''}"><i></i>${stateText}</div>
            <div class="ms-profile-divider"></div>
            <div class="ms-profile-note">برای دیدن دستاوردها، سطح و اطلاعات بیشتر، صفحهٔ پروفایل کاربر را باز کن.</div>
        </section>
        <div class="ms-profile-actions">
            <a class="ms-profile-primary" href="/u/${encodeURIComponent(c.username)}/">مشاهدهٔ پروفایل <span>←</span></a>
            <button class="ms-profile-danger ${c.blocked_by_me ? 'undo' : ''}" id="btnBlockToggle">
                ${c.blocked_by_me ? '✓ رفع بلاک کاربر' : '⛔ بلاک کردن کاربر'}</button>
        </div>`;
    $('#btnBlockToggle').addEventListener('click', () => toggleBlock(c));
}

async function toggleBlock(c) {
    const doBlock = !c.blocked_by_me;
    const run = async () => {
        const r = await post(`/messenger/${doBlock ? 'block' : 'unblock'}/${c.user_id}/`);
        if (r.ok && r.data?.success) {
            c.blocked_by_me = doBlock;
            c.blocked_between = doBlock;
            toast(doBlock ? `«${c.username}» بلاک شد ⛔` : `«${c.username}» رفع بلاک شد ✔`, 'ok');
            renderComposer(); renderUserInfo();
            loadConversations();
        } else toast(r.data?.error || 'خطا', 'error');
    };
    if (doBlock) {
        confirmDialog('بلاک کاربر',
            `«${c.username}» بلاک شود؟ دیگر نمی‌توانید در چت دونفره به هم پیام بدهید.`, run);
    } else run();
}

async function reloadMessages() {
    if (!state.activeId) return;
    const r = await api(`/messenger/messages/${state.activeId}/`);
    if (r.ok && r.data?.success) {
        state.active = r.data.conversation;
        state.participants = r.data.participants || [];
        renderMessages(r.data.messages);
        if ($('#modalInfo').classList.contains('open') && state.active?.is_group) renderGroupInfo();
    }
}

$('#btnBlocked').addEventListener('click', async () => {
    openModal('#modalBlocked');
    const body = $('#blockedBody');
    body.innerHTML = '<div class="ms-loading"><div class="big">⏳</div>در حال بارگذاری…</div>';
    const r = await api('/messenger/blocked/');
    const rows = r.data?.blocked_users || [];
    body.innerHTML = rows.length ? rows.map((u) => `
        <div class="ms-list-row">
            ${avatarHTML(u.username + u.id, (u.username || '؟').charAt(0))}
            <div class="meta"><b><a href="/u/${encodeURIComponent(u.username)}/">${esc(u.username)}</a></b>
            <small>از ${faNum(u.since)}</small></div>
            <button class="ms-row-btn ok" data-unblock="${u.id}">رفع بلاک</button>
        </div>`).join('')
        : `<div class="ms-convs-empty"><div class="big">🕊️</div>هیچ کاربری را بلاک نکردی.</div>`;
    $$('#blockedBody [data-unblock]').forEach((b) => b.addEventListener('click', async () => {
        const rr = await post(`/messenger/unblock/${b.dataset.unblock}/`);
        if (rr.ok && rr.data?.success) {
            toast('رفع بلاک شد ✔', 'ok');
            b.closest('.ms-list-row').remove();
            if (!$$('#blockedBody .ms-list-row').length)
                $('#blockedBody').innerHTML = `<div class="ms-convs-empty"><div class="big">🕊️</div>هیچ کاربری را بلاک نکردی.</div>`;
            if (state.active) { state.active.blocked_by_me = false; state.active.blocked_between = false; renderComposer(); }
            loadConversations();
        } else toast('خطا', 'error');
    }));
});

$('#btnBack').addEventListener('click', () => {
    state.activeId = null; state.active = null;
    disconnectWS();
    $('#msApp').classList.remove('chat-open');
    history.replaceState(null, '', '/messenger/');
    renderConvList();
});

setInterval(() => {
    if (document.visibilityState === 'visible') loadConversations();
}, 15000);
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') loadConversations();
});

(async function init() {
    $('#msMyAvatar').setAttribute('style', avatarStyle(state.meName));
    $('#msMyAvatar').textContent = (state.meName || '؟').charAt(0);

    await loadConversations();

    const url = new URL(location.href);
    const c = url.searchParams.get('c');
    const u = url.searchParams.get('u');
    if (c && state.convs.some((x) => x.id === +c)) openConv(+c);
    else if (c) { toast('به این گفت‌وگو دسترسی نداری', 'error'); }
    else if (u) openDM(+u);
})();
})();
