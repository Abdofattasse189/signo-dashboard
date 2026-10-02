# session.py
"""هوية المستخدم — تُحفظ في dict على الخادم مفتاحه browser_id (cookie دائم)."""
from nicegui import app


USER_META = {
    'عبد الرحمان': {'initial': 'A', 'slug': 'abd',
                    'bg': '#dbeafe', 'fg': '#1e40af', 'border': '#93c5fd'},
    'محمد':        {'initial': 'M', 'slug': 'moh',
                    'bg': '#ede9fe', 'fg': '#6d28d9', 'border': '#c4b5fd'},
    'أسامة':       {'initial': 'O', 'slug': 'osa',
                    'bg': '#dcfce7', 'fg': '#15803d', 'border': '#86efac'},
}
ALLOWED_USERS = list(USER_META.keys())

# مفتاح التخزين: browser_id → اسم المستخدم
_USERS = {}


def _bid():
    """معرّف المتصفح — يُحفظ في cookie دائم."""
    try:
        return app.storage.browser.get('id')
    except Exception:
        return None


def get_user():
    bid = _bid()
    return _USERS.get(bid) if bid else None


def set_user(name):
    if name not in ALLOWED_USERS:
        return False
    bid = _bid()
    if not bid:
        return False
    _USERS[bid] = name
    return True


def clear_user():
    bid = _bid()
    if bid:
        _USERS.pop(bid, None)


def get_meta(name=None):
    name = name or get_user()
    return USER_META.get(name, {
        'initial': '?', 'slug': 'x',
        'bg': '#f3f3f3', 'fg': '#666', 'border': '#ddd',
    })