from braingeneers.iot import messaging
import uuid


def respondToCommand(topic: str, message: dict):
    print("Received:", str, dict)


mb = messaging.MessageBroker(str(uuid.uuid4))

mb.subscribe_message(f"devices/#", respondToCommand)

mb.publish_message("devices/foo", None)