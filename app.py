# app.py
"""نقطة الدخول — هوية عالمية + قائمة جانبية + 5 صفحات."""
import os

from nicegui import app, ui

import mqtt_client as mqtt
import session
from assets import CSS, GLOVE_SVG, CHAT_INPUT_JS

# ─── الصفحات (الترتيب إلزامي) ───
import sensors
import ai_studio
import voice
import files
import chat


# ═══════════════════════════════════════════════════════════
# ترتيب الصفحات في القائمة الجانبية
# ═══════════════════════════════════════════════════════════
PAGES = [
    sensors,       # 1 · لوحة الحساسات
    ai_studio,     # 2 · استوديو الذكاء الاصطناعي
    voice,         # 3 · تحويل النص إلى صوت
    files,         # 4 · مستودع الملفات
    chat,          # 5 · غرفة التواصل
]


# ═══════════════════════════════════════════════════════════
# تشغيل MQTT
# ═══════════════════════════════════════════════════════════
mqtt.start()


@app.on_shutdown
def _shutdown():
    mqtt.stop()


# ═══════════════════════════════════════════════════════════
# الصفحة الرئيسية
# ═══════════════════════════════════════════════════════════
@ui.page('/')
async def main_page():
    ui.add_head_html(CSS)
    ui.add_body_html(CHAT_INPUT_JS)

    user = session.get_user()
    if not user:
        _build_login()
    else:
        _build_app(user)


# ═══════════════════════════════════════════════════════════
# شاشة اختيار الهوية
# ═══════════════════════════════════════════════════════════
def _build_login():
    def choose(name):
        if session.set_user(name):
            ui.run_javascript('window.location.reload()')

    with ui.element('div').classes('app-login-wrap'):
        with ui.element('div').classes('app-login-card'):
            ui.html(GLOVE_SVG).classes('app-login-glove')
            ui.label('SIGNO').classes('app-login-brand')
            ui.label('Smart Sign Glove · v1.0').classes('app-login-sub')
            ui.label('اختر هويتك للدخول').classes('app-login-prompt')

            with ui.element('div').classes('app-login-users'):
                for uname, meta in session.USER_META.items():
                    def make_click(n=uname):
                        return lambda: choose(n)

                    with ui.element('div').classes('app-login-user') \
                            .on('click', make_click()):
                        ui.label(meta['initial']).classes('chat-avatar') \
                            .style(f'background:{meta["bg"]}; color:{meta["fg"]}; '
                                   f'border:1px solid {meta["border"]}')
                        ui.label(uname).classes('app-login-user-name')


# ═══════════════════════════════════════════════════════════
# التطبيق الكامل (بعد تسجيل الدخول)
# ═══════════════════════════════════════════════════════════
def _build_app(user):
    meta = session.get_meta(user)
    state = {'i': 0}
    card_elems = []
    page_refs = []
    nav_buttons = []

    def do_switch():
        session.clear_user()
        ui.run_javascript('window.location.reload()')

    def select(i):
        state['i'] = i
        for k, c in enumerate(card_elems):
            c.set_visibility(k == i)
        for k, b in enumerate(nav_buttons):
            b.classes(add='active') if k == i else b.classes(remove='active')
        if hasattr(PAGES[i], 'on_enter'):
            try:
                PAGES[i].on_enter()
            except Exception as e:
                print(f'[on_enter] {PAGES[i].__name__}: {e}', flush=True)

    # ═══════════════════════════════════════════════════════
    # الشريط الجانبي
    # ═══════════════════════════════════════════════════════
    with ui.left_drawer(value=True, bordered=False).props('width=250').classes('p-0'):
        with ui.column().classes('w-full h-full gap-0'):

            # ─── الشعار ───
            with ui.element('div').classes('brand-block'):
                with ui.element('div').classes('brand-left'):
                    ui.html(GLOVE_SVG).classes('brand-glove')
                    ui.label('SIGNO').classes('brand')
                ui.label('◼').classes('brand-mark')

            # ─── أزرار التنقل ───
            with ui.column().classes('nav-list'):
                for i, page in enumerate(PAGES):
                    btn = ui.button(
                        getattr(page, 'TITLE', f'صفحة {i+1}'),
                        icon=getattr(page, 'ICON', 'circle'),
                        on_click=lambda k=i: select(k),
                    ).props('flat no-caps align=left').classes('nav-btn w-full')
                    nav_buttons.append(btn)

            ui.space()

            # ─── بطاقة الهوية الحالية ───
            with ui.element('div').classes('sidebar-user'):
                ui.label(meta['initial']).classes('chat-avatar chat-avatar-sm') \
                    .style(f'background:{meta["bg"]}; color:{meta["fg"]}; '
                           f'border:1px solid {meta["border"]}')
                with ui.element('div').classes('sidebar-user-info'):
                    ui.label(user).classes('sidebar-user-name')
                    ui.label('الهوية الحالية').classes('sidebar-user-hint')
                ui.button(icon='swap_horiz', on_click=do_switch) \
                    .props('flat dense round size=sm') \
                    .classes('sidebar-switch-btn')

            ui.label('V 1.0').classes('footer-mark')

    # ═══════════════════════════════════════════════════════
    # المحتوى (البطاقات)
    # ═══════════════════════════════════════════════════════
    with ui.element('div').classes('content-wrap'):
        for idx, page in enumerate(PAGES):
            with ui.column().classes('card') as card:
                # رأس البطاقة
                with ui.element('div').classes('card-header'):
                    ui.label('لوحة التحكم').classes('card-title')
                    ui.label(f'{idx+1:02d} / {len(PAGES):02d}').classes('card-index')

                # جسم البطاقة (يبنيها ملف الصفحة)
                with ui.column().classes('card-body'):
                    page_refs.append(page.build())

                # تذييل البطاقة
                with ui.element('div').classes('card-footer'):
                    ui.label('SIGNO SYSTEM').classes('footer-label')
                    with ui.element('div').style('display:flex;gap:5px'):
                        for _ in PAGES:
                            ui.element('div').style(
                                'width:6px;height:6px;'
                                'border:1px solid #000;border-radius:50%'
                            )

            card_elems.append(card)

    # ─── اختيار الصفحة الافتراضية ───
    select(0)

    # ═══════════════════════════════════════════════════════
    # حلقة التحديث الدوري
    # ═══════════════════════════════════════════════════════
    async def refresh():
        try:
            page = PAGES[state['i']]
            await page.refresh(page_refs[state['i']])
        except Exception as e:
            print(f'[refresh] {e}', flush=True)

    ui.timer(0.1, refresh)


# ═══════════════════════════════════════════════════════════
# التشغيل — يدعم Hugging Face Spaces + محلي
# ═══════════════════════════════════════════════════════════
port = int(os.environ.get('PORT', 7860))
storage_secret = os.environ.get(
    'STORAGE_SECRET',
    'signo-hf-secret-change-me-in-production',
)

ui.run(
    host='0.0.0.0',
    port=port,
    title='SIGNO',
    language='ar',
    dark=False,
    favicon='🧤',
    reload=False,
    storage_secret=storage_secret,
    show=False,
)