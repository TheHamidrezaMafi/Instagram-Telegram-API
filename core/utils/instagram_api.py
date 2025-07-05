from instagrapi import Client
import time
import sqlite3
import os
import datetime
from instagrapi.mixins.challenge import ChallengeChoice
from instagrapi.exceptions import LoginRequired
from instagrapi.image_util import prepare_image
import logging
from PIL import Image

class CustomClient(Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request_timeout = 1 # Increase the read timeout to 5 seconds from 1

class insta_util:
    def __init__(self, username=None, password=None, session=None, id=None):
        self.username = username
        self.password = password
        self.id = id
        self.cl = self.init_login(username, password, session)
    def init_login(self, USERNAME=None, PASSWORD=None, session=None):
        logger = logging.getLogger() 
        logging.basicConfig(level=logging.WARNING) #ERROR or CRITICAL or INFO
        cl = CustomClient()
        if session is not None:
            cl.set_settings(session)
            try:
                cl.get_timeline_feed()  # Check if the session is valid
            except LoginRequired:
                logger.info("Session is invalid, need to login via username and password")
                old_session = cl.get_settings()
                cl.set_settings({})
                try:
                    cl.set_uuids(old_session["uuids"])
                    cl.login(USERNAME, PASSWORD)
                except Exception as e:
                    logger.error(f"Login failed: {e}")
                    return None

        else:
            try:
                cl.set_uuids({"username": USERNAME})
                cl.login(USERNAME, PASSWORD)
            except Exception as e:
                logger.error(f"Login failed: {e}")
                return None
        self.id = cl.user_id
        return cl
    
    def get_chats(self):
        try:
            threads = self.cl.direct_threads()
            chats = []
            for thread in threads:
                profile_pic_url = thread.users[0].profile_pic_url if thread.users else None
                chat = {
                    "thread_id": thread.id,
                    "title": thread.named,
                    "participants": [user.username for user in thread.users],
                    "last_message": thread.messages[0] ,
                    "unread_count": thread.is_seen(self.cl.user_id),
                    "profile_pic_url": profile_pic_url
                }
                chats.append(chat)
            return chats
        except Exception as e:
            # print(f"Error fetching chats: {e}")
            return []
    def get_session(self):
        return self.cl.get_settings()
    def get_messages(self, thread_id):
        """Fetch messages from a given thread, return structured data with media URLs."""
        try:
            thread = self.cl.direct_thread(thread_id)
            messages_data = []

            for message in thread.messages:
                msg = {
                    "id": message.id,
                    "timestamp": str(message.timestamp),
                    "sender_id": str(message.user_id),
                    "type": message.item_type,
                    "text": "",
                    "media_url": "",
                    "media_type": "",
                    "post_caption": "",
                    "post_url": "",
                }
                if message.item_type == "text":
                    msg["text"] = message.text

                elif message.item_type == "xma_media_share":
                    # Posts shared (single or album)
                    media_pk = self.cl.media_pk_from_url(str(message.xma_share.video_url).split("'")[0])
                    media_id = self.cl.media_id(media_pk)
                    post = self.cl.media_info(media_id)

                    msg["media_type"] = "post"
                    msg["post_caption"] = post.caption_text
                    msg["post_url"] = f"https://www.instagram.com/p/{post.code}/"

                    if post.media_type != 8:  # Not an album
                        url = post.video_url if post.media_type == 2 else post.thumbnail_url
                        msg["media_url"] = (str(url))
                    else:
                        for resource in post.resources:
                            url = resource.video_url if resource.media_type == 2 else resource.thumbnail_url
                            msg["media_url"] = (str(url))

                elif message.item_type == "media":
                    # Photo or video
                    if message.media.media_type == 1:
                        msg["media_url"] = message.media.thumbnail_url
                        msg["media_type"] = "photo"
                    elif message.media.media_type == 2:
                        msg["media_url"] = message.media.video_url
                        msg["media_type"] = "video"

                elif message.item_type == "voice_media":
                    msg["media_url"] = message.media.audio_url
                    msg["media_type"] = "audio"

                elif message.item_type == "clip":
                    msg["media_url"] = message.clip.video_url
                    msg["media_type"] = "reel"
                    msg["post_caption"] = message.clip.caption_text
                    msg["post_url"] = f"https://www.instagram.com/reel/{message.clip.code}/"

                elif message.item_type == "xma_story_share":
                    # Story share — may include additional handling if needed
                    # msg["media_url"] = message.reel_share.video_url or message.reel_share.image_url
                    # msg["media_type"] = "story"
                    msg["text"] = f"Unsupported message type: {message.item_type}"

                elif message.item_type == "generic_xma":
                    msg["text"] = str(message.xma_share)

                else:
                    msg["text"] = f"Unsupported message type: {message.item_type}"

                messages_data.append(msg)

            return messages_data

        except Exception as e:
            # print(f"Error fetching messages from thread {thread_id}: {e}")
            return []

    def get_chat_metadata(self, thread_id):
        try:
            thread = self.cl.direct_thread(thread_id)
            participants = [user.username for user in thread.users]
            profile_pic_urls = [user.profile_pic_url for user in thread.users]
            return {
                "participants": participants,
                "profile_pic_urls": profile_pic_urls
            }
        except Exception as e:
            # print(f"Error fetching chat metadata for thread {thread_id}: {e}")
            return {
                "participants": [],
                "profile_pic_urls": []
            }
    def get_name(self):
        try:
            username = self.cl.user_info(self.cl.user_id).username
            return username
        except Exception as e:
            # print(f"Error fetching user name: {e}")
            return None
    def get_profile_picture_url(self):
        try:
            return self.cl.user_info(self.cl.user_id).profile_pic_url_hd
        except Exception as e:
            # print(f"Error fetching profile picture URL: {e}")
            return None