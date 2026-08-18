(function () {
    'use strict';

    const LQ = window.LQ = window.LQ || {};

    const ICONS = {
        success: '✅', error: '⛔', warning: '⚠️', info: '🔔', reward: '🎁', message: '💬'
    };

    function esc(v) {
        return String(v == null ? '' : v)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }
    LQ.esc = esc;

    function csrf() {
        const m = document.cookie.match(/(^|;\s*)csrftoken\s*=\s*([^;]+)/);
        return m ? decodeURIComponent(m[2]) : '';
    }
    LQ.csrf = csrf;

    let stack = null;

    function getStack() {
        if (!stack || !document.body.contains(stack)) {
            stack = document.createElement('div');
            stack.className = 'lq-toast-stack';
            stack.setAttribute('aria-live', 'polite');
            document.body.appendChild(stack);
        }
        return stack;
    }

    const recent = new Map();

    function tooSoon(key) {
        const now = Date.now();
        if (recent.has(key) && now - recent.get(key) < 2500) return true;
        recent.set(key, now);
        return false;
    }

    function dismiss(el) {
        if (!el || el.classList.contains('hide')) return;
        el.classList.add('hide');
        setTimeout(() => el.remove(), 340);
    }

    function mountToast(el, duration) {
        const box = getStack();
        box.appendChild(el);
        while (box.children.length > 5) dismiss(box.firstChild);
        const x = el.querySelector('.lq-t-x');
        if (x) x.addEventListener('click', (ev) => { ev.stopPropagation(); dismiss(el); });
        if (duration > 0) {
            const prog = document.createElement('span');
            prog.className = 'lq-t-prog';
            prog.style.animationDuration = duration + 'ms';
            el.appendChild(prog);
            const timer = setTimeout(() => dismiss(el), duration);
            el.addEventListener('mouseenter', () => {
                clearTimeout(timer);
                prog.style.animationPlayState = 'paused';
            });
            el.addEventListener('mouseleave', () => {
                prog.style.animationPlayState = 'running';
                setTimeout(() => dismiss(el), 1600);
            });
        }
    }

    LQ.toast = function (text, type, opts) {
        opts = opts || {};
        type = type || 'info';
        const duration = opts.duration || 4200;
        const key = type + '|' + text;
        if (tooSoon(key)) return;
        const el = document.createElement('div');
        el.className = 'lq-toast t-' + type;
        el.innerHTML =
            '<div class="lq-t-ico">' + (opts.icon || ICONS[type] || ICONS.info) + '</div>' +
            '<div class="lq-t-body">' +
            (opts.title ? '<div class="lq-t-title">' + esc(opts.title) + '</div>' : '') +
            '<div class="lq-t-text">' + esc(text) + '</div>' +
            '</div>' +
            '<button type="button" class="lq-t-x" aria-label="بستن">✕</button>';
        mountToast(el, duration);
        return el;
    };

    LQ.notify = function (d) {
        if (!d || typeof d !== 'object') return;
        if (window.LQ_ACTIVE_CHAT_ID && d.conversation_id === window.LQ_ACTIVE_CHAT_ID) return;

        const name = d.is_group && d.group_name ? d.group_name : d.sender_username;
        const title = d.is_group
            ? ('پیام جدید در «' + name + '»')
            : ('پیام جدید از ' + name);
        const ava = d.sender_avatar
            ? '<img src="' + esc(d.sender_avatar) + '" alt="">'
            : esc((d.sender_username || '؟').charAt(0).toUpperCase());

        const el = document.createElement('div');
        el.className = 'lq-toast lq-msg t-message';
        el.innerHTML =
            '<div class="lq-msg-ava">' + ava + '</div>' +
            '<div class="lq-t-body">' +
            '<div class="lq-t-title">' + esc(title) + '</div>' +
            '<div class="lq-t-excerpt">' + esc(d.excerpt || '') + '</div>' +
            '<div class="lq-t-meta"><span>' + esc(d.time || '') + '</span>' +
            (d.conversation_url ? '<a class="lq-t-chat" href="' + esc(d.conversation_url) + '">💬 گفت‌وگو</a>' : '') +
            '</div></div>' +
            '<button type="button" class="lq-t-x" aria-label="بستن">✕</button>';

        el.addEventListener('click', (ev) => {
            if (ev.target.closest('.lq-t-x') || ev.target.closest('.lq-t-chat')) return;
            dismiss(el);
            if (d.sender_username) LQ.openProfile(d.sender_username);
        });
        const chatLink = el.querySelector('.lq-t-chat');
        if (chatLink) chatLink.addEventListener('click', (ev) => ev.stopPropagation());
        mountToast(el, 6000);
    };

    let modalOverlay = null;
    let lastFocus = null;

    function ensureModal() {
        if (modalOverlay && document.body.contains(modalOverlay)) return modalOverlay;
        modalOverlay = document.createElement('div');
        modalOverlay.className = 'lq-pmodal-overlay';
        modalOverlay.id = 'lqPmodal';
        modalOverlay.innerHTML =
            '<div class="lq-pmodal" role="dialog" aria-modal="true">' +
            '<button type="button" class="lq-pmodal-x" aria-label="بستن">✕</button>' +
            '<div class="lq-pmodal-inner"></div>' +
            '</div>';
        document.body.appendChild(modalOverlay);
        modalOverlay.addEventListener('click', (ev) => {
            if (ev.target === modalOverlay) LQ.closeProfile();
        });
        modalOverlay.querySelector('.lq-pmodal-x').addEventListener('click', LQ.closeProfile);
        document.addEventListener('keydown', (ev) => {
            if (ev.key === 'Escape' && modalOverlay.classList.contains('open')) LQ.closeProfile();
        });
        return modalOverlay;
    }

    function skeletonHTML() {
        return '' +
            '<div class="lq-pmodal-hero"><div class="lq-skel" style="width:96px;height:96px;border-radius:50%;margin:0 auto"></div></div>' +
            '<div class="lq-pmodal-body"><div class="lq-pmodal-card">' +
            '<div class="lq-skel" style="height:22px;width:55%;margin:0 auto"></div>' +
            '<div class="lq-skel" style="height:12px;width:75%;margin:10px auto 0"></div>' +
            '<div class="lq-pmodal-stats">' +
            '<div class="lq-skel" style="height:44px"></div><div class="lq-skel" style="height:44px"></div>' +
            '<div class="lq-skel" style="height:44px"></div><div class="lq-skel" style="height:44px"></div>' +
            '</div>' +
            '<div class="lq-skel" style="height:10px;margin-top:14px"></div>' +
            '</div></div>';
    }

    function errorHTML(msg, username) {
        return '<div class="lq-pmodal-err"><div style="font-size:2rem;margin-bottom:8px">🙈</div>' +
            esc(msg || 'پروفایل پیدا نشد') +
            (username
                ? '<div style="margin-top:14px"><button type="button" class="lq-pmodal-btn ghost" style="flex:0;padding:9px 26px" onclick="window.LQ.openProfile(\'' + esc(username) + '\')">تلاش دوباره</button></div>'
                : '') +
            '</div>';
    }

    function profileHTML(p) {
        const frameCls = p.frame_css ? ' lq-framed ' + p.frame_css : '';
        const effectCls = p.profile_effect_css ? ' ' + p.profile_effect_css : '';
        const nameCls = p.username_color_css ? ' class="' + esc(p.username_color_css) + '"' : '';
        const avaInner = p.avatar_url
            ? '<img src="' + esc(p.avatar_url) + '" alt="' + esc(p.username) + '">'
            : esc(p.initial || '👤');
        const onlineTxt = p.online
            ? '<span class="lq-st-on">🟢 آنلاین</span>'
            : '<span>آفلاین</span>';
        const titleChip = p.title_label
            ? '<span class="lq-pmodal-pet" style="background:#eef0ff;color:#4f46e5;margin-top:0">🎖 ' + esc(p.title_label) + '</span>'
            : '';
        let badges = '';
        if (p.badges && p.badges.length) {
            badges = '<div class="lq-pmodal-badges">' + p.badges.map((b) =>
                '<span class="' + esc(b.css_class || '') + '">' + esc(b.label) + '</span>').join('') + '</div>';
        }
        const pet = p.pet
            ? '<div><span class="lq-pmodal-pet">' + esc(p.pet.emoji) + ' پت: <b>' + esc(p.pet.name) + '</b> · سطح ' + esc(p.pet.level) + '</span></div>'
            : '';

        let actions = '';
        if (p.is_self) {
            actions = '<div class="lq-pmodal-actions"><a class="lq-pmodal-btn primary" href="/home/profile/">👤 پروفایل من</a></div>';
        } else if (p.blocked_between && !p.blocked_by_me) {
            actions = '<div class="lq-pmodal-note">⛔ امکان گفت‌وگو با این کاربر وجود ندارد</div>';
        } else {
            actions =
                '<div class="lq-pmodal-actions">' +
                (p.can_message ? '<a class="lq-pmodal-btn primary" href="' + esc(p.message_url) + '">💬 ارسال پیام</a>' : '') +
                '<button type="button" class="lq-pmodal-btn ' + (p.blocked_by_me ? 'ghost' : 'danger') + '" data-lq-block="' + esc(p.username) + '" data-lq-blocked="' + (p.blocked_by_me ? '1' : '0') + '">' +
                (p.blocked_by_me ? '✔ رفع بلاک' : '⛔ بلاک') + '</button>' +
                '</div>';
        }
        const blockedNote = p.blocked_by_me
            ? '<div class="lq-pmodal-note" style="background:#fef3c7;color:#92400e;margin-top:10px">⛔ این کاربر را بلاک کرده‌ای</div>'
            : '';

        return '' +
            '<div class="lq-pmodal-hero">' +
            '<div class="lq-pmodal-ava' + frameCls + effectCls + '">' + avaInner +
            '<span class="lq-on-dot' + (p.online ? ' on' : '') + '"></span>' +
            '</div></div>' +
            '<div class="lq-pmodal-body"><div class="lq-pmodal-card">' +
            '<div class="lq-pmodal-name"><span' + nameCls + '>' + esc(p.display_name) + '</span>' + titleChip + '</div>' +
            '<div class="lq-pmodal-sub"><span dir="ltr">@' + esc(p.username) + '</span> · ' + onlineTxt + '</div>' +
            badges + pet +
            '<div class="lq-pmodal-stats">' +
            '<div class="lq-pmodal-stat"><div class="v" style="color:#d97706">🏅 ' + esc(p.global_rank) + '</div><div class="k">رتبهٔ جهانی</div></div>' +
            '<div class="lq-pmodal-stat"><div class="v" style="color:#0ea5a4">⚡ ' + esc(p.level) + '</div><div class="k">سطح</div></div>' +
            '<div class="lq-pmodal-stat"><div class="v" style="color:#8b5cf6">⭐ ' + esc(p.xp) + '</div><div class="k">XP</div></div>' +
            '<div class="lq-pmodal-stat"><div class="v" style="color:#ef4444">🔥 ' + esc(p.streak || 0) + '</div><div class="k">روز متوالی</div></div>' +
            '</div>' +
            '<div class="lq-pmodal-level"><div class="lbl"><span>پیشرفت سطح ' + esc(p.level) + '</span><span>' + Math.round(p.level_progress || 0) + '٪</span></div>' +
            '<div class="bar"><div class="fill" data-w="' + Math.max(0, Math.min(100, p.level_progress || 0)) + '"></div></div></div>' +
            (p.joined_jalali ? '<div class="lq-pmodal-join">📅 عضو از ' + esc(p.joined_jalali) + '</div>' : '') +
            '</div>' + actions + blockedNote + '</div>';
    }

    function wireModalContent(container, p, username) {
        const fill = container.querySelector('.lq-pmodal-level .fill');
        if (fill) requestAnimationFrame(() => { fill.style.width = fill.dataset.w + '%'; });

        const blockBtn = container.querySelector('[data-lq-block]');
        if (blockBtn) {
            blockBtn.addEventListener('click', async () => {
                const wasBlocked = blockBtn.dataset.lqBlocked === '1';
                const uname = blockBtn.dataset.lqBlock;
                if (!wasBlocked && !window.confirm('این کاربر بلاک شود؟ دیگر نمی‌توانید به هم پیام بدهید.')) return;
                blockBtn.disabled = true;
                try {
                    const r = await fetch('/messenger/' + (wasBlocked ? 'unblock' : 'block') + '/' + encodeURIComponent(p.id) + '/', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf() },
                        body: '{}'
                    });
                    const d = await r.json().catch(() => ({}));
                    if (r.ok && d.success) {
                        LQ.toast(wasBlocked ? 'بلاک برداشته شد ✔' : 'کاربر بلاک شد ⛔', wasBlocked ? 'success' : 'warning');
                        LQ.openProfile(username);
                    } else {
                        LQ.toast(d.error || 'خطا رخ داد', 'error');
                        blockBtn.disabled = false;
                    }
                } catch (e) {
                    LQ.toast('خطا در ارتباط با سرور', 'error');
                    blockBtn.disabled = false;
                }
            });
        }
    }

    LQ.openProfile = function (username) {
        if (!username) return;
        const overlay = ensureModal();
        const inner = overlay.querySelector('.lq-pmodal-inner');
        lastFocus = document.activeElement;
        overlay.classList.add('open');
        document.body.style.overflow = 'hidden';
        inner.innerHTML = skeletonHTML();

        fetch('/api/profile/' + encodeURIComponent(username) + '/', {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        }).then(async (r) => {
            const d = await r.json().catch(() => ({}));
            if (!r.ok || !d.success || !d.profile) {
                inner.innerHTML = errorHTML((d && d.error) || 'پروفایل پیدا نشد', username);
                return;
            }
            inner.innerHTML = profileHTML(d.profile);
            wireModalContent(inner, d.profile, username);
        }).catch(() => {
            inner.innerHTML = errorHTML('خطا در ارتباط با سرور', username);
        });
    };

    LQ.closeProfile = function () {
        if (!modalOverlay) return;
        modalOverlay.classList.remove('open');
        document.body.style.overflow = '';
        if (lastFocus && lastFocus.focus) {
            try { lastFocus.focus(); } catch (e) {}
        }
    };

    let guideOverlay = null;
    let guideCache = null;
    const GUIDE_URL = '/home/guide/?partial=1';

    function ensureGuideModal() {
        if (guideOverlay && document.body.contains(guideOverlay)) return guideOverlay;
        guideOverlay = document.createElement('div');
        guideOverlay.className = 'lq-gmodal-overlay';
        guideOverlay.innerHTML =
            '<div class="lq-gmodal" role="dialog" aria-modal="true" aria-label="راهنمای سایت">' +
            '<div class="lq-gmodal-head">' +
            '<div class="lq-gmodal-title">🧭 راهنمای لرن‌کوئست</div>' +
            '<button type="button" class="lq-pmodal-x" aria-label="بستن">✕</button>' +
            '</div>' +
            '<div class="lq-gmodal-body"></div>' +
            '</div>';
        document.body.appendChild(guideOverlay);
        guideOverlay.addEventListener('click', (ev) => {
            if (ev.target === guideOverlay) LQ.closeGuide();
        });
        guideOverlay.querySelector('.lq-pmodal-x').addEventListener('click', LQ.closeGuide);
        document.addEventListener('keydown', (ev) => {
            if (ev.key === 'Escape' && guideOverlay.classList.contains('open')) LQ.closeGuide();
        });
        wireGuideBody(guideOverlay.querySelector('.lq-gmodal-body'));
        return guideOverlay;
    }

    function wireGuideBody(body) {
        body.addEventListener('click', (ev) => {
            const a = ev.target.closest && ev.target.closest('a[href^="#"]');
            if (!a) return;
            const id = a.getAttribute('href').slice(1);
            const t = id && body.querySelector('[id="' + CSS.escape(id) + '"]');
            if (!t) return;
            ev.preventDefault();
            t.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    }

    LQ.openGuide = function () {
        const overlay = ensureGuideModal();
        const body = overlay.querySelector('.lq-gmodal-body');
        overlay.classList.add('open');
        document.body.style.overflow = 'hidden';
        if (guideCache) {
            body.innerHTML = guideCache;
            body.scrollTop = 0;
            return;
        }
        body.innerHTML = '<div class="lq-gmodal-loading"><div class="lq-gmodal-spin"></div>در حال بارگذاری راهنما…</div>';
        fetch(GUIDE_URL, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
            .then((r) => {
                if (!r.ok) throw new Error('bad');
                return r.text();
            })
            .then((html) => {
                guideCache = html;
                body.innerHTML = html;
                body.scrollTop = 0;
            })
            .catch(() => {
                body.innerHTML = '<div class="lq-pmodal-err"><div style="font-size:2rem;margin-bottom:8px">🙈</div>' +
                    'راهنما بارگذاری نشد' +
                    '<div style="margin-top:14px"><a class="lq-pmodal-btn ghost" href="/home/guide/">باز کردن صفحهٔ کامل راهنما</a></div></div>';
            });
    };

    LQ.closeGuide = function () {
        if (!guideOverlay) return;
        guideOverlay.classList.remove('open');
        document.body.style.overflow = '';
    };

    function wireGuideLinks() {
        document.addEventListener('click', (ev) => {
            if (ev.defaultPrevented || ev.button !== 0 || ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey) return;
            const a = ev.target.closest && ev.target.closest('a[href]');
            if (!a || a.hasAttribute('data-no-modal')) return;
            const href = a.getAttribute('href') || '';
            if (!/^\/home\/guide\/?(?:[?#].*)?$/.test(href)) return;
            ev.preventDefault();
            LQ.openGuide();
        });
    }

    function interceptLinks() {
        document.addEventListener('click', (ev) => {
            if (!window.LQ_USER || !window.LQ_USER.authed) return;
            if (ev.defaultPrevented || ev.button !== 0 || ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey) return;
            const a = ev.target.closest && ev.target.closest('a[href]');
            if (!a || a.hasAttribute('data-no-modal') || a.hasAttribute('download')) return;
            const href = a.getAttribute('href') || '';
            const m = href.match(/^\/u\/([^/?#]+)\/?(?:[?#].*)?$/);
            if (!m) return;
            let username = m[1];
            try { username = decodeURIComponent(username); } catch (e) {}
            if (window.LQ_USER && window.LQ_USER.username === username) return;
            ev.preventDefault();
            LQ.openProfile(username);
        });
    }

    function ensureCosmetics() {
        const href = '/static/css/cosmetics.css';
        if (!document.querySelector('link[href*="' + href + '"]')) {
            const l = document.createElement('link');
            l.rel = 'stylesheet';
            l.href = href;
            document.head.appendChild(l);
        }
    }

    let ws = null;
    let wsRetries = 0;
    let pingTimer = null;
    const WS_MAX_FAILS = 10;

    function wsUrl() {
        const proto = location.protocol === 'https:' ? 'wss' : 'ws';
        return proto + '://' + location.host + '/ws/notifications/';
    }

    function scheduleReconnect() {
        if (wsRetries >= WS_MAX_FAILS) return;
        const delay = Math.min(30000, 1200 * Math.pow(2, wsRetries));
        wsRetries++;
        setTimeout(connectWS, delay);
    }

    function connectWS() {
        if (!window.LQ_USER || !window.LQ_USER.authed) return;
        if (wsRetries >= WS_MAX_FAILS && ws === null) return;
        if (ws && (ws.readyState === 0 || ws.readyState === 1)) return;
        try { ws = new WebSocket(wsUrl()); } catch (e) { scheduleReconnect(); return; }

        ws.onopen = () => {
            wsRetries = 0;
            clearInterval(pingTimer);
            pingTimer = setInterval(() => {
                if (ws && ws.readyState === 1) ws.send(JSON.stringify({ type: 'ping' }));
            }, 25000);
        };
        ws.onmessage = (ev) => {
            let d;
            try { d = JSON.parse(ev.data); } catch (e) { return; }
            if (d && d.type === 'notify.message') {
                d.conversation_url = '/messenger/?c=' + encodeURIComponent(d.conversation_id || '');
                LQ.notify(d);
            }
        };
        ws.onclose = () => {
            clearInterval(pingTimer);
            ws = null;
            scheduleReconnect();
        };
        ws.onerror = () => { try { ws.close(); } catch (e) {} };
    }

    function flushFlashes() {
        document.querySelectorAll('[data-lq-flash]').forEach((el) => {
            const type = el.getAttribute('data-lq-flash') || 'info';
            const duration = parseInt(el.getAttribute('data-lq-duration') || '0', 10) || undefined;
            const title = el.getAttribute('data-lq-title') || undefined;
            LQ.toast(el.textContent.trim(), type, { duration: duration, title: title });
            el.remove();
        });
    }

    function boot() {
        ensureCosmetics();
        flushFlashes();
        interceptLinks();
        wireGuideLinks();
        connectWS();
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && (!ws || ws.readyState > 1)) connectWS();
        });
    }
    LQ.bootNotify = connectWS;

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }
})();

(function () {
    function hueOf(s) { var h = 0; for (var i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) % 360; return h; }
    function swap(img) {
        if (img.dataset.artDone) return;
        img.dataset.artDone = '1';
        var span = document.createElement('span');
        var inDash = !!img.closest('.db-art-cov');
        span.className = inDash ? 'huecover' : 'bl-art';
        span.style.setProperty('--h', String(hueOf(img.getAttribute('src') || img.alt || 'x')));
        span.innerHTML = inDash ? '<i>\u{1F4D6}</i>' : '<i class="bl-art-emo">\u{1F4D6}</i>';
        img.replaceWith(span);
    }
    function arm() {
        document.querySelectorAll('.bl-thumb img, .bl-fcard img, .rl-thumb img, .db-art-cov img').forEach(function (img) {
            if (img.complete && img.naturalWidth === 0) swap(img);
            else img.addEventListener('error', function () { swap(img); });
        });
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', arm);
    else arm();
})();
