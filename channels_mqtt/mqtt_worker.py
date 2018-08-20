
import asyncio
import logging

import os
import asyncio
import functools
import logging
import time
import signal
import json

import paho.mqtt.client as mqtt

from asgiref.server import StatelessServer

from channels_mqtt import settings

logger = logging.getLogger(__name__)

async def mqtt_send(future, channel_layer, channel, event):
    result = await channel_layer.send(channel, event)
    future.set_result(event)
    # future.set_result(result)


class Server(StatelessServer):
    """
    MQTT Channels
    """

    software_name = "chmqttbgi"
    # software_version = chmqttbgi.__version__

    def __init__(self, application, channel_layer, host=None, port=None, username=None, password=None,
            client_id=None, topics_subscription=None, mqtt_channel_name = None,
            mqtt_top=None, mqtt_sub=None, mqtt_unsub=None, mqtt_pub=None):
        super().__init__(application, 1)

        self.channel = settings.MQTT_PROTOCOL_NAME
        self.channel_layer = channel_layer
        self.host = host or settings.MQTT_HOST
        self.port = port or settings.MQTT_PORT
        self.client_id = client_id or settings.MQTT_CLIENT_ID
        self.client = mqtt.Client(client_id=self.client_id, clean_session=False, userdata={
            "server": self,
            "channel": self.channel_layer,
            "host": self.host,
            "port": self.port,
        })
        self.username = username or settings.MQTT_USERNAME
        self.password = password or settings.MQTT_PASSWORD
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        self.mqtt_channel_name = mqtt_channel_name or settings.MQTT_PROTOCOL_NAME
        self.mqtt_top = mqtt_top or settings.MQTT_TOPIC
        self.mqtt_pub = mqtt_pub or settings.MQTT_PUBLISH
        self.mqtt_sub = mqtt_sub or settings.MQTT_SUBSCRIBE
        self.mqtt_unsub = mqtt_unsub or settings.MQTT_UNSUBSCRIBE

        # self.topics_subscription = topics_subscription or [("#", 2),]
        self.topics_subscription = topics_subscription or application.application_mapping[self.mqtt_channel_name].TOPICS
        assert isinstance(self.topics_subscription, list), "Topic subscription must be a list with (topic, qos)"

    ### Mainloop and handling
    async def handle(self):
        """
        Main loop. Long-polls and dispatches updates to handlers.
        """
        self.stop = False
        loop = asyncio.get_event_loop()
        self.loop = loop

        # for signame in ('SIGINT', 'SIGTERM'):
        #     loop.add_signal_handler(
        #             getattr(signal, signame),
        #             functools.partial(self.stop_server, signame)
        #         )

        print("Event loop running forever, press Ctrl+C to interrupt.")
        print("pid %s: send SIGINT or SIGTERM to exit." % os.getpid())

        # tasks = asyncio.gather(*[
        #         asyncio.ensure_future(self.client_pool_start()),
        #         asyncio.ensure_future(self.client_pool_message()),
        #     ])
        tasks = [
                asyncio.ensure_future(self.client_pool_start()),
                asyncio.ensure_future(self.client_pool_message()),
            ]
        await asyncio.wait(tasks)

        self.stop = True
        self.client.disconnect()
        logger.info("handle end")

    async def application_send(self, scope, message):
        """
        Receives outbound sends from applications and handles them.
        """
        print("app_send {}, {}".format(scope, message))
        await self._mqtt_receive(message)

    def _on_connect(self, client, userdata, flags, rc):
        logger.info("Connected with status {}".format(rc))
        client.unsubscribe("#")
        client.subscribe(self.topics_subscription)

    def _on_disconnect(self, client, userdata, rc):
        logger.info("Disconnected")
        if not self.stop:
            j = 3
            for i in range(j):
                client.unsubscribe("#")
                logger.info("Trying to reconnect")
                try:
                    client.reconnect()
                    logger.info("Reconnected")
                    break
                except Exception as e:
                    if i < j:
                        logger.warn(e)
                        time.sleep(1)
                        continue
                    else:
                        raise

    def _mqtt_send_got_result(self, future):
        logger.info("Sending message to MQTT channel, with result\r\n%s", future.result())
        logger.debug("Sending message to MQTT channel, with result\r\n%s", future.result())

    def _on_message(self, client, userdata, message):
        logger.debug("Received message from topic {}".format(message.topic))
        payload = message.payload.decode("utf-8")
        logger.info("on message %s, %s", message.topic, payload)
        try:
            payload = json.loads(payload)
        except:
            logger.debug("Payload is nos a JSON Serializable\r\n%s", payload)
            pass

        msg = {
            "topic": message.topic,
            "payload": payload,
            "qos": message.qos,
            "host": userdata["host"],
            "port": userdata["port"],
        }

        try:
            future = asyncio.Future(loop=self.loop)
            asyncio.ensure_future(
                self._mqtt_receive({"type": self.mqtt_top, "text": msg}),
                # mqtt_send(
                #     future,
                #     self.channel_layer,
                #     self.mqtt_channel_name,
                #     {
                #         "type": self.mqtt_top,
                #         "text": msg
                #     }),
                loop=self.loop
            )

            future.add_done_callback(self._mqtt_send_got_result)

        except Exception as e:
            logger.error("Cannot send message {}".format(msg))
            logger.exception(e)
            print(e)

    async def _mqtt_receive(self, msg):
        """
        Receive a message from the Channel
        mqtt.top: received messages for topics
        mqtt.pub: publish to mqtt broker
        mqtt.sub: subcribe to mqtt broker
        mqtt.unsub: unsubscribe to mqtt broker
        """
        if msg['type'] == self.mqtt_top:
            scope = {"type": self.mqtt_channel_name, "channel": self.channel_layer}
            instance_queue = self.get_or_create_application_instance(self.channel_layer, scope)
            # Run the message into the app
            await instance_queue.put(msg)
        elif msg['type'] == self.mqtt_sub:
            payload = msg['text']

            if not isinstance(payload, dict):
                payload = json.loads(payload)

            logger.info("Receive a message with payload: %s", msg)
            self.client.subscribe(
                    payload['topic'],
                    qos=payload.get('qos', 2),
                    )
        elif msg['type'] == self.mqtt_pub:
            payload = msg['text']

            if not isinstance(payload, dict):
                payload = json.loads(payload)
            if isinstance(payload['payload'], dict):
                payload_body = json.dumps(payload['payload'])
            else:
                payload_body = payload['payload']

            logger.info("Receive a message with payload: %s", msg)
            self.client.publish(
                    payload['topic'],
                    payload_body,
                    qos=payload.get('qos', 2),
                    retain=False)
        elif msg['type'] == self.mqtt_unsub:
            payload = msg['text']

            if not isinstance(payload, dict):
                payload = json.loads(payload)

            logger.info("Receive a message with payload: %s", msg)
            self.client.unsubscribe(payload['topic'])

    async def client_pool_start(self):
        # Loop to receive MQTT messages
        if self.username:
            self.client.username_pw_set(username=self.username, password=self.password)

        # self.client.connect(self.host, self.port)
        self.client.connect_async(self.host, self.port)
        self.client.loop_start()

        logger.info("Starting loop")

        # while True:
        #     self.client.loop(0.1)
        #     logger.debug("Restarting loop")
        #     await asyncio.sleep(0.1)

    async def client_pool_message(self):
        logger.info("Loop of reception of messages")

        while True:
            try:
                logger.info("Wait to receive a message from the channel %s", self.mqtt_channel_name)
                result = await self.channel_layer.receive(self.mqtt_channel_name)
                await self._mqtt_receive(result)
                # await asyncio.sleep(0.01)
            except Exception as e:
                logger.exception("")

        logger.info("client_pool_message end")
    # def stop_server(self, signum):
    #     logger.info("Received signal {}, terminating".format(signum))
    #     self.stop = True
    #     for task in asyncio.Task.all_tasks():
    #         task.cancel()
    #     self.loop.stop()
