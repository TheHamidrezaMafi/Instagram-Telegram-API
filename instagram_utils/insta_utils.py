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
import pytesseract
from PIL import Image

# -------------------------------
# Challenge Code Handler
# -------------------------------
def get_code_from_sms(username):
    """Prompt the user to enter the SMS code."""
    return input("Enter the SMS code: ")

def challenge_code_handler(username, choice):
    """Handle Instagram's challenge verification."""
    if choice == ChallengeChoice.SMS:
        return get_code_from_sms(username)
    elif choice == ChallengeChoice.EMAIL:
        return None
    return False

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
# Database Setup
# -------------------------------
sqlite3.register_adapter(datetime.datetime, lambda dt: dt.isoformat())
conn = sqlite3.connect("instagram.db")
c = conn.cursor()

# Create 'users' table
c.execute('''CREATE TABLE IF NOT EXISTS users (
                pk TEXT PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                is_private BOOLEAN,
                profile_pic_url TEXT,
                profile_pic_url_hd TEXT,
                is_verified BOOLEAN,
                media_count INTEGER,
                follower_count INTEGER,
                following_count INTEGER,
                biography TEXT,
                external_url TEXT,
                account_type INTEGER,
                is_business BOOLEAN,
                public_email TEXT,
                contact_phone_number TEXT,
                business_category_name TEXT,
                category_name TEXT,
                city_name TEXT
            )''')

# Create 'posts' table
c.execute('''CREATE TABLE IF NOT EXISTS posts (
                pk TEXT PRIMARY KEY,
                id TEXT,
                code TEXT,
                taken_at TEXT,
                media_type INTEGER,
                thumbnail_url TEXT,
                media_paths TEXT,  -- Stores multiple file paths as a comma-separated string
                caption TEXT,
                like_count INTEGER
            )''')
conn.commit()

# -------------------------------
# Helper Functions
# -------------------------------

def extract_text_from_image(image_path, lang="fas+eng"):
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image, lang=lang)
        return text
    except Exception as e:
        return f"Error processing image: {e}"

def download_media(url, filename, folder, media_type):
    """Helper function to download media based on type."""
    if media_type == 1:  # Image
        return cl.photo_download_by_url(url, filename, folder)
    elif media_type == 2:  # Video
        return cl.video_download_by_url(url, filename, folder)
    elif media_type == 8:  # Album
        return cl.album_download_by_urls(url, folder)
    elif media_type == 15:  # IGTV
        return cl.igtv_download_by_url(url, filename, folder)
    elif media_type == 16:  # Reels Clip
        return cl.clip_download_by_url(url, filename, folder)
    else:
        return None

def save_user_info_in_database(user):
    """Stores Instagram user info in the database."""
    c.execute('''INSERT OR REPLACE INTO users 
                 (pk, username, full_name, is_private, profile_pic_url, profile_pic_url_hd, 
                  is_verified, media_count, follower_count, following_count, biography, 
                  external_url, account_type, is_business, public_email, 
                  contact_phone_number, business_category_name, category_name, city_name) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (user.pk, user.username, user.full_name, user.is_private, 
               str(user.profile_pic_url), str(user.profile_pic_url_hd), 
               user.is_verified, user.media_count, user.follower_count, 
               user.following_count, user.biography, user.external_url, 
               user.account_type, user.is_business, user.public_email, 
               user.contact_phone_number, user.business_category_name, 
               user.category_name, user.city_name))
    conn.commit()

def get_post_metadata(message_xma_share):
   """Download media from a shared post."""
   # Set the folder to save media
   media_folder = os.path.join("media", "temp_posts")
   os.makedirs(media_folder, exist_ok=True)  # Ensure the folder exists

   metadata = []
   post_data = {
      "title": message_xma_share.title,
      "video_url": str(message_xma_share.video_url),
      "preview_url": str(message_xma_share.preview_url),
      "header_icon_url": str(message_xma_share.header_icon_url),
      "header_title": message_xma_share.header_title_text,
      "media": []
   }

   # Generate a unique filename using the media ID and timestamp
   media_id = message_xma_share.preview_media_fbid or "unknown_id"
   timestamp = int(time.time())  # Use the current timestamp for uniqueness
   filename = f"{media_id}_{timestamp}.mp4" if message_xma_share.video_url else f"{media_id}_{timestamp}.jpg"

   # Determine the media URL
   media_url = str(message_xma_share.video_url) if message_xma_share.video_url else str(message_xma_share.preview_url)

   # Download the media
   saved_path = download_media(media_url, filename, media_folder, 2 if message_xma_share.video_url else 1)

   if saved_path:
      post_data["media"].append({
         "url": media_url,
         "local_path": saved_path
      })

   metadata.append(post_data)
   print(metadata)
   return metadata

def process_post(post, media_folder):
    """
    Processes an Instagram post, downloads media, and inserts data into the database.
    
    :param post: Instagram post object
    :param media_folder: Directory where media files should be saved
    :param c: SQLite cursor object for executing queries
    :param conn: SQLite connection object for committing transactions
    """
    media_paths = []
    
    # Check if the post has multiple media items (album)
    if post.media_type != 8:  # 8 means it's an album
        filename = f"{post.pk}"
        media_url = str(post.video_url if post.media_type == 2 else post.thumbnail_url)
        saved_path = download_media(media_url, filename, media_folder, post.media_type)
        if saved_path:
            media_paths.append(saved_path)
    else:
        for resource in post.resources:
            filename = f"{resource.pk}"
            media_url = str(resource.video_url if resource.media_type == 2 else resource.thumbnail_url)
            saved_path = download_media(media_url, filename, media_folder, resource.media_type)
            if saved_path:
                media_paths.append(saved_path)
    
    # Insert post data into the database
    c.execute('''INSERT OR IGNORE INTO posts 
                 (pk, id, code, taken_at, media_type, thumbnail_url, media_paths, caption, like_count) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (post.pk, post.id, post.code, post.taken_at, post.media_type, 
               str(post.thumbnail_url), ",".join(map(str, media_paths)), 
               post.caption_text, post.like_count))
    
    conn.commit()
def send_direct_message_user_ids(message, user_ids,media_type="text",path=None):
    """Send a direct message to a user."""
    if media_type == "text":
        cl.direct_send(message, user_ids)
    elif media_type == "photo":
        cl.direct_send_photo(path, user_ids)
    elif media_type == "video":
        cl.direct_send_file(path, user_ids)
    elif media_type == "audio":
        cl.direct_send_file(path, user_ids)
    elif media_type == "file":
        cl.direct_send_file(path, user_ids)
    elif media_type == "post":
        cl.direct_media_share(media_id=path, user_ids=user_ids)
# -------------------------------
# Core Features
# -------------------------------
def handle_messages():
    """Handle unread and pending messages."""
    # Handle unread messages in the main inbox
    try:
        threads_list = cl.direct_threads(selected_filter="unread")
        for thread in threads_list:
            message = thread.messages[0]
            user_id = message.user_id

            # Process message based on type
            if message.item_type == 'text':
                print("Received a text message:", message.text)
            elif message.item_type == 'xma_media_share':
                media_folder = os.path.join("directs_media", user_id)
                os.makedirs(media_folder, exist_ok=True)
                media_id = cl.media_id(cl.media_pk_from_url(str(message.xma_share.video_url).split("'")[0]))
                post = cl.media_info(media_id)
                send_direct_message_user_ids("",[user_id], media_type="post",path=media_id)
                process_post(post, media_folder)
            elif message.item_type == 'media':
                if message.media.media_type == 1:
                    media_folder = os.path.join("directs_media", user_id)
                    os.makedirs(media_folder, exist_ok=True)
                    downloaded_path = cl.photo_download_by_url(str(message.media.thumbnail_url).split("'")[0], str(message.id), media_folder)
                    extracted_text = extract_text_from_image(str(downloaded_path))
                    send_direct_message_user_ids("",[user_id], media_type="photo",path=downloaded_path)  #have to change the aspect ratio in prepare_image to None
                    cl.direct_send(text=extracted_text, user_ids=[user_id])
                elif message.media.media_type == 2:
                    media_folder = os.path.join("directs_media", user_id)
                    os.makedirs(media_folder, exist_ok=True)
                    downloaded_path = cl.video_download_by_url(str(message.media.video_url).split("'")[0], str(message.id), media_folder)
                    # cl.direct_send_video(downloaded_path, user_ids=[user_id])
            elif message.item_type == 'voice_media':
                    media_folder = os.path.join("directs_media", user_id)
                    os.makedirs(media_folder, exist_ok=True)
                    downloaded_path = cl.track_download_by_url(str(message.media.audio_url).split("'")[0], str(message.id), media_folder)
                    send_direct_message_user_ids("",[user_id], media_type="audio",path=downloaded_path)
            elif message.item_type == 'clip':
                    media_folder = os.path.join("directs_media", user_id)
                    media_id = cl.media_id(cl.media_pk_from_url(str(message.clip.video_url).split("'")[0]))
                    os.makedirs(media_folder, exist_ok=True)
                    cl.clip_download_by_url(str(message.clip.video_url).split("'")[0], str(message.id), media_folder)
                    # send_direct_message_user_ids("",[user_id], media_type="post",path=media_id)

            elif message.item_type == 'generic_xma':
                print("Received a generic XMA message:", message.xma_share)
            elif message.item_type == 'xma_story_share':
                    media_folder = os.path.join("directs_media", user_id)
                    print(message.reel_share)
                    
                    # cl.story_download(message.id, str(message.id), media_folder)
                    print("Received a shared story:", message)
            else:
                print("Received an unknown type of message:", message.item_type)

            # Reply to the message
            reply_message = f"from bot: {message.text}"
            cl.direct_message_seen(thread_id=thread.id, message_id=message.id)
            cl.direct_send(text=reply_message, user_ids=[user_id])

    except Exception as e:
        print(f"Error handling unread messages: {e}")

    # Handle messages in the requests (pending inbox)
    try:
        pending_threads = cl.direct_pending_inbox()
        for thread in pending_threads:
            for message in thread.messages:
                user_id = message.user_id
                text = message.text
                reply_message = f"Hello! {text}"
                cl.direct_send(reply_message, [user_id])
                cl.direct_message_seen(thread_id=thread.id, message_id=message.id)
    except Exception as e:
        print(f"Error handling pending messages: {e}")

