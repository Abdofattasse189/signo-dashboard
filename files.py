# files.py
"""مستودع الملفات — رفع، عرض، تحميل، حذف."""
import json
import time
import uuid

from nicegui import ui

import session


TITLE = 'مستودع الملفات'
ICON  = 'folder_open'
DESC  = 'مستودع مشترك لرفع الملفات وتحميلها.'

MAX_FILE_SIZE = 15 * 1024 * 1024

FILES = {}
_version = {'v': 0}


def _fmt_size(n):
    if n < 1024: return f'{n} B'
    if n < 1024 * 1024: return f'{n/1024:.1f} KB'
    return f'{n/(1024*1024):.2f} MB'


def _fmt_date(ts):
    return time.strftime('%Y-%m-%d %H:%M', time.localtime(ts))


def _ext_icon(name):
    n = (name or '').lower()
    if n.endswith(('.png','.jpg','.jpeg','.gif','.webp','.svg','.bmp')): return 'image'
    if n.endswith(('.mp4','.mov','.avi','.mkv','.webm')): return 'movie'
    if n.endswith(('.mp3','.wav','.ogg','.m4a')): return 'audiotrack'
    if n.endswith('.pdf'): return 'picture_as_pdf'
    if n.endswith(('.zip','.rar','.7z','.tar','.gz')): return 'folder_zip'
    if n.endswith(('.doc','.docx','.odt')): return 'description'
    if n.endswith(('.xls','.xlsx','.csv','.ods')): return 'table_chart'
    if n.endswith(('.ppt','.pptx','.odp')): return 'slideshow'
    if n.endswith(('.py','.js','.ts','.html','.css','.json','.java','.c','.cpp')): return 'code'
    return 'insert_drive_file'


def _copy(text):
    ui.run_javascript(f'navigator.clipboard.writeText({json.dumps(text)})')
    ui.notify('تم النسخ', type='positive', position='top', timeout=1200)


def build() -> dict:
    refs = {}
    user = session.get_user()

    ui.label('03').classes('page-number')
    ui.label(TITLE).classes('page-title')
    ui.element('div').classes('divider')
    ui.label(DESC).classes('hint-box')

    if not user:
        ui.label('الرجاء اختيار هوية من الصفحة الرئيسية.').classes('hint-box')
        return refs

    meta = session.get_meta(user)

    with ui.element('div').classes('repo-header'):
        ui.label('SIGNO · Files').classes('repo-logo')
        with ui.element('div').classes('repo-header-right'):
            with ui.element('div').classes('repo-me'):
                ui.label(meta['initial']).classes('chat-avatar chat-avatar-sm') \
                    .style(f'background:{meta["bg"]}; color:{meta["fg"]}; '
                           f'border:1px solid {meta["border"]}')
                ui.label(user).classes('repo-me-label')

    with ui.element('div').classes('repo-upload-area'):
        with ui.element('div').classes('repo-upload-text'):
            ui.icon('cloud_upload').classes('repo-upload-icon')
            ui.label('اسحب الملفات هنا أو اضغط للاختيار').classes('repo-upload-title')
            ui.label(f'الحد الأقصى: {_fmt_size(MAX_FILE_SIZE)}').classes('repo-upload-hint')

        async def handle_upload(e):
            try:
                data = await e.file.read()
            except Exception:
                try: data = e.content.read()
                except Exception: data = b''
            if not data:
                ui.notify('فشل قراءة الملف', type='negative'); return
            if len(data) > MAX_FILE_SIZE:
                ui.notify('الملف كبير', type='negative'); return
            fid = uuid.uuid4().hex[:12]
            FILES[fid] = {
                'id': fid, 'name': e.file.name,
                'mime': e.file.content_type or 'application/octet-stream',
                'size': len(data), 'data': data,
                'uploader': user, 'ts': time.time(),
            }
            _version['v'] += 1
            ui.notify(f'تم رفع {e.file.name}', type='positive', position='top')
            refs['files_view'].refresh()
            _update_stats(refs, user)

        ui.upload(
            on_upload=handle_upload,
            auto_upload=True,
            multiple=True,
            max_file_size=MAX_FILE_SIZE,
        ).props('flat no-caps label="رفع ملفات" accept=*/*') \
         .classes('repo-upload-btn')

    with ui.element('div').classes('repo-stats'):
        refs['stat_count'] = ui.label('0 ملف').classes('repo-stat')
        refs['stat_size']  = ui.label('0 B').classes('repo-stat')
        ui.element('div').classes('repo-stat-spacer')
        refs['stat_user'] = ui.label(f'مسجّل: {user}').classes('repo-stat repo-stat-muted')

    with ui.element('div').classes('repo-list'):
        @ui.refreshable
        def files_view():
            if not FILES:
                with ui.column().classes('repo-empty'):
                    ui.icon('folder_off').classes('repo-empty-icon')
                    ui.label('المستودع فارغ').classes('repo-empty-title')
                    ui.label('ارفع أول ملف لبدء الاستخدام').classes('repo-empty-hint')
                return

            ordered = sorted(FILES.values(), key=lambda f: f['ts'], reverse=True)

            with ui.element('div').classes('repo-row repo-row-head'):
                ui.label('الملف').classes('repo-col repo-col-name')
                ui.label('الحجم').classes('repo-col repo-col-size')
                ui.label('الرافع').classes('repo-col repo-col-user')
                ui.label('التاريخ').classes('repo-col repo-col-date')
                ui.label('').classes('repo-col repo-col-actions')

            for f in ordered:
                _render_row(f, user, lambda fid=f['id']: _delete_file(fid, refs, user))

        files_view()
        refs['files_view'] = files_view

    _update_stats(refs, user)
    return refs


def _render_row(f, viewer, on_delete):
    umeta = session.get_meta(f['uploader'])
    is_owner = (f['uploader'] == viewer)
    icon = _ext_icon(f['name'])

    with ui.element('div').classes('repo-row'):
        with ui.element('div').classes('repo-col repo-col-name'):
            ui.icon(icon).classes('repo-file-icon')
            ui.label(f['name']).classes('repo-file-name')
        ui.label(_fmt_size(f['size'])).classes('repo-col repo-col-size')
        with ui.element('div').classes('repo-col repo-col-user'):
            ui.label(umeta['initial']).classes('chat-avatar chat-avatar-xs') \
                .style(f'background:{umeta["bg"]}; color:{umeta["fg"]}; '
                       f'border:1px solid {umeta["border"]}')
            ui.label(f['uploader']).classes('repo-user-name')
        ui.label(_fmt_date(f['ts'])).classes('repo-col repo-col-date')
        with ui.element('div').classes('repo-col repo-col-actions'):
            ui.button(icon='download',
                      on_click=lambda d=f['data'], n=f['name']: ui.download(d, n)) \
                .props('flat dense round size=sm').classes('repo-action-btn')
            ui.button(icon='content_copy', on_click=lambda n=f['name']: _copy(n)) \
                .props('flat dense round size=sm').classes('repo-action-btn')
            if is_owner:
                ui.button(icon='delete', on_click=on_delete) \
                    .props('flat dense round size=sm') \
                    .classes('repo-action-btn repo-action-danger')


def _delete_file(fid, refs, user):
    if fid in FILES:
        name = FILES[fid]['name']
        del FILES[fid]
        _version['v'] += 1
        ui.notify(f'تم حذف {name}', type='warning', position='top')
        refs['files_view'].refresh()
        _update_stats(refs, user)


def _update_stats(refs, user):
    total = sum(f['size'] for f in FILES.values())
    if 'stat_count' in refs:
        refs['stat_count'].text = f'{len(FILES)} ملف'
    if 'stat_size' in refs:
        refs['stat_size'].text = _fmt_size(total)
    if 'stat_user' in refs and user:
        refs['stat_user'].text = f'مسجّل: {user}'


async def refresh(refs):
    fv = refs.get('files_view')
    if fv is None:
        return
    v_now = _version['v']
    v_seen = refs.get('_v', -1)
    if v_now == v_seen:
        return
    refs['_v'] = v_now
    fv.refresh()


def on_enter():
    pass