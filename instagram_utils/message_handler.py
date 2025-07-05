from instagrapi import Client
import time
import sqlite3
import os
import requests
import hashlib
import json
import random
import tempfile
import datetime
from instagrapi.mixins.challenge import ChallengeChoice
from instagrapi.exceptions import LoginRequired
from instagrapi.image_util import prepare_image
import logging
from PIL import Image



# -------------------------------
# Initialize Instagram Client
# -------------------------------

USERNAME = "megachat_test3"
PASSWORD = "Megachat_newpass@431"

logger = logging.getLogger() 
logging.basicConfig(level=logging.WARNING) #ERROR or CRITICAL or INFO

class CustomClient(Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request_timeout = 2 # Increase the read timeout to 5 seconds from 1

def login_user():
    cl = CustomClient()
    session_file = "session.json"

    # Load session if it exists
    try:
        cl.load_settings(session_file)
        cl.login(USERNAME, PASSWORD)
        try:
            cl.get_timeline_feed()  # Check if the session is valid
        except LoginRequired:
            logger.info("Session is invalid, need to login via username and password")
            old_session = cl.get_settings()
            cl.set_settings({})
            cl.set_uuids(old_session["uuids"])
            cl.login(USERNAME, PASSWORD)
    except Exception as e:
        logger.info("Couldn't login user using session information: %s" % e)
        logger.info("Attempting to login via username and password")
        try:
            if cl.login(USERNAME, PASSWORD):
                cl.dump_settings(session_file)
        except Exception as e:
            logger.error("Couldn't login user using username and password: %s" % e)
            raise Exception("Couldn't login user with either password or session")

    return cl

def add_delays(client, min_delay, max_delay):
    client.delay_range = [min_delay, max_delay]

# -------------------------------
# Core Features
# -------------------------------

def process_message_json(message_json):
    # Example placeholder - you can do anything with this JSON
    print(json.dumps(message_json, indent=2))
    # Here you could send it to a webhook, log it, etc.

def handle_messages():
    try:
        threads_list = cl.direct_threads(selected_filter="unread")
        for thread in threads_list:
            message = thread.messages[0]
            user_id = message.user_id

            message_json = {
                "thread_id": thread.id,
                "message_id": message.id,
                "user_id": user_id,
                "timestamp": str(message.timestamp),
                "item_type": None,
                "text": "",
                "post_url": None,
                "post_caption": None,
                "media_urls": [],
                "media_url": None,
                "media_type": None,
            }

            if message.item_type == 'text':
                message_json["text"] = message.text

            elif message.item_type == 'media':
                if message.media.media_type == 1:
                    message_json["media_url"] = message.media.thumbnail_url
                    message_json["media_type"] = "photo"
                elif message.media.media_type == 2:
                    message_json["media_url"] = message.media.video_url
                    message_json["media_type"] = "video"

            elif message.item_type == 'voice_media':
                audio_path = cl.track_download_by_url(message.media.audio_url, str(message.id), media_folder)
                message_json["media"] = {
                    "media_type": "audio",
                    "path": audio_path
                }

            elif message.item_type == 'xma_media_share':
                # Posts shared (single or album)
                media_pk = cl.media_pk_from_url(str(message.xma_share.video_url).split("'")[0])
                media_id = cl.media_id(media_pk)
                post = cl.media_info(media_id)

                message_json["media_type"] = "post"
                message_json["post_caption"] = post.caption_text
                message_json["post_url"] = f"https://www.instagram.com/p/{post.code}/"
                message_json["media_urls"] = []

                if post.media_type != 8:  # Not an album
                    url = post.video_url if post.media_type == 2 else post.thumbnail_url
                    message_json["media_urls"].append(str(url))
                else:
                    for resource in post.resources:
                        url = resource.video_url if resource.media_type == 2 else resource.thumbnail_url
                        message_json["media_urls"].append(str(url))

            elif message.item_type == 'clip':
                # Reels shared
                message_json["media_url"] = message.clip.video_url
                message_json["media_type"] = "reel"
                message_json["post_caption"] = message.clip.caption_text
                message_json["post_url"] = f"https://www.instagram.com/reel/{message.clip.code}/"

            elif message.item_type == 'generic_xma':
                message_json["media"] = {
                    "media_type": "generic_xma",
                    "details": str(message.xma_share)
                }

            elif message.item_type == 'xma_story_share':
                message_json["media"] = {
                    "media_type": "story_share",
                    "details": str(message.reel_share)
                }

            else:
                print("Unknown message type:", message.item_type)

            cl.direct_message_seen(thread_id=thread.id, message_id=message.id)

            # Pass the structured message to another handler
            process_message_json(message_json)

    except Exception as e:
        print(f"Error handling unread messages: {e}")

    try:
        pending_threads = cl.direct_pending_inbox()
        for thread in pending_threads:
            for message in thread.messages:
                user_id = message.user_id
                cl.direct_message_seen(thread_id=thread.id, message_id=message.id)

                message_json = {
                    "thread_id": thread.id,
                    "message_id": message.id,
                    "user_id": user_id,
                    "timestamp": str(message.timestamp),
                    "item_type": message.item_type,
                    "text": getattr(message, "text", None)
                }

                process_message_json(message_json)

    except Exception as e:
        print(f"Error handling pending messages: {e}")


# -------------------------------
# Script Execution
# -------------------------------
if __name__ == "__main__":

    cl = login_user()
    add_delays(cl, 0.1, 2) # Add delays between requests


    start_time = time.time()
    while True:
        try:
            handle_messages()
            # time.sleep(5)  # Check for new messages every 5 seconds
            print(f"Running for {time.time() - start_time} seconds")
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)  # Wait longer if there's an error