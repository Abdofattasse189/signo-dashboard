# chat.py
"""غرفة تواصل — Markdown · ملفات · نسخ · تعديل."""
import json
import time
import uuid

from nicegui import ui

import session


TITLE = 'غرفة التواصل'
ICON  = 'chat_bubble_outline'
DESC  = ('دردشة فورية بين ثلاثة أعضاء — Markdown، أكواد، ملفات، '
         'نسخ وتعديل الرسائل.')

MAX_MESSAGES  = 300
MAX_RENDERED  = 100
MAX_FILE_SIZE = 8 * 1024 * 1024


# ═══════════════════════════════════════════════════════════
# المخزن العام
# ═══════════════════════════════════════════════════════════
MESSAGES = []
FILES    = {}
_version = {'v': 0}


# ═══════════════════════════════════════════════════════════
# أدوات
# ═══════════════════════════════════════════════════════════
def _push(user, text=None, file_meta=None):
    msg = {
        'id': uuid.uuid4().hex[:10],
        'user': user,
        'time': time.strftime('%H:%M'),
        'ts': time.time(),
        'edited': False,
    }
    if file_meta:
        msg['type'] = 'file'
        msg['file'] = file_meta
    else:
        msg['type'] = 'text'
        msg['text'] = (text or '').strip()[:4000]
    MESSAGES.append(msg)
    if len(MESSAGES) > MAX_MESSAGES:
        del MESSAGES[:len(MESSAGES) - MAX_MESSAGES]
    _version['v'] += 1
    return msg


def _push_text(user, text):
    if (text or '').strip():
        _push(user, text=text)


def _push_file(user, name, mime, data):
    fid = uuid.uuid4().hex[:12]
    FILES[fid] = {'name': name, 'mime': mime, 'data': data}
    _push(user, file_meta={'id': fid, 'name': name, 'size': len(data)})


def _fmt_size(n):
    if n < 1024:
        return f'{n} B'
    if n < 1024 * 1024:
        return f'{n / 1024:.1f} KB'
    return f'{n / (1024 * 1024):.2f} MB'


def _copy(text):
    ui.run_javascript(f'navigator.clipboard.writeText({json.dumps(text)})')
    ui.notify('تم النسخ', type='positive', position='top', timeout=1200)


def _scroll_bottom():
    try:
        ui.run_javascript(
            "setTimeout(function(){"
            "  var el = document.querySelector('.chat-messages');"
            "  if (el) el.scrollTop = el.scrollHeight;"
            "}, 80);"
        )
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════
# الواجهة الرئيسية
# ═══════════════════════════════════════════════════════════
def build() -> dict:
    refs = {}
    user = session.get_user()

    ui.label('02').classes('page-number')
    ui.label(TITLE).classes('page-title')
    ui.element('div').classes('divider')
    ui.label(DESC).classes('hint-box')

    if not user:
        ui.label('الرجاء اختيار هوية من الصفحة الرئيسية.').classes('hint-box')
        return refs

    meta = session.get_meta(user)

    # ─── الرأس ───
    with ui.element('div').classes('chat-header'):
        ui.label('SIGNO · Chat').classes('chat-logo')
        with ui.element('div').classes('chat-header-right'):
            with ui.element('div').classes('chat-me'):
                ui.label(meta['initial']).classes('chat-avatar chat-avatar-sm') \
                    .style(f'background:{meta["bg"]}; color:{meta["fg"]}; '
                           f'border:1px solid {meta["border"]}')
                ui.label(user).classes('chat-me-label')

    # ─── منطقة الرسائل ───
    with ui.element('div').classes('chat-messages'):

        @ui.refreshable
        def messages_view():
            if not MESSAGES:
                with ui.column().classes('chat-empty'):
                    ui.label('لا توجد رسائل بعد').classes('chat-empty-title')
                    ui.label('ابدأ المحادثة بكتابة أول رسالة').classes('chat-empty-hint')
                return
            for m in MESSAGES[-MAX_RENDERED:]:
                _render_message(m, user, messages_view.refresh)

        messages_view()

    refs['messages_view'] = messages_view

    # ─── منطقة الإدخال ───
    code_mode = {'on': False}

    with ui.element('div').classes('chat-input-area'):

        # رافع الملفات (مُنسَّق كأيقونة)
        async def handle_upload(e):
            try:
                data = await e.file.read()
            except Exception:
                try:
                    data = e.content.read()
                except Exception:
                    data = b''

            if not data:
                ui.notify('فشل قراءة الملف', type='negative')
                return

            if len(data) > MAX_FILE_SIZE:
                ui.notify(
                    f'الملف كبير — الحد {_fmt_size(MAX_FILE_SIZE)}',
                    type='negative', position='top',
                )
                return

            _push_file(
                user,
                e.file.name,
                e.file.content_type or 'application/octet-stream',
                data,
            )
            ui.notify(f'تم إرفاق {e.file.name}', type='positive', position='top')
            messages_view.refresh()
            _scroll_bottom()

        ui.upload(
            on_upload=handle_upload,
            auto_upload=True,
            multiple=True,
            max_file_size=MAX_FILE_SIZE,
        ).props('flat dense label=""').classes('chat-upload-inline')

        # زر تحويل لكتلة كود
        code_btn = ui.button(icon='code') \
            .props('flat dense').classes('chat-icon-btn')

        def toggle_code():
            code_mode['on'] = not code_mode['on']
            if code_mode['on']:
                code_btn.classes(add='active')
                ui.notify('الرسالة القادمة ستُرسل ككتلة كود',
                          position='top', timeout=1500)
            else:
                code_btn.classes(remove='active')

        code_btn.on_click(toggle_code)

        # حقل النص
        input_field = ui.textarea(
            placeholder='اكتب رسالة... (Enter للإرسال، Shift+Enter لسطر جديد)'
        ).props('borderless autogrow rows=1').classes('chat-input-field')

        # زر الإرسال
        def send():
            text = (input_field.value or '').strip()
            if not text:
                return
            if code_mode['on']:
                text = f'```\n{text}\n```'
                code_mode['on'] = False
                code_btn.classes(remove='active')
            _push_text(user, text)
            input_field.value = ''
            messages_view.refresh()
            _scroll_bottom()

        ui.button(icon='send', on_click=send) \
            .props('flat dense').classes('chat-send-btn')

    # ─── تلميح ───
    ui.label('Enter = إرسال · Shift+Enter = سطر جديد · زر <> = كتلة كود') \
        .classes('chat-input-hint')

    return refs


# ═══════════════════════════════════════════════════════════
# رسم رسالة واحدة
# ═══════════════════════════════════════════════════════════
def _render_message(m, viewer, on_refresh):
    meta = session.get_meta(m['user'])
    own = (m['user'] == viewer)
    display_name = 'أنت' if own else m['user']

    with ui.element('div').classes(
        f'chat-msg chat-msg-{meta["slug"]} ' + ('own' if own else 'other')
    ):
        # الرأس
        with ui.element('div').classes('chat-msg-head'):
            if not own:
                ui.label(meta['initial']).classes('chat-avatar chat-avatar-sm') \
                    .style(f'background:{meta["bg"]}; color:{meta["fg"]}; '
                           f'border:1px solid {meta["border"]}')

            ui.label(display_name).classes('chat-msg-name') \
                .style(f'color:{meta["fg"]}')

            if m.get('edited'):
                ui.label('(مُعدّلة)').classes('chat-msg-edited')

            ui.label(m['time']).classes('chat-msg-time')

            # الإجراءات
            with ui.element('div').classes('chat-msg-actions'):
                if m['type'] == 'text':
                    ui.button(icon='content_copy',
                              on_click=lambda t=m['text']: _copy(t)) \
                        .props('flat dense round size=sm') \
                        .classes('chat-copy-btn')

                    if own:
                        ui.button(
                            icon='edit',
                            on_click=lambda mid=m['id']: _open_edit_dialog(mid, on_refresh),
                        ).props('flat dense round size=sm') \
                         .classes('chat-copy-btn')

                else:
                    fm = m['file']
                    ui.button(icon='link',
                              on_click=lambda f=fm: _copy(f['name'])) \
                        .props('flat dense round size=sm') \
                        .classes('chat-copy-btn')

        # الجسم
        with ui.element('div').classes('chat-msg-body'):
            if m['type'] == 'text':
                with ui.element('div').classes('chat-markdown'):
                    ui.markdown(m['text'])
            else:
                _render_file(m['file'])


# ─── بطاقة الملف ───
def _render_file(fm):
    data = FILES.get(fm['id'], {}).get('data', b'')

    with ui.element('div').classes('chat-file'):
        with ui.element('div').classes('chat-file-icon'):
            ui.icon('insert_drive_file').style('font-size:22px')

        with ui.element('div').classes('chat-file-info'):
            ui.label(fm['name']).classes('chat-file-name')
            ui.label(_fmt_size(fm['size'])).classes('chat-file-size')

        ui.button('تحميل',
                  on_click=lambda d=data, n=fm['name']: ui.download(d, n)) \
            .props('flat no-caps').classes('chat-file-dl')


# ─── نافذة تعديل الرسالة ───
def _open_edit_dialog(msg_id, on_refresh):
    msg = next((m for m in MESSAGES if m['id'] == msg_id), None)
    if not msg or msg['type'] != 'text':
        return

    with ui.dialog() as dlg, ui.card().classes('chat-edit-dialog'):
        ui.label('تعديل الرسالة').classes('chat-edit-title')

        edit_input = ui.textarea(value=msg['text']) \
            .props('borderless autogrow rows=3') \
            .classes('chat-edit-input')

        with ui.element('div').classes('chat-edit-actions'):
            def save():
                new_text = (edit_input.value or '').strip()
                if new_text and new_text != msg['text']:
                    msg['text'] = new_text[:4000]
                    msg['edited'] = True
                    _version['v'] += 1
                    on_refresh()
                    _scroll_bottom()
                dlg.close()

            ui.button('إلغاء', on_click=dlg.close) \
                .props('flat no-caps').classes('chat-edit-cancel')

            ui.button('حفظ', on_click=save) \
                .props('flat no-caps').classes('chat-edit-save')

    dlg.open()


# ═══════════════════════════════════════════════════════════
# التحديث الدوري
# ═══════════════════════════════════════════════════════════
async def refresh(refs: dict):
    mv = refs.get('messages_view')
    if mv is None:
        return

    v_now  = _version['v']
    v_seen = refs.get('_v', -1)
    if v_now == v_seen:
        return
    refs['_v'] = v_now
    mv.refresh()
    _scroll_bottom()


def on_enter():
    pass