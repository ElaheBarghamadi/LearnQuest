/* Shared helpers for every LearnQuest game page: fa-digits, CSRF, score saving
   with a unified "+XP / new record" feedback line. */
(function () {
    function cookie(name) {
        var m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
        return m ? m.pop() : '';
    }

    function fa(n) {
        return String(n).replace(/[0-9]/g, function (d) { return '۰۱۲۳۴۵۶۷۸۹'[d]; });
    }

    function csrf() {
        var meta = document.querySelector('meta[name="csrf-token"]');
        if (meta && meta.content) return meta.content;
        var hidden = document.getElementById('lqCsrf');
        if (hidden && hidden.value) return hidden.value;
        return cookie('csrftoken');
    }

    /* Build the standard result message from any save-score response. */
    function resultMessage(d, opts) {
        if (!d || d.status !== 'success') return 'نتوانستیم نتیجه را ثبت کنیم';
        var parts = [];
        if (d.xp_gained > 0) parts.push('⭐ +' + fa(d.xp_gained) + ' XP');
        else if (opts && opts.noXp) parts.push(opts.noXp);
        if (d.points_gained > 0) parts.push('+' + fa(d.points_gained) + ' امتیاز 🎯');
        if (d.new_best) parts.push('رکورد جدید 🏆');
        if (d.achievements && d.achievements.length) parts.push('دستاورد: ' + d.achievements[0] + ' 🏅');
        if (d.achievements_earned && d.achievements_earned.length) parts.push('دستاورد: ' + d.achievements_earned[0] + ' 🏅');
        return parts.length ? parts.join(' • ') : 'ثبت شد';
    }

    /**
     * POST a score; paint the unified message into `lineEl` (element or id);
     * resolves with the parsed JSON so games can add their own logic.
     */
    function saveScore(url, payload, lineEl, opts) {
        if (typeof lineEl === 'string') lineEl = document.getElementById(lineEl);
        if (lineEl) { lineEl.textContent = 'در حال ثبت نتیجه…'; lineEl.classList.remove('ok'); }
        return fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf() },
            body: JSON.stringify(payload)
        }).then(function (r) { return r.json().catch(function () { return {}; }); })
          .then(function (d) {
              if (lineEl) {
                  lineEl.textContent = resultMessage(d, opts);
                  lineEl.classList.add('ok');
              }
              return d;
          })
          .catch(function () {
              if (lineEl) lineEl.textContent = 'خطا در اتصال — دوباره تلاش کن';
              return {};
          });
    }

    window.GP = { fa: fa, csrf: csrf, saveScore: saveScore, resultMessage: resultMessage };
})();