def retrieve_media_with_username(username):
    """Retrieve posts from a username and store them in the database."""
    user_id = cl.user_id_from_username(username)
    posts = cl.user_medias(user_id)

    media_folder = os.path.join("media", username)
    os.makedirs(media_folder, exist_ok=True)

    for post in posts:
        process_post(post, media_folder)

def download_story_with_username(username):
    """Download stories from a given username."""
    user_id = cl.user_id_from_username(username)
    stories = cl.user_stories(user_id)

    media_folder = os.path.join("media", username)
    os.makedirs(media_folder, exist_ok=True)

    for story in stories:
        filename = f"{story.pk}"
        cl.story_download(story_pk=story.pk, filename=filename, folder=media_folder)

def send_direct_message_with_username(username, message):
    """Send a direct message to a user."""
    user_id = cl.user_id_from_username(username)
    cl.direct_send(message, [user_id])

def comment_on_post_by_id(post_id, comment):
    """Comment on a post."""
    return cl.media_comment(media_id=post_id, text=comment)

def like_post_by_id(post_id):
    """Like a post."""
    return cl.media_like(media_id=post_id)

def get_posts_by_hashtag(hashtag, type='top', amount=10):
    """Retrieve posts by hashtag."""
    posts = []
    if type == 'top':
        posts = cl.hashtag_medias_top(hashtag, amount)
    elif type == 'recent':
        posts = cl.hashtag_medias_recent(hashtag, amount)
    else:
        raise ValueError("Type must be either 'top' or 'recent'")
    media_folder = os.path.join("hashtag", hashtag)
    os.makedirs(media_folder, exist_ok=True)
    for post in posts:
        process_post(post, media_folder)
    
    return posts

# -------------------------------
# Script Execution
# -------------------------------
if __name__ == "__main__":

    cl = login_user()
    add_delays(cl, 0.1, 2) # Add delays between requests


    # Example usage
    # get_posts_by_hashtag("meme", type='top', amount=5)
    # retrieve_media_with_username("elahe_samadfam")
    # send_direct_message_with_username("megachat_test", "Hello! This is a test message from ChatGPT.")
    # download_story_with_username("elahe_samadfam")
    # print(cl.user_info_by_username("elahe_samadfam"))
    # save_user_info_in_database(cl.user_info_by_username("elahe_samadfam"))
    comment_on_post_by_id("3544076771193756114_2200294728","this is a comment from bot!")
    like_post_by_id("3544076771193756114_2200294728")


    start_time = time.time()
    while True:
        try:
            handle_messages()
            # time.sleep(5)  # Check for new messages every 5 seconds
            print(f"Running for {time.time() - start_time} seconds")
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)  # Wait longer if there's an error

