---
title: SIGNO Dashboard
emoji: 🧤
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: Smart Sign Glove Dashboard — Live sensors, AI, Voice
---

# SIGNO · Smart Sign Glove Dashboard

لوحة تحكم لمشروع قفاز الإشارة الذكي — عرض حي، ذكاء اصطناعي، تحويل نص إلى صوت، مستودع ملفات، ودردشة.

## الصفحات

| # | الصفحة | الوصف |
|---|--------|-------|
| 1 | لوحة الحساسات | قراءات MQTT مباشرة من ESP32 |
| 2 | استوديو الذكاء الاصطناعي | جمع بيانات، تدريب، تنبؤ حيّ |
| 3 | تحويل النص إلى صوت | عربي · فرنسي · إنجليزي |
| 4 | مستودع الملفات | رفع وتحميل مشترك |
| 5 | غرفة التواصل | دردشة فورية بين 3 أعضاء |

## التقنيات

- **NiceGUI** — واجهة تفاعلية
- **paho-mqtt** — استقبال بيانات القفاز
- **edge-tts** — تحويل النص إلى صوت
- **scikit-learn** — تصنيف إشارات القفاز

## الاستخدام

1. اختر هويتك من الصفحة الرئيسية
2. تنقّل بين الصفحات من القائمة الجانبية
3. راقب القراءات الحية من القفاز عبر MQTT
</｜｜DSML｜｜ parameter>
</｜｜DSML｜｜ invoke>
</｜｜DSML｜｜ calls>