#!/usr/bin/env python3

import requests
import boto3
import hashlib
import json
import smtplib
import os


from dotenv import load_dotenv
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from botocore.exceptions import ClientError


def get_secret():
    """Return the user/pass for the workmail account."""

    secret_name = "prod/wottbda/workmail"
    region_name = "us-east-1"

    session = boto3.session.Session()

    client = session.client(
        service_name="secretsmanager",
        region_name="us-east-1",
    )

    get_secret_value_response = client.get_secret_value(SecretId=secret_name)

    secret = json.loads(get_secret_value_response["SecretString"])

    return secret["user"], secret["pass"]


def email(email_recipient, message):
    """Send e-mails to recipients."""

    email_sender = "matt xoxo <matt@geometry.xxx>"
    email_subject = f"EGG DROP!"

    msg = MIMEMultipart()
    msg["From"] = email_sender
    msg["To"] = " ".join(email_recipient)
    msg["Subject"] = email_subject

    text = ""
    text += message
    text += "<br><br>"
    text += "<i><small>you love chickey so get her an egg</i></small>"

    msg.attach(MIMEText(text, "html"))

    server = smtplib.SMTP_SSL("smtp.mail.us-east-1.awsapps.com", 465)
    server.ehlo()
    server.login(*get_secret())

    res = server.sendmail(
        email_sender,
        email_recipient,
        msg.as_string(),
    )

    if not res:
        print("wotd successfully sent")
    else:
        print("wotd failed to send")


# Load environment variables
load_dotenv()


def checksum(x):
    y = json.dumps(x)
    return hashlib.md5(y.encode()).hexdigest()


def get_result_path():
    return os.path.expanduser("~/egg-drop.txt")


def save_result(x):
    with open(get_result_path(), "w") as hash_file:
        hash_file.write(x)


def get_previous_result():
    result_path = get_result_path()
    if not os.path.exists(result_path):
        return None
    with open(result_path, "r") as hash_file:
        return hash_file.read().strip()


def check_for_eggs():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    }
    response = requests.get("https://danielhalksworth.com/", headers=headers)

    if response.status_code != 200:
        raise SystemExit(1)

    print("Successfully retrieved the website.")

    # Parse the HTML content
    soup = BeautifulSoup(response.content, "html.parser")

    # Find all h2 elements with class woocommerce-loop-product__title
    product_titles = soup.find_all("h2", class_="woocommerce-loop-product__title")

    try:
        description = (
            soup.find("div", class_="page-description")
            .find("span")
            .get_text(strip=True)
        )
    except:
        description = "n/a"

    paintings = sorted(
        title.find("a").get_text(strip=True)
        for title in product_titles
        if title.find("a")
    )

    paintings = [description] + paintings

    # Calculate MD5 checksum
    md5_hash = checksum(paintings)

    # Get previous result
    previous_hash = get_previous_result()

    if md5_hash == previous_hash:
        raise SystemExit()

    print("Changes detected!")

    email(["matt@worldshadowgovernment.com"], "Go to https://danielhalksworth.com/")

    save_result(md5_hash)
