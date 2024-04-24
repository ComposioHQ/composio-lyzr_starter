#!/usr/bin/env python
from dotenv import load_dotenv
load_dotenv()
from lyzer.lyzr import Lyzrbase
from flask import Flask, request
import os

<<<<<<< HEAD
=======
from dotenv import load_dotenv
from flask import Flask, request

from src.lyzr.lyzr import Lyzrbase

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize Flask app
>>>>>>> 6bba9b7 (removed jupyter notebook)
app = Flask(__name__)

TRIGGER_ID = os.environ.get("TRIGGER_ID")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

if TRIGGER_ID is None or CHANNEL_ID is None:
    print("Please set TRIGGER_ID and CHANNEL_ID environment variables in the .env file")
    exit(1)


def run_lyzr(topic: str):
    inputs = {"topic": topic}
    Lyzrbase.main(inputs)


async def async_run_lyzr(channel, text, user):
    if channel == CHANNEL_ID:
        run_lyzr(text)
    return "Lyzr run initiated", 200

@app.route("/", methods=["POST"])
async def webhook():
    payload = request.json
    print("Payload received", payload)

    print("Received payload:", payload)

    message_payload = payload.get("payload", {})

    channel = message_payload.get("channel", "")
    text = message_payload.get("text", "")
    user = message_payload.get("user", "")

    return await async_run_lyzr(channel, text=text, user=user)


if __name__ == "__main__":
    app.run(port=2000, debug=True)
