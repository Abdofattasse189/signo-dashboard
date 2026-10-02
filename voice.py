# voice.py
"""صفحة تحويل النص إلى صوت — عربي · فرنسي · إنجليزي."""
import base64
import io

from nicegui import ui

import edge_tts


TITLE = 'تحويل النص إلى صوت'
ICON  = 'record_voice_over'
DESC  = ('اكتب أي نص بالعربية أو الفرنسية أو الإنجليزية، اختر صوتاً، '
         'واسمع الترجمة الصوتية فوراً. يمكنك تحميل الملف الصوتي بضغطة.')

# ═══════════════════════════════════════════════════════════
# الأصوات المتوفرة (Microsoft Edge TTS — مجاني)
# ═══════════════════════════════════════════════════════════
VOICES = {
    'عربي · جمال (المغرب)':        'ar-MA-JamalNeural',
    'عربي · منى (المغرب)':         'ar-MA-MounaNeural',
    'عربي · حامد (السعودية)':       'ar-SA-HamedNeural',
    'عربي · زارية (السعودية)':      'ar-SA-ZariyahNeural',
    'عربي · شاكر (مصر)':            'ar-EG-ShakirNeural',
    'عربي · سلمى (مصر)':            'ar-EG-SalmaNeural',
    'فرنسي · هنري (رجل)':           'fr-FR-HenriNeural',
    'فرنسي · دينيس (امرأة)':        'fr-FR-DeniseNeural',
    'إنجليزي · Guy (أمريكي)':       'en-US-GuyNeural',
    'إنجليزي · Jenny (أمريكي)':     'en-US-JennyNeural',
    'إنجليزي · Ryan (بريطاني)':     'en-GB-RyanNeural',
    'إنجليزي · Sonia (بريطاني)':    'en-GB-SoniaNeural',
}

DEFAULT_VOICE = 'عربي · جمال (المغرب)'


# ═══════════════════════════════════════════════════════════
# توليد الصوت
# ═══════════════════════════════════════════════════════════
async def _generate(text: str, voice_id: str,
                    rate: int = 0, pitch: int = 0, volume: int = 0) -> bytes:
    communicate = edge_tts.Communicate(
        text, voice_id,
        rate=f'{rate:+d}%',
        pitch=f'{pitch:+d}Hz',
        volume=f'{volume:+d}%',
    )
    buf = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk.get('type') == 'audio':
            buf.write(chunk['data'])
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════
# الواجهة
# ═══════════════════════════════════════════════════════════
def build() -> dict:
    refs = {
        'audio_state': {'data': b'', 'name': 'voice.mp3'},
    }

    ui.label('03').classes('page-number')
    ui.label(TITLE).classes('page-title')
    ui.element('div').classes('divider')
    ui.label(DESC).classes('hint-box')

    with ui.element('div').classes('voice-layout'):

        # ─── النص ───
        with ui.element('div').classes('voice-block'):
            ui.label('النص').classes('voice-block-title')
            with ui.element('div').classes('voice-block-body'):
                refs['text'] = (
                    ui.textarea(placeholder='اكتب النص هنا...')
                    .props('borderless autogrow rows=5')
                    .classes('voice-textarea')
                )

        # ─── الإعدادات ───
        with ui.element('div').classes('voice-block'):
            ui.label('الصوت').classes('voice-block-title')
            with ui.element('div').classes('voice-block-body'):
                refs['voice'] = (
                    ui.select(options=list(VOICES.keys()),
                              value=DEFAULT_VOICE,
                              label='اختر الصوت')
                    .props('borderless')
                    .classes('voice-select')
                )

                with ui.element('div').classes('voice-slider-row'):
                    ui.label('السرعة').classes('voice-slider-label')
                    refs['rate'] = (
                        ui.number(value=0, min=-50, max=100, step=5, format='%d')
                        .props('borderless dense')
                        .classes('voice-number')
                    )
                    ui.label('٪').classes('voice-slider-unit')

                with ui.element('div').classes('voice-slider-row'):
                    ui.label('النبرة').classes('voice-slider-label')
                    refs['pitch'] = (
                        ui.number(value=0, min=-50, max=50, step=5, format='%d')
                        .props('borderless dense')
                        .classes('voice-number')
                    )
                    ui.label('Hz').classes('voice-slider-unit')

                with ui.element('div').classes('voice-slider-row'):
                    ui.label('الصوت').classes('voice-slider-label')
                    refs['volume'] = (
                        ui.number(value=0, min=-50, max=100, step=10, format='%d')
                        .props('borderless dense')
                        .classes('voice-number')
                    )
                    ui.label('٪').classes('voice-slider-unit')

        # ─── النتيجة ───
        with ui.element('div').classes('voice-block voice-result'):
            ui.label('النتيجة').classes('voice-block-title')
            with ui.element('div').classes('voice-block-body'):

                async def generate():
                    text = (refs['text'].value or '').strip()
                    if not text:
                        ui.notify('اكتب نصاً أولاً', type='warning', position='top')
                        return

                    voice_label = refs['voice'].value
                    voice_id = VOICES.get(voice_label)
                    if not voice_id:
                        ui.notify('اختر صوتاً', type='warning', position='top')
                        return

                    refs['status'].text = 'جارٍ التوليد...'
                    refs['status'].classes(remove='ok err')
                    refs['generate_btn'].props('loading')

                    try:
                        audio = await _generate(
                            text, voice_id,
                            rate=int(refs['rate'].value or 0),
                            pitch=int(refs['pitch'].value or 0),
                            volume=int(refs['volume'].value or 0),
                        )
                    except Exception as e:
                        refs['status'].text = f'فشل: {e}'
                        refs['status'].classes(add='err')
                        refs['generate_btn'].props(remove='loading')
                        ui.notify('فشل التوليد', type='negative', position='top')
                        return

                    refs['generate_btn'].props(remove='loading')

                    if not audio:
                        refs['status'].text = 'لم يُنتج أي صوت'
                        refs['status'].classes(add='err')
                        return

                    b64 = base64.b64encode(audio).decode()
                    refs['audio_state']['data'] = audio
                    refs['audio_state']['name'] = f'voice_{voice_id}.mp3'

                    refs['player'].source = f'data:audio/mp3;base64,{b64}'
                    refs['player'].update()

                    refs['download_btn'].enable()
                    refs['status'].text = f'✓ جاهز · {len(audio) // 1024} KB'
                    refs['status'].classes(remove='err').classes(add='ok')
                    ui.notify('تم التوليد', type='positive', position='top')

                def download():
                    data = refs['audio_state']['data']
                    if not data:
                        return
                    ui.download(data, refs['audio_state']['name'])

                refs['player'] = ui.audio('').classes('voice-player')

                with ui.element('div').classes('voice-actions'):
                    refs['generate_btn'] = ui.button(
                        'توليد الصوت', icon='play_arrow', on_click=generate
                    ).props('flat no-caps').classes('voice-generate-btn')

                    refs['download_btn'] = ui.button(
                        'تحميل', icon='download', on_click=download
                    ).props('flat no-caps').classes('voice-download-btn')

                refs['download_btn'].disable()

                refs['status'] = ui.label('').classes('voice-status')

    return refs


async def refresh(refs):
    pass


def on_enter():
    pass