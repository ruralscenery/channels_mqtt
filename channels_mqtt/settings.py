from django.conf import settings

MQTT_HOST = settings.MQTT_HOST
MQTT_PORT = settings.MQTT_PORT
MQTT_USERNAME = settings.MQTT_USERNAME
MQTT_PASSWORD = settings.MQTT_PASSWORD
MQTT_CLIENT_ID = "mqtt.client"
MQTT_PROTOCOL_NAME = settings.MQTT_PROTOCOL_NAME if hasattr(settings, "MQTT_PROTOCOL_NAME") else "mqtt"

MQTT_TOPIC = "mqtt.top"
MQTT_PUBLISH = "mqtt.pub"
MQTT_SUBSCRIBE = "mqtt.sub"
MQTT_UNSUBSCRIBE = "mqtt.unsub"
