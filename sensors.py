# sensors.py
"""صفحة لوحة الحساسات — عرض مباشر فقط."""
from nicegui import ui

from mqtt_client import STATE


# ─── بطاقة الصفحة (يستخدمها app.py للتنقل) ───
TITLE = 'لوحة الحساسات'
ICON  = 'sensors'


def _fmt_duration(ms: int) -> str:
    ms = max(0, ms)
    if ms < 1000:
        return f'{ms} ms'
    secs = ms / 1000
    if secs < 60:
        return f'{secs:.2f} ث'
    mins, rem = divmod(secs, 60)
    return f'{int(mins)} د {rem:.1f} ث'


def build() -> dict:
    """يبني واجهة الصفحة، ويعيد refs للتحديث."""
    refs = {}

    # شريط حالة MQTT
    with ui.element('div').classes('mqtt-bar'):
        refs['mqtt_dot']   = ui.element('div').classes('mqtt-dot wait')
        refs['mqtt_label'] = ui.label('جارٍ الاتصال...').classes('mqtt-label')
        refs['mqtt_meta']  = ui.label(
            f'{STATE.get("broker", "")}'
        ).classes('mqtt-meta')

    # العنوان
    ui.label('01').classes('page-number')
    ui.label(TITLE).classes('page-title')
    ui.element('div').classes('divider')
    ui.label(
        'قراءات حية من قفاز الإشارة: قيم الأصابع، الجايروسكوب، '
        'التسارع، والوقت. عرض مباشر فقط.'
    ).classes('hint-box')

    # الشبكة 2×2
    with ui.element('div').classes('sensor-grid'):

        # ─── الوقت ───
        with ui.element('div').classes('sensor-block'):
            ui.label('الوقت').classes('sensor-block-title')
            with ui.element('div').classes('sensor-rows'):
                for key, lbl in (
                    ('start',   'بدأ عند'),
                    ('now',     'الآن'),
                    ('elapsed', 'الوقت المنقضي'),
                ):
                    with ui.element('div').classes('sensor-row'):
                        ui.label(lbl).classes('sensor-label')
                        refs[key] = ui.label('—').classes('sensor-value')

        # ─── Flex ───
        with ui.element('div').classes('sensor-block'):
            ui.label('الأصابع · Flex').classes('sensor-block-title')
            with ui.element('div').classes('sensor-rows'):
                for i in range(1, 6):
                    key = f'flex{i}'
                    with ui.element('div').classes('sensor-row'):
                        ui.label(f'Flex {i}').classes('sensor-label')
                        refs[key] = ui.label('—').classes('sensor-value')

        # ─── Gyro ───
        with ui.element('div').classes('sensor-block'):
            ui.label('الجايروسكوب · Gyro').classes('sensor-block-title')
            with ui.element('div').classes('sensor-rows'):
                for key in ('gx', 'gy', 'gz'):
                    with ui.element('div').classes('sensor-row'):
                        ui.label(key).classes('sensor-label')
                        refs[key] = ui.label('—').classes('sensor-value')

        # ─── Accel ───
        with ui.element('div').classes('sensor-block'):
            ui.label('التسارع · Accel').classes('sensor-block-title')
            with ui.element('div').classes('sensor-rows'):
                for key in ('ax', 'ay', 'az'):
                    with ui.element('div').classes('sensor-row'):
                        ui.label(key).classes('sensor-label')
                        refs[key] = ui.label('—').classes('sensor-value')

    return refs


async def refresh(refs: dict):
    """يُستدعى كل 0.1 ث عندما تكون الصفحة نشطة."""
    s = STATE

    # ─── شريط حالة MQTT ───
    dot = refs['mqtt_dot']
    dot.classes(remove='on off wait')

    if s['connected']:
        dot.classes(add='on')
        refs['mqtt_label'].text = 'متصل · قراءات حية'
    elif 'فشل' in s['reason'] or 'انقطع' in s['reason']:
        dot.classes(add='off')
        refs['mqtt_label'].text = s['reason']
    else:
        dot.classes(add='wait')
        refs['mqtt_label'].text = s['reason']

    if s['total'] == 0:
        refs['mqtt_meta'].text = f'{s["broker"]}:{s["port"]} · لا رسائل بعد'
    else:
        refs['mqtt_meta'].text = (
            f'{s["broker"]}:{s["port"]} · {s["total"]} رسالة'
        )

    # ─── القيم ───
    latest = s['latest']
    if latest is None:
        return

    for i in range(1, 6):
        refs[f'flex{i}'].text = str(latest[f'flex{i}'])

    for key in ('gx', 'gy', 'gz', 'ax', 'ay', 'az'):
        refs[key].text = f'{latest[key]:+.2f}'

    first = s['first_time']
    refs['start'].text   = f'{first} ms' if first is not None else '—'
    refs['now'].text     = f"{latest['time']} ms"
    refs['elapsed'].text = (
        _fmt_duration(latest['time'] - first) if first is not None else '—'
    )


def on_enter():
    """يُستدعى عند الدخول للصفحة (اختياري)."""
    pass