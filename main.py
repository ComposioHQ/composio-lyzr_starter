#!/usr/bin/env python
import logging
import os

from dotenv import load_dotenv
from flask import Flask, request

from src.lyzr.lyzr import Lyzrbase

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize Flask app
app = Flask(__name__)

# Retrieve environment variables
TRIGGER_ID = os.environ.get("TRIGGER_ID")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

# Check if necessary environment variables are set
if TRIGGER_ID is None or CHANNEL_ID is None:
    logging.error(
        "Please set TRIGGER_ID and CHANNEL_ID environment variables in the .env file"
    )
    exit(1)


def run_lyzr(topic: str):
    """Function to run Lyzr analysis on a given topic."""
    lyzr_instance = Lyzrbase(topic=topic)
    lyzr_instance.main()


async def async_run_lyzr(channel, text, user):
    """Asynchronously run Lyzr if the message is from the specified channel."""
    if channel == CHANNEL_ID:
        run_lyzr(text)
    return "Lyzr run initiated", 200


@app.route("/", methods=["POST"])
async def webhook():
    """Webhook to handle POST requests."""
    payload = request.json
    if payload is None:
        logging.error("Received payload is not in JSON format.")
        return "Invalid payload format", 400
    logging.info(f"Payload received: {payload}")

    message_payload = payload.get("payload", {})

    channel = message_payload.get("channel", "")
    text = message_payload.get("text", "")
    user = message_payload.get("user", "")

    return await async_run_lyzr(channel, text=text, user=user)


if __name__ == "__main__":
    app.run(port=2000, debug=True)
