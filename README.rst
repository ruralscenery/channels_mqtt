Channels Mqtt
=============

Mqtt Client for Channels Worker that bridge paho mqtt client to channels consumers

Dependencies
------------

Required Packages::

    channels 2.x
    paho-mqtt 1.3.1

Installation
------------

Install with pip::

    pip install channels_mqtt

Settings
--------
Edit your Django Settings::

    INSTALLED_APPS = [
        ...
        'channels_mqtt',
        ...
    ]

    MQTT_HOST = "ip.mqtt.host"
    MQTT_PORT = 1883
    MQTT_USERNAME = "username"
    MQTT_PASSWORD = "password"

In your channels routing.py::

    application = ProtocolTypeRouter({
        "mqtt": YourConsumer,
    })

Start Channels Mqtt Worker::

    manage runmqttworker

Usage
-----

Write YourConsumer::

    class YourConsumer(SyncConsumer):
        TOPICS = [('my_topic', my_qos), ]

        def mqtt_sub(self, event):
            logger.info("consumer SUB {}".format(event))

        def mqtt_pub(self, event):
            logger.info("consumer PUB {}".format(event))

        def mqtt_top(self, event):
            logger.info("consumer TOP {}".format(event))
            payload = json.dumps(event['text']['payload'])
            self.send({'type': channels_mqtt.settings.MQTT_PUBLISH,
                       'text': {'topic': 'my_topic',
                                'payload': payload,
                                'qos': 0,
                                'retain': False})
