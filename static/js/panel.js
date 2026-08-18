(function () {
    'use strict';

    const $ = (s, r) => (r || document).querySelector(s);
    const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
    const FA = '۰۱۲۳۴۵۶۷۸۹';
    const faNum = (v) => String(v).replace(/\d/g, (d) => FA[+d]);

    function toast(msg, type) {
        if (window.LQ && window.LQ.toast) {
            window.LQ.toast(msg, type || 'info');
        } else {
            alert(msg);
        }
    }

    async function post(url, body) {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body || {}),
        });
        let data = null;
        try { data = await res.json(); } catch (e) { }
        return { ok: res.ok, status: res.status, data };
    }

    function uuid() {
        if (window.crypto && crypto.randomUUID) return crypto.randomUUID();
        return 'xxxxxxxxxxxx4xxx'.replace(/x/g, () =>
            Math.floor(Math.random() * 16).toString(16)) + Date.now().toString(16);
    }

    function pnConfirm(text) {
        return new Promise((resolve) => {
            const back = document.createElement('div');
            back.className = 'pn-confirm-back';
            back.innerHTML =
                '<div class="pn-confirm" role="dialog" aria-modal="true">' +
                '<p></p>' +
                '<div class="row">' +
                '<button type="button" class="pn-btn ghost" data-no>انصراف</button>' +
                '<button type="button" class="pn-btn danger" data-yes>بله، مطمئنم</button>' +
                '</div></div>';
            back.querySelector('p').textContent = text;
            document.body.appendChild(back);
            const done = (val) => { back.remove(); resolve(val); };
            back.addEventListener('click', (e) => { if (e.target === back) done(false); });
            back.querySelector('[data-no]').addEventListener('click', () => done(false));
            back.querySelector('[data-yes]').addEventListener('click', () => done(true));
        });
    }

    function respond(res, okMsg) {
        const d = res.data || {};
        if (d.ok && d.duplicate) {
            toast(d.error || 'این درخواست تکراری بود؛ دوباره اعمال نشد', 'warning');
            return true;
        }
        if (d.ok) {
            toast(okMsg || 'اعمال شد ✅', 'success');
            return true;
        }
        if (d.error === 'insufficient') {
            toast('موجودی کافی نیست — کاربر فقط ' + faNum(d.have || 0) + ' دارد', 'error');
            return false;
        }
        toast(d.error || 'اعمال نشد', 'error');
        return false;
    }

    function wireSuggest(inp, hidden, box) {
        let timer = null;
        inp.addEventListener('input', () => {
            hidden.value = '';
            clearTimeout(timer);
            const q = inp.value.trim();
            if (q.length < 2) { box.classList.remove('open'); box.innerHTML = ''; return; }
            timer = setTimeout(async () => {
                try {
                    const res = await fetch('/messenger/search/?q=' + encodeURIComponent(q));
                    const d = await res.json();
                    const users = (d && d.users) || [];
                    box.classList.add('open');
                    box.innerHTML = users.map((u) =>
                        '<div class="sg" data-id="' + u.id + '" data-name="' + u.username.replace(/"/g, '') + '">' +
                        '<span class="pn-ava">' + (u.username || '؟').charAt(0).toUpperCase() + '</span>' +
                        '<b>' + u.username + '</b>' +
                        (u.online ? '<small>🟢</small>' : '') +
                        '</div>').join('') || '<div class="sg"><small>کاربری پیدا نشد</small></div>';
                    $$('.sg[data-id]', box).forEach((el) => el.addEventListener('click', () => {
                        inp.value = el.dataset.name;
                        hidden.value = el.dataset.id;
                        box.classList.remove('open');
                    }));
                } catch (e) { }
            }, 300);
        });
        document.addEventListener('click', (e) => {
            if (!box.contains(e.target) && e.target !== inp) box.classList.remove('open');
        });
    }

    const qgForm = $('#quickGrantForm');
    if (qgForm) {
        const inp = $('#qgUser');
        const hidden = $('#qgUserId');
        const box = $('#qgSuggest');
        wireSuggest(inp, hidden, box);
        qgForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (!hidden.value) { toast('اول کاربر را از پیشنهادها انتخاب کن', 'error'); return; }
            const amount = parseInt($('#qgAmount').value, 10);
            if (!amount) { toast('مقدار معتبر نیست', 'error'); return; }
            const btn = $('#qgSubmit');
            btn.disabled = true;
            const res = await post('/panel/users/' + hidden.value + '/grant/', {
                target: $('#qgTarget').value,
                amount: amount,
                note: $('#qgNote').value.trim(),
                idem: uuid(),
            });
            btn.disabled = false;
            if (respond(res, 'برای ' + inp.value + ' اعمال شد 🎁')) {
                if (res.data && res.data.ok && !res.data.duplicate) $('#qgNote').value = '';
            }
        });
    }

    const grantForm = $('#grantForm');
    if (grantForm) {
        $$('.pn-chips-amt button').forEach((b) => b.addEventListener('click', () => {
            $('#gAmount').value = b.dataset.amt;
        }));
        grantForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const amount = parseInt($('#gAmount').value, 10);
            if (!amount) { toast('مقدار معتبر نیست', 'error'); return; }
            const kind = $('#gTarget').value;
            const btn = $('#gSubmit');
            btn.disabled = true;
            const res = await post(grantForm.dataset.url, {
                target: kind,
                amount: amount,
                note: $('#gNote').value.trim(),
                idem: uuid(),
            });
            btn.disabled = false;
            if (respond(res)) {
                const d = res.data || {};
                if (d.ok && !d.duplicate) {
                    if (d.coins !== undefined) $('#statCoins').textContent = faNum(d.coins);
                    if (d.gems !== undefined) $('#statGems').textContent = faNum(d.gems);
                    if (d.xp !== undefined) $('#statXp').textContent = faNum(d.xp);
                    if (d.level !== undefined && d.xp !== undefined) {
                        $('#statXp').parentElement.innerHTML =
                            '<span id="statXp">' + faNum(d.xp) + '</span> · ل' + faNum(d.level);
                    }
                    if (d.value !== undefined) {
                        const map = { points: '#statPoints', streak: '#statStreak' };
                        if (map[d.target]) $(map[d.target]).textContent = faNum(d.value);
                    }
                }
            }
        });
    }

    const itemForm = $('#itemForm');
    if (itemForm) {
        itemForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = $('#iSubmit');
            btn.disabled = true;
            const sel = $('#iProduct');
            const res = await post(itemForm.dataset.url, {
                product_id: parseInt(sel.value, 10),
                note: $('#iNote').value.trim(),
                idem: uuid(),
            });
            btn.disabled = false;
            respond(res, '«' + sel.options[sel.selectedIndex].text.split('—')[0].trim() + '» اهدا شد 🎒');
        });
    }

    const toggleBtn = $('#btnToggleActive');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', async () => {
            const active = toggleBtn.dataset.active === '1';
            const yes = await pnConfirm(active
                ? 'حساب این کاربر تعلیق شود؟ دیگر نمی‌تواند وارد شود.'
                : 'حساب این کاربر دوباره فعال شود؟');
            if (!yes) return;
            toggleBtn.disabled = true;
            const res = await post('/panel/users/' + toggleBtn.dataset.userId + '/toggle-active/', {
                is_active: !active,
                idem: uuid(),
            });
            toggleBtn.disabled = false;
            const d = res.data || {};
            if (d.ok) {
                const nowActive = !!d.is_active;
                toggleBtn.dataset.active = nowActive ? '1' : '0';
                toggleBtn.className = 'pn-btn ' + (nowActive ? 'danger' : 'ok');
                toggleBtn.textContent = nowActive ? '⛔ تعلیق حساب' : '✅ فعال‌سازی حساب';
                const badge = $('#udActiveBadge');
                badge.className = 'pn-badge ' + (nowActive ? 'on' : 'off');
                badge.textContent = nowActive ? 'فعال' : 'تعلیق';
                toast(nowActive ? 'حساب فعال شد ✅' : 'حساب تعلیق شد ⛔', nowActive ? 'success' : 'warning');
            } else {
                toast(d.error || 'اعمال نشد', 'error');
            }
        });
    }
})();
