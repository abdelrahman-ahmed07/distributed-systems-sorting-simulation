import os

# عنوان البروكر. localhost لو شغال على نفس جهازك.
# لو زميلك بيتصل من جهاز تاني، هيحط IP جهازك بدل localhost.
BROKER_HOST = os.getenv("MQTT_HOST", "localhost")
BROKER_PORT = int(os.getenv("MQTT_PORT", "1883"))

# كل كام ثانية العميل يبعت ping للبروكر عشان يثبت إنه لسه حي.
KEEPALIVE_SECONDS = 60

# مدة الانتظار بين محاولات إعادة الاتصال (بالثواني): من 1 لحد 30.
RECONNECT_MIN_DELAY = 1
RECONNECT_MAX_DELAY = 30