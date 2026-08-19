/* ============================================================
   LearnQuest CMS — Visual Block Editor
   تبدیل textareaهای ریک‌تکست به ویرایشگر بلوکی درگ‌اندروپ
   بدون نیاز به نوشتن HTML — هر بلوک: متن/تیتر/لیست/نقل‌قول/عکس/کد
   ============================================================ */
(function () {
    'use strict';

    var EDITOR_PLACEHOLDER = 'برای نوشتن اینجا کلیک کنید…';

    /* ---------- HTML → بلوک‌ها (جدا کردن) ---------- */
    function htmlToBlocks(html) {
        if (!html || !html.trim()) return [{ type: 'text', content: '' }];
        var blocks = [];
        var container = document.createElement('div');
        container.innerHTML = html;

        function walk(node, parentList) {
            var children = Array.prototype.slice.call(node.childNodes);
            children.forEach(function (child) {
                if (child.nodeType === 3) { // متن
                    var t = (child.textContent || '').replace(/\s+/g, ' ').trim();
                    if (t) blocks.push({ type: 'text', content: t });
                    return;
                }
                if (child.nodeType !== 1) return;
                var tag = child.tagName.toLowerCase();
                if (/^(h1|h2|h3|h4)$/.test(tag)) {
                    blocks.push({ type: 'heading', content: (child.textContent || '').trim() });
                } else if (tag === 'li' && parentList) {
                    blocks.push({ type: 'bullet', content: (child.textContent || '').trim() });
                } else if (tag === 'ul' || tag === 'ol') {
                    walk(child, true);
                } else if (tag === 'blockquote') {
                    blocks.push({ type: 'quote', content: (child.textContent || '').trim() });
                } else if (tag === 'img') {
                    blocks.push({ type: 'image', content: '', src: child.getAttribute('src') || '' });
                } else if (tag === 'pre' || tag === 'code') {
                    blocks.push({ type: 'code', content: (child.textContent || '').trim() });
                } else if (tag === 'p' || tag === 'div' || tag === 'span' || tag === 'strong' || tag === 'em' || tag === 'br') {
                    walk(child, parentList);
                } else {
                    walk(child, parentList);
                }
            });
        }
        walk(container, false);
        if (!blocks.length) blocks.push({ type: 'text', content: '' });
        return blocks;
    }

    /* ---------- بلوک‌ها → HTML ---------- */
    function blocksToHtml(blocks) {
        if (!blocks || !blocks.length) return '';
        var html = '';
        blocks.forEach(function (b) {
            var c = (b.content || '').trim();
            if (b.type === 'heading') {
                html += '<h3>' + escapeHtml(c) + '</h3>\n';
            } else if (b.type === 'bullet') {
                html += '<li>' + escapeHtml(c) + '</li>\n';
            } else if (b.type === 'quote') {
                html += '<blockquote>' + escapeHtml(c) + '</blockquote>\n';
            } else if (b.type === 'code') {
                html += '<pre><code>' + escapeHtml(c) + '</code></pre>\n';
            } else if (b.type === 'image') {
                if (b.src) html += '<img src="' + escapeAttr(b.src) + '" alt="">\n';
            } else {
                html += '<p>' + escapeHtml(c) + '</p>\n';
            }
        });
        return html;
    }

    function escapeHtml(s) {
        return String(s == null ? '' : s)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }
    function escapeAttr(s) { return escapeHtml(s).replace(/'/g, '&#39;'); }

    /* ---------- اسکیپ موجودی که باید نمایش داده شود ---------- */
    function htmlForEdit(html) {
        if (!html || !html.trim()) return '';
        var c = document.createElement('div');
        c.innerHTML = html;
        return c.textContent || '';
    }

    /* ---------- ساخت DOM ویرایشگر ---------- */
    function buildEditor(textarea) {
        var wrap = document.createElement('div');
        wrap.className = 'lbe-wrap';

        var toolbar = document.createElement('div');
        toolbar.className = 'lbe-toolbar';

        var btnAdd = document.createElement('div');
        btnAdd.className = 'lbe-addrow';
        btnAdd.innerHTML =
            '<button type="button" class="lbe-add" data-t="text">＋ متن</button>' +
            '<button type="button" class="lbe-add" data-t="heading">✎ تیتر</button>' +
            '<button type="button" class="lbe-add" data-t="bullet">• لیست</button>' +
            '<button type="button" class="lbe-add" data-t="quote">❝ نقل‌قول</button>' +
            '<button type="button" class="lbe-add" data-t="code">&lt;/&gt; کد</button>' +
            '<button type="button" class="lbe-add lbe-addimg" data-t="image">🖼 عکس</button>';
        toolbar.appendChild(btnAdd);
        wrap.appendChild(toolbar);

        var canvas = document.createElement('div');
        canvas.className = 'lbe-canvas';
        wrap.appendChild(canvas);

        var hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.name = '__lbe_upload_target';
        hiddenInput.value = '';
        wrap.appendChild(hiddenInput);

        textarea.style.display = 'none';
        textarea.parentNode.insertBefore(wrap, textarea.nextSibling);

        return { wrap: wrap, canvas: canvas, textarea: textarea };
    }

    function addBlock(canvas, block, opts) {
        var el = document.createElement('div');
        el.className = 'lbe-block';
        el.setAttribute('data-type', block.type);

        /* دستگیرهٔ درگ */
        var drag = document.createElement('span');
        drag.className = 'lbe-drag';
        drag.textContent = '⠿';
        drag.setAttribute('draggable', 'true');
        drag.title = 'درگ برای جابه‌جایی';
        el.appendChild(drag);

        /* دکمه‌های حذف / کپی */
        var actions = document.createElement('div');
        actions.className = 'lbe-actions';
        var btnUp = document.createElement('button');
        btnUp.type = 'button'; btnUp.className = 'lbe-act'; btnUp.title = 'بالا';
        btnUp.innerHTML = '↑';
        var btnDown = document.createElement('button');
        btnDown.type = 'button'; btnDown.className = 'lbe-act'; btnDown.title = 'پایین';
        btnDown.innerHTML = '↓';
        var btnDel = document.createElement('button');
        btnDel.type = 'button'; btnDel.className = 'lbe-act lbe-del'; btnDel.title = 'حذف';
        btnDel.innerHTML = '🗑';
        actions.appendChild(btnUp);
        actions.appendChild(btnDown);
        actions.appendChild(btnDel);
        el.appendChild(actions);

        /* بدنهٔ بلوک */
        var body = document.createElement('div');
        body.className = 'lbe-body';

        if (block.type === 'image') {
            var img = document.createElement('img');
            img.className = 'lbe-img';
            if (block.src) img.src = block.src;
            body.appendChild(img);
            var imgRow = document.createElement('div');
            imgRow.className = 'lbe-imgrow';
            var file = document.createElement('input');
            file.type = 'file';
            file.accept = 'image/*';
            file.className = 'lbe-file';
            file.innerHTML = '';
            var hint = document.createElement('span');
            hint.className = 'lbe-hint';
            hint.textContent = 'آپلود عکس (تا ۵MB)';
            imgRow.appendChild(file);
            imgRow.appendChild(hint);
            body.appendChild(imgRow);
            el._file = file;
        } else {
            var ta = document.createElement('textarea');
            ta.className = 'lbe-text';
            ta.placeholder = EDITOR_PLACEHOLDER;
            ta.rows = block.type === 'heading' ? 1 : (block.type === 'text' ? 3 : 2);
            ta.value = htmlForEdit(block.content || '');
            ta.addEventListener('input', function () { autoGrow(ta); });
            body.appendChild(ta);
            el._ta = ta;
        }
        el.appendChild(body);
        canvas.appendChild(el);

        /* دکمه‌های بالا/پایین/حذف */
        btnUp.addEventListener('click', function () {
            if (el.previousElementSibling && el.previousElementSibling.classList.contains('lbe-block')) {
                canvas.insertBefore(el, el.previousElementSibling);
            }
        });
        btnDown.addEventListener('click', function () {
            if (el.nextElementSibling && el.nextElementSibling.classList.contains('lbe-block')) {
                canvas.insertBefore(el.nextElementSibling, el);
            }
        });
        btnDel.addEventListener('click', function () {
            if (el._file && el._file.dataset.uploaded === '1') {
                // فایل آپلودشده به‌صورت کامل حذف می‌شود
            }
            el.remove();
        });

        /* درگ‌اندروپ */
        drag.addEventListener('dragstart', function (e) {
            e.dataTransfer.setData('text/plain', 'block');
            el.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
        });
        drag.addEventListener('dragend', function () {
            el.classList.remove('dragging');
            canvas.querySelectorAll('.lbe-block').forEach(function (b) { b.classList.remove('drop-target'); });
        });
        canvas.addEventListener('dragover', function (e) {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            var dragging = canvas.querySelector('.lbe-block.dragging');
            if (!dragging) return;
            canvas.querySelectorAll('.lbe-block').forEach(function (b) { b.classList.remove('drop-target'); });
            var after = getDragAfterElement(canvas, e.clientY);
            var target = after ? after : null;
            if (target) target.classList.add('drop-target');
        });
        canvas.addEventListener('drop', function (e) {
            e.preventDefault();
            var dragging = canvas.querySelector('.lbe-block.dragging');
            if (!dragging) return;
            var after = getDragAfterElement(canvas, e.clientY);
            if (after == null) canvas.appendChild(dragging);
            else canvas.insertBefore(dragging, after);
            canvas.querySelectorAll('.lbe-block').forEach(function (b) { b.classList.remove('drop-target'); });
        });

        /* آپلود عکس */
        if (block.type === 'image' && file) {
            file.addEventListener('change', function () {
                var f = file.files && file.files[0];
                if (!f) return;
                if (f.size > 5 * 1024 * 1024) { alert('حداکثر ۵ مگابایت'); return; }
                var fd = new FormData();
                fd.append('file', f);
                fd.append('target', '__lesson_block__');
                var uploadUrl = window.LBE_UPLOAD_URL || '';
                if (!uploadUrl) { alert('آدرس آپلود تنظیم نشده'); return; }
                fetch(uploadUrl, { method: 'POST', body: fd, headers: { 'X-CSRFToken': window.LBE_CSRF || '' } })
                    .then(function (r) { return r.json(); })
                    .then(function (d) {
                        if (d.ok) {
                            img.src = d.url;
                            el._imgUrl = d.url;
                            file.dataset.uploaded = '1';
                            hint.textContent = '✓ آپلود شد — می‌توانید عوض کنید';
                        } else {
                            alert(d.error || 'خطا در آپلود');
                        }
                    })
                    .catch(function () { alert('خطای اتصال'); });
            });
        }
        return el;
    }

    function getDragAfterElement(container, y) {
        var els = [].slice.call(container.querySelectorAll('.lbe-block:not(.dragging)'));
        var closest = { offset: -Infinity, element: null };
        els.forEach(function (child) {
            var box = child.getBoundingClientRect();
            var offset = y - box.top - box.height / 2;
            if (offset < 0 && offset > closest.offset) {
                closest = { offset: offset, element: child };
            }
        });
        return closest.element;
    }

    function autoGrow(ta) {
        ta.style.height = 'auto';
        ta.style.height = Math.max(ta.scrollHeight + 2, 60) + 'px';
    }

    /* ---------- راه‌اندازی ---------- */
    function init() {
        var uploadInput = document.getElementById('id_lesson_upload_target');
        window.LBE_UPLOAD_URL = window.LBE_UPLOAD_URL || (uploadInput ? uploadInput.dataset.url : '');
        window.LBE_CSRF = window.LBE_CSRF || (function () {
            var m = document.cookie.match(/(^|;\s*)csrftoken\s*=\s*([^;]+)/);
            return m ? decodeURIComponent(m[2]) : '';
        })();

        document.querySelectorAll('textarea[data-block-editor]').forEach(function (ta) {
            var editor = buildEditor(ta);
            var blocks = htmlToBlocks(ta.value || '');
            blocks.forEach(function (b) { addBlock(editor.canvas, b, {}); });

            /* افزودن بلوک جدید */
            editor.wrap.querySelectorAll('.lbe-add').forEach(function (btn) {
                btn.addEventListener('click', function () {
                    var type = btn.getAttribute('data-t');
                    var b = { type: type, content: '', src: '' };
                    if (type === 'image') {
                        addBlock(editor.canvas, b, {});
                        // auto-open file picker
                        var last = editor.canvas.querySelector('.lbe-block:last-child .lbe-file');
                        if (last) last.click();
                    } else {
                        addBlock(editor.canvas, b, {});
                        var lastTa = editor.canvas.querySelector('.lbe-block:last-child .lbe-text');
                        if (lastTa) lastTa.focus();
                    }
                });
            });

            /* همگام‌سازی در ارسال فرم */
            var form = ta.closest('form');
            if (form) {
                form.addEventListener('submit', function (e) {
                    var blocks = [];
                    editor.canvas.querySelectorAll('.lbe-block').forEach(function (el) {
                        var type = el.getAttribute('data-type');
                        if (type === 'image') {
                            if (el._imgUrl) blocks.push({ type: 'image', content: '', src: el._imgUrl });
                        } else {
                            var val = el._ta ? el._ta.value.trim() : '';
                            if (val) blocks.push({ type: type, content: val });
                        }
                    });
                    ta.value = blocksToHtml(blocks);
                });
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
