(function () {
    'use strict';

    const $ = (s, r) => (r || document).querySelector(s);
    const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
    const FA = '۰۱۲۳۴۵۶۷۸۹';
    const faNum = (s) => String(s).replace(/\d/g, (d) => FA[+d]);

    function csrf() {
        const m = document.querySelector('meta[name="csrf-token"]');
        if (m && m.content) return m.content;
        const h = document.getElementById('lqCsrf');
        if (h && h.value) return h.value;
        const c = document.cookie.match('(^|;)\s*csrftoken\s*=\s*([^;]+)');
        return c ? c.pop() : '';
    }
    const POST = { method: 'POST', headers: { 'X-CSRFToken': csrf() } };

    function toast(msg, type) {
        if (window.LQ && window.LQ.toast) {
            const mapped = type === 'err' ? 'error' : type === 'ok' ? 'success' : 'info';
            window.LQ.toast(msg, mapped);
            return;
        }
        alert(msg);
    }

    const reveals = $$('.reveal:not(.in)');
    if (reveals.length && 'IntersectionObserver' in window) {
        const io = new IntersectionObserver((entries) => {
            entries.forEach((e) => {
                if (!e.isIntersecting) return;
                const el = e.target;
                const idx = Array.from(el.parentElement.children).indexOf(el);
                el.style.transitionDelay = Math.min(idx * 70, 420) + 'ms';
                el.classList.add('in');
                io.unobserve(el);
            });
        }, { threshold: 0.08, rootMargin: '0px 0px 120px 0px' });
        reveals.forEach((el) => { el.classList.add('armed'); io.observe(el); });
        setTimeout(() => {
            $$('.reveal.armed:not(.in)').forEach((el) => {
                const r = el.getBoundingClientRect();
                if (r.top < window.innerHeight) el.classList.add('in');
            });
        }, 2500);
    } else {
        reveals.forEach((el) => el.classList.add('in'));
    }

    const cfg = $('#blog-config');
    if (!cfg) return; // صفحهٔ لیست — همین‌جا کافی است

    const likeUrl = cfg.dataset.likeUrl;
    const commentLikeTpl = cfg.dataset.commentLikeUrl;
    const isAuthed = cfg.dataset.auth === '1';

    const progress = $('#read-progress');
    if (progress) {
        let ticking = false;
        const update = () => {
            const h = document.documentElement;
            const max = h.scrollHeight - h.clientHeight;
            progress.style.width = (max > 0 ? (h.scrollTop / max) * 100 : 0) + '%';
            ticking = false;
        };
        window.addEventListener('scroll', () => {
            if (!ticking) { window.requestAnimationFrame(update); ticking = true; }
        }, { passive: true });
        update();
    }

    function burst(container) {
        if (!container) return;
        container.innerHTML = '';
        for (let i = 0; i < 8; i++) {
            const p = document.createElement('i');
            const ang = (i / 8) * Math.PI * 2;
            const dist = 26 + Math.random() * 14;
            p.style.setProperty('--dx', Math.cos(ang) * dist + 'px');
            p.style.setProperty('--dy', Math.sin(ang) * dist + 'px');
            p.style.background = i % 2 ? '#FF6584' : '#36D1DC';
            container.appendChild(p);
        }
        setTimeout(() => { container.innerHTML = ''; }, 750);
    }
    function pop(btn) {
        btn.classList.remove('pop'); void btn.offsetWidth; btn.classList.add('pop');
    }

    const likeBtn = $('#article-like-btn');
    if (likeBtn) {
        likeBtn.addEventListener('click', async () => {
            if (!isAuthed) { toast('برای لایک‌کردن اول وارد حسابت شو 😉', 'err'); return; }
            try {
                const res = await fetch(likeUrl, POST);
                const d = await res.json();
                if (!d.success) throw 0;
                likeBtn.classList.toggle('liked', d.liked);
                $('#article-likes-count').textContent = faNum(d.likes);
                const heroCnt = $('#article-likes-hero');
                if (heroCnt) heroCnt.textContent = faNum(d.likes);
                likeBtn.lastElementChild.textContent = d.liked ? 'پسندیدی!' : 'بپسند';
                if (d.liked) { burst($('.burst', likeBtn)); pop(likeBtn); }
            } catch (e) { toast('مشکلی پیش آمد؛ دوباره تلاش کن', 'err'); }
        });
    }

    const copyBtn = $('#copy-link-btn');
    if (copyBtn) {
        copyBtn.addEventListener('click', async () => {
            const url = window.location.href;
            try {
                await navigator.clipboard.writeText(url);
            } catch (e) {
                const inp = document.createElement('input');
                inp.value = url; document.body.appendChild(inp);
                inp.select(); document.execCommand('copy'); inp.remove();
            }
            toast('لینک مقاله کپی شد 🔗', 'ok');
        });
    }

    document.addEventListener('input', (e) => {
        const ta = e.target.closest('.comment-form-ajax textarea');
        if (!ta) return;
        const num = ta.closest('.comment-form-ajax').querySelector('.c-count-num');
        if (num) num.textContent = ta.value.length;
    });

    document.addEventListener('click', (e) => {
        const rb = e.target.closest('.c-reply-btn');
        if (!rb) return;
        const item = rb.closest('.c-item');
        const box = item && item.querySelector(':scope > .c-main .c-inline-form');
        if (box) {
            box.classList.toggle('open');
            if (box.classList.contains('open')) {
                const ta = box.querySelector('textarea');
                if (ta) ta.focus();
            }
        }
    });

    document.addEventListener('click', async (e) => {
        const btn = e.target.closest('.c-like');
        if (!btn) return;
        const url = commentLikeTpl.replace(/\/0\/$/, '/' + btn.dataset.commentId + '/');
        try {
            const res = await fetch(url, POST);
            const d = await res.json();
            if (!d.success) throw 0;
            btn.classList.toggle('liked', d.liked);
            btn.querySelector('.c-like-cnt').textContent = faNum(d.likes);
            if (d.liked) pop(btn);
        } catch (err) { toast('مشکلی پیش آمد؛ دوباره تلاش کن', 'err'); }
    });

    document.addEventListener('submit', async (e) => {
        const form = e.target.closest('.comment-form-ajax');
        if (!form) return;
        e.preventDefault();

        const btn = form.querySelector('.btn-send');
        const errBox = form.querySelector('.c-error');
        if (errBox) { errBox.classList.remove('show'); errBox.textContent = ''; }
        if (btn) btn.disabled = true;

        try {
            const res = await fetch(form.action, { method: 'POST', body: new FormData(form), headers: { 'X-CSRFToken': csrf() } });
            const d = await res.json();
            if (!res.ok || !d.success) {
                const msg = d.error || 'نظر ثبت نشد؛ دوباره تلاش کن.';
                if (errBox) { errBox.textContent = msg; errBox.classList.add('show'); }
                toast(msg, 'err');
                return;
            }

            const list = $('#comments-list');
            const empty = $('#comments-empty');
            if (empty) empty.remove();

            if (d.parent_id) {
                let item = document.querySelector('.c-item[data-comment-id="' + d.parent_id + '"]');
                let replies = item && item.querySelector(':scope > .c-replies');
                if (!replies && item) {
                    replies = document.createElement('div');
                    replies.className = 'c-replies';
                    item.appendChild(replies);
                }
                if (replies) replies.insertAdjacentHTML('beforeend', d.html);
                const inline = form.closest('.c-inline-form');
                if (inline) inline.classList.remove('open');
            } else if (list) {
                list.insertAdjacentHTML('afterbegin', d.html);
            }

            form.reset();
            const cnt = form.querySelector('.c-count-num');
            if (cnt) cnt.textContent = '0';

            ['comments-count', 'comments-count-hero', 'comments-count-btn'].forEach((id) => {
                const el = document.getElementById(id);
                if (el && d.comments_count != null) el.textContent = faNum(d.comments_count);
            });
            toast('نظرت ثبت شد ✅', 'ok');
        } catch (err) {
            toast('خطا در ارتباط با سرور', 'err');
        } finally {
            if (btn) btn.disabled = false;
        }
    });
})();

(function () {
var imgs = [];
document.querySelectorAll('.bl-thumb img, .bl-fcard img, .rl-thumb img').forEach(function (i) { imgs.push(i); });
imgs.forEach(function (img) {
    function swap() {
        if (img.dataset.artDone) return;
        img.dataset.artDone = '1';
        var h = 0, s = img.getAttribute('src') || '';
        for (var i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) % 360;
        var span = document.createElement('span');
        span.className = 'bl-art';
        span.style.setProperty('--h', String(h));
        span.innerHTML = '<i class="bl-art-emo">\u{1F4D6}</i>';
        img.replaceWith(span);
    }
    if (img.complete && img.naturalWidth === 0) swap();
    else img.addEventListener('error', swap);
});
})();
