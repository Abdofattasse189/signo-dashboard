# mqtt_client.py
"""MQTT + الحالة المشتركة."""
import json
import time
import uuid
from collections import deque

import paho.mqtt.client as mqtt


BROKER      = 'broker.hivemq.com'
PORT        = 1883
TOPIC       = 'signo_v1_morocco_fattasse_2026'
MAX_SAMPLES = 50
CLIENT_ID   = f'signo_dash_{uuid.uuid4().hex[:8]}'


DATA = deque(maxlen=MAX_SAMPLES)

STATE = {
    'connected':    False,
    'reason':       'جارٍ الاتصال...',
    'latest':       None,
    'first_time':   None,
    'total':        0,
    'parse_errors': 0,
    'last_raw':     None,
    'last_arrival': 0.0,
    'broker':       BROKER,     # ← جديد (للصفحة)
    'port':         PORT,       # ← جديد
}

client = None


def _i(v, d=0):
    try: return int(float(v))
    except (TypeError, ValueError): return d

def _f(v, d=0.0):
    try: return float(v)
    except (TypeError, ValueError): return d


def _on_connect(c, u, flags, reason_code, *a, **k):
    try: code = int(reason_code)
    except (TypeError, ValueError): code = getattr(reason_code, 'value', -1)
    if code == 0:
        STATE['connected'] = True
        STATE['reason']    = 'متصل'
        c.subscribe(TOPIC, qos=0)
        print(f'[MQTT] connected · SUBSCRIBED -> {TOPIC}', flush=True)
    else:
        STATE['connected'] = False
        STATE['reason']    = f'فشل ({reason_code})'


def _on_disconnect(c, u, *a, **k):
    STATE['connected'] = False
    STATE['reason']    = 'انقطع الاتصال'


def _on_message(c, u, msg):
    raw = msg.payload.decode('utf-8', errors='replace')
    STATE['last_raw']     = raw
    STATE['last_arrival'] = time.monotonic()
    STATE['total']       += 1

    try:
        p = json.loads(raw)
    except json.JSONDecodeError:
        STATE['parse_errors'] += 1
        return

    t = _i(p.get('time'))

    packet = {
        'time':  t,
        'flex1': _i(p.get('flex1')), 'flex2': _i(p.get('flex2')),
        'flex3': _i(p.get('flex3')), 'flex4': _i(p.get('flex4')),
        'flex5': _i(p.get('flex5')),
        'gx':    _f(p.get('gx')), 'gy': _f(p.get('gy')), 'gz': _f(p.get('gz')),
        'ax':    _f(p.get('ax')), 'ay': _f(p.get('ay')), 'az': _f(p.get('az')),
    }

    DATA.append(packet)
    STATE['latest'] = packet

    if STATE['first_time'] is None:
        STATE['first_time'] = t


def start():
    global client
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=CLIENT_ID)
    except AttributeError:
        client = mqtt.Client(client_id=CLIENT_ID)

    client.on_connect    = _on_connect
    client.on_disconnect = _on_disconnect
    client.on_message    = _on_message
    client.reconnect_delay_set(min_delay=1, max_delay=10)

    try:
        client.connect_async(BROKER, PORT, keepalive=60)
        client.loop_start()
        print(f'[MQTT] loop_start() · client_id={CLIENT_ID}', flush=True)
    except Exception as e:
        STATE['reason'] = f'فشل البدء: {e}'


def stop():
    if client:
        try:
            client.loop_stop()
            client.disconnect()
        except Exception:
            pass