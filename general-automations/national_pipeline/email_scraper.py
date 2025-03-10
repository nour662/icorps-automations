import mailbox
import pandas as pd
from email.utils import parsedate_tz, mktime_tz, parseaddr
from datetime import datetime
import chardet
from bs4 import BeautifulSoup
import re

def decode_body(body_bytes):
    detected_encoding = chardet.detect(body_bytes)
    encoding = detected_encoding['encoding']
    try:
        return body_bytes.decode(encoding)
    except (UnicodeDecodeError, TypeError):
        return body_bytes.decode('ISO-8859-1', errors='replace')

def clean_html(body):
    soup = BeautifulSoup(body, 'html.parser')
    return soup.get_text()

def remove_quoted_text(body):
    body = re.sub(r"(?<=\n)On.*wrote:\n", "", body)
    body = re.sub(r"(?<=\n)>.*", "", body)
    return body.strip()

def extract_email_and_name(address):
    name, email = parseaddr(address)
    return name, email

mbox = mailbox.mbox('/Users/nour.ahmed/Downloads/Takeout/Mail/tmp.mbox')
data = []
counter = 0

for message in mbox:
    subject = message['subject']
    sender_name, sender_email = extract_email_and_name(message['from'])
    recipient_name, recipient_email = extract_email_and_name(message['to'])
    cc = message.get('cc', '')
    bcc = message.get('bcc', '')

    # Extract only emails from cc and bcc
    cc_emails = [extract_email_and_name(addr)[1] for addr in cc.split(',')] if cc else []
    bcc_emails = [extract_email_and_name(addr)[1] for addr in bcc.split(',')] if bcc else []

    date_str = message['date']
    date_tuple = parsedate_tz(date_str)
    if date_tuple:
        date = datetime.fromtimestamp(mktime_tz(date_tuple))
    else:
        date = None

    body = ""
    if message.is_multipart():
        for part in message.walk():
            content_type = part.get_content_type()
            if content_type == 'text/plain':  
                body_bytes = part.get_payload(decode=True)
                body = decode_body(body_bytes)
                body = remove_quoted_text(body)
                break
            elif content_type == 'text/html':  
                body_bytes = part.get_payload(decode=True)
                body = decode_body(body_bytes)
                body = clean_html(body)
                body = remove_quoted_text(body)
                break
    else:
        body_bytes = message.get_payload(decode=True)
        body = decode_body(body_bytes)

    data.append({
        'subject': subject,
        'sender_name': sender_name,
        'sender_email': sender_email,
        'recipient_name': recipient_name,
        'recipient_email': recipient_email,
        'cc_emails': cc_emails,
        'bcc_emails': bcc_emails,
        'date': date,
        'body': body
    })
    counter += 1
    print(counter)

df = pd.DataFrame(data)
df.to_csv("tmp.csv", index=False)
print(df.head())
