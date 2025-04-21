import os
import csv
import openai
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from config import SLACK_TOKEN, OPENAI_API_KEY

slack_client = WebClient(token=SLACK_TOKEN)
openai.api_key = OPENAI_API_KEY

def fetch_channels_by_section(section_name):
    try:
        response = slack_client.conversations_list(types="public_channel,private_channel")
        channels = response["channels"]
        return [channel for channel in channels if channel.get("name", "").startswith(section_name)]
    except SlackApiError as e:
        print(f"Error fetching channels: {e.response['error']}")
        return []

def fetch_messages(channel_id):
    try:
        response = slack_client.conversations_history(channel=channel_id)
        return response["messages"]
    except SlackApiError as e:
        print(f"Error fetching messages for channel {channel_id}: {e.response['error']}")
        return []

def is_office_hour_notes(message):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Determine if the given message is an office hour note."},
                {"role": "user", "content": message},
            ]
        )
        classification = response["choices"][0]["message"]["content"].strip()
        return classification.lower() == "yes"
    except Exception as e:
        print(f"Error with OpenAI API: {e}")
        return False

def save_to_csv(data, filename="office_hour_notes.csv"):
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Channel", "User", "Message"])
        writer.writerows(data)

def main():
    section_name = input("Enter the section name to filter channels: ").strip()
    office_hour_notes = []
    channels = fetch_channels_by_section(section_name)

    for channel in channels:
        print(f"Processing channel: {channel['name']}")
        messages = fetch_messages(channel_id=channel["id"])

        for message in messages:
            if "text" in message and "user" in message:
                is_note = is_office_hour_notes(message["text"])
                if is_note:
                    office_hour_notes.append([
                        channel["name"],
                        message["user"],
                        message["text"]
                    ])

    save_to_csv(office_hour_notes)
    print(f"Saved {len(office_hour_notes)} office hour notes to CSV.")

if __name__ == "__main__":
    main()
