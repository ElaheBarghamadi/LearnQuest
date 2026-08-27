import json
import logging
import os
import time
import urllib.request
import urllib.error

from django.conf import settings

logger = logging.getLogger(__name__)

OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions'
# مدل پیش‌فرض: رایگان و با پشتیبانی خوب از فارسی + خروجی JSON (۲۰۲۶-۰۸)
# مدل قبلی (llama-3.3-70b:free) دیگر رایگان نیست و OpenRouter خطای 404 می‌دهد.
DEFAULT_MODEL = 'minimax/minimax-m3:free'


def api_key():
    key = getattr(settings, 'OPENROUTER_API_KEY', '') or os.environ.get('OPENROUTER_API_KEY', '')
    if not key:
        try:
            key_path = os.path.join(settings.BASE_DIR, 'openrouter_key.txt')
            if os.path.exists(key_path):
                with open(key_path, 'r', encoding='utf-8') as f:
                    key = f.read().strip()
        except OSError:
            key = ''
    return key


def model_name():
    return getattr(settings, 'OPENROUTER_MODEL', '') or os.environ.get('OPENROUTER_MODEL', '') or DEFAULT_MODEL


def available():
    return bool(api_key())


def _post_once(body, key, timeout):
    req = urllib.request.Request(
        OPENROUTER_URL,
        data=body,
        headers={
            'Authorization': 'Bearer ' + key,
            'Content-Type': 'application/json',
            'HTTP-Referer': getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000'),
            'X-Title': 'LearnQuest AI Tutor',
        },
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode('utf-8'))


def chat(messages, temperature=0.4, max_tokens=1200, timeout=25, retries=2):
    key = api_key()
    if not key:
        return None
    body = json.dumps({
        'model': model_name(),
        'messages': messages,
        'temperature': temperature,
        'max_tokens': max_tokens,
    }).encode('utf-8')
    for attempt in range(retries + 1):
        try:
            data = _post_once(body, key, timeout)
            break
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < retries:
                # لایهٔ رایگان OpenRouter محدودیت ریکвест/دقیقه دارد؛ کمی صبر و تلاش دوباره
                wait = 5 * (attempt + 1)
                logger.warning('OpenRouter 429 rate limit - retrying in %ss', wait)
                time.sleep(wait)
                continue
            logger.warning('OpenRouter call failed: %s', exc)
            return None
        except (urllib.error.URLError, ValueError, OSError) as exc:
            logger.warning('OpenRouter call failed: %s', exc)
            return None
    else:
        return None
    try:
        return data['choices'][0]['message']['content']
    except (KeyError, IndexError, TypeError):
        return None


def _extract_json(text):
    if not text:
        return None
    t = text.strip()
    if t.startswith('```'):
        t = t.split('```', 2)[1]
        if t.lstrip().lower().startswith('json'):
            t = t.lstrip()[4:]
        t = t.strip()
    try:
        return json.loads(t)
    except ValueError:
        pass
    for opener, closer in (('[', ']'), ('{', '}')):
        i = text.find(opener)
        j = text.rfind(closer)
        if 0 <= i < j:
            try:
                return json.loads(text[i:j + 1])
            except ValueError:
                continue
    return None


def chat_json(messages, temperature=0.3, max_tokens=1800, expected=list, retries=1):
    for _ in range(retries + 1):
        raw = chat(messages, temperature=temperature, max_tokens=max_tokens)
        obj = _extract_json(raw)
        if isinstance(obj, expected):
            return obj
    return None
