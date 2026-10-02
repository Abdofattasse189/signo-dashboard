# soundboard.py
"""لوحة الجمل السريعة — أزرار ناطقة لعبارات شائعة."""
from nicegui import ui

import audio
import session


TITLE = 'لوحة الجمل السريعة'
ICON  = 'campaign'
DESC  = ('عبارات شائعة ومهمة — اضغط على أي زر لينطق الموقع العبارة '
         'بصوت عربي واضح. أداة مساعدة سريعة للتواصل الفوري.')


# ═══════════════════════════════════════════════════════════
# العبارات — (نص الزر، النص المنطوق)
# ═══════════════════════════════════════════════════════════
PHRASES_BASIC = [
    ('نعم',              'نعم'),
    ('لا',               'لا'),
    ('شكراً',            'شكراً جزيلاً'),
    ('من فضلك',          'من فضلك'),
    ('مرحباً',           'مرحباً'),
    ('إلى اللقاء',       'إلى اللقاء'),
    ('معذرة',            'معذرة'),
    ('أنا بخير',         'أنا بخير، شكراً'),
]

PHRASES_NEEDS = [
    ('أحتاج مساعدة',     'أحتاج مساعدة من فضلك'),
    ('أريد ماء',         'أريد ماءً من فضلك'),
    ('أنا جائع',         'أنا جائع'),
    ('أشعر بالتعب',      'أشعر بالتعب'),
    ('أشعر بالألم',      'أشعر بالألم'),
    ('أريد الحمام',      'أريد الذهاب إلى الحمام'),
]

PHRASES_URGENT = [
    ('اتصل بالطوارئ',    'اتصل بالطوارئ من فضلك'),
    ('أحتاج طبيباً',     'أحتاج طبيباً بسرعة'),
    ('ساعدوني',          'ساعدوني من فضلك'),
    ('انتبه!',           'انتبه، هناك خطر'),
]

PHRASES_QUESTIONS = [
    ('كم الساعة؟',       'كم الساعة من فضلك؟'),
    ('أين أنا؟',         'أين أنا؟'),
    ('ما اسمك؟',         'ما اسمك؟'),
    ('أعد من فضلك',      'أعد ما قلت من فضلك'),
]


def build() -> dict:
    refs = {}
    user = session.get_user()

    ui.label('04').classes('page-number')
    ui.label(TITLE).classes('page-title')
    ui.element('div').classes('divider')
    ui.label(DESC).classes('hint-box')

    if not user:
        ui.label('الرجاء اختيار هوية من الصفحة الرئيسية.').classes('hint-box')
        return refs

    # ─── شريط الحالة ───
    s = audio.get()
    with ui.element('div').classes('sb-status'):
        ui.icon('record_voice_over').classes('sb-status-icon')
        ui.label('النطق بالعربية').classes('sb-status-label')
        with ui.element('div').classes('sb-status-meta'):
            ui.label(f'السرعة: {s["rate"]:.2f}') \
                .classes('sb-status-item')
            ui.label(f'النبرة: {s["pitch"]:.2f}') \
                .classes('sb-status-item')
            voice_name = s.get('voice') or 'افتراضي'
            ui.label(f'الصوت: {voice_name[:24]}') \
                .classes('sb-status-item')

    # ─── الأقسام ───
    _render_section('عبارات أساسية', PHRASES_BASIC, 'sb-basic')
    _render_section('احتياجات', PHRASES_NEEDS, 'sb-needs')
    _render_section('طوارئ', PHRASES_URGENT, 'sb-urgent')
    _render_section('أسئلة', PHRASES_QUESTIONS, 'sb-questions')

    return refs


def _render_section(title, items, cls):
    with ui.element('div').classes('sb-section'):
        ui.label(title).classes('sb-section-title')
        with ui.element('div').classes(f'sb-grid {cls}'):
            for display, say in items:
                btn = ui.button(display) \
                    .props('flat no-caps') \
                    .classes('sb-btn')
                btn.on_click(lambda t=say: audio.speak(t))


async def refresh(refs):
    pass


def on_enter():
    pass