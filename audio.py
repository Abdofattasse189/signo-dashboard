# audio.py — النسخة المبسطة
"""إعدادات النطق الفوري (Web Speech API) للتنبؤات."""
import json

from nicegui import app, ui


DEFAULTS = {
    'rate':   1.0,
    'pitch':  1.0,
    'volume': 1.0,
    'voice':  '',
    'auto':   True,
}
_KEY = 'signo_voice'


def get():
    try:
        s = app.storage.browser.get(_KEY)
        if not isinstance(s, dict):
            return dict(DEFAULTS)
        merged = dict(DEFAULTS)
        merged.update(s)
        return merged
    except Exception:
        return dict(DEFAULTS)


def set(**kwargs):
    s = get()
    s.update(kwargs)
    try:
        app.storage.browser[_KEY] = s
    except Exception:
        pass
    return s


def speak(text, **overrides):
    """ينطق النص في المتصفح فوراً."""
    if not text:
        return
    s = get()
    s.update(overrides)
    payload = json.dumps({
        'text':   str(text),
        'rate':   float(s.get('rate', 1.0)),
        'pitch':  float(s.get('pitch', 1.0)),
        'volume': float(s.get('volume', 1.0)),
        'voice':  s.get('voice', '') or '',
    }, ensure_ascii=False)
    try:
        ui.run_javascript(
            f'window.signoSpeak && window.signoSpeak({payload})'
        )
    except Exception as e:
        print(f'[audio] speak failed: {e}', flush=True)


def speak_prediction(text):
    """يستدعيه ai_studio.py — ينطق إذا كان auto مُفعّلاً."""
    if get().get('auto', True):
        speak(text)


def stop():
    try:
        ui.run_javascript(
            'window.speechSynthesis && window.speechSynthesis.cancel()'
        )
    except Exception:
        pass


def refresh_voices():
    try:
        ui.run_javascript('window.signoListVoices && window.signoListVoices()')
    except Exception:
        pass