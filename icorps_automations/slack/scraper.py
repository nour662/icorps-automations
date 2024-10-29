import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


client = WebClient(token=os.getenv("token"))

def get_channel_ids():
    try:
        response = client.conversations_list(types="public_channel,private_channel")
        channels = response["channels"]
        return [channel["id"] for channel in channels]
    except SlackApiError as e:
        print(f"Error fetching channels: {e.response['error']}")
        return []

def get_messages(channel_id):
    try:
        response = client.conversations_history(channel=channel_id)
        messages = response["messages"]
        return messages
    except SlackApiError as e:
        print(f"Error fetching messages from channel {channel_id}: {e.response['error']}")
        return []

all_messages = {}
channel_ids = get_channel_ids()

for channel_id in channel_ids:
    all_messages[channel_id] = get_messages(channel_id)

# Print or process messages as needed
for channel_id, messages in all_messages.items():
    print(f"Messages from channel {channel_id}:")
    for msg in messages:
        print(msg["text"])
