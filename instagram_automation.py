#!/usr/bin/env python3
"""
Complete Social Media Automation Engine v2.0 (Production Ready)

This script provides a full-cycle, intelligent social media automation solution.
It incorporates best practices for security, rate limiting, and API usage.

Features:
- Secure configuration using environment variables (.env file).
- Modern, robust API clients for all services.
- Intelligent rate limiting to prevent account restrictions.
- Full automation for Instagram, Facebook, and YouTube posting.
- AI-powered content generation via OpenAI.
- Dual content sourcing from Google Drive and Instagram inspiration.
- HTML dashboard for visual reporting.
- Scheduled, continuous operation.
"""

import os
import io
import json
import time
import random
import pickle
import logging
import schedule
import facebook
import getpass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

# Third-party libraries
from auth_service import AuthService  # Centralized authentication service
from improved_instagram_publisher import ImprovedInstagramPublisher
import instaloader
import openai
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

# --- Secure Configuration ---

def load_secure_config() -> Dict[str, Any]:
    """Loads configuration from .env and a config.json file."""
    load_dotenv()
    
    with open("config.json", 'r') as f:
        config = json.load(f)

    return config

# --- Rate Limiting ---

class RateLimiter:
    """Simple rate limiter to add delays between API calls."""
    def __init__(self, min_delay=2, max_delay=8):
        self.min_delay = min_delay
        self.max_delay = max_delay

    def wait(self):
        """Waits for a random duration."""
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)

# --- State Management ---

class StateManager:
    """Manages the state of processed posts to avoid duplicates."""
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.processed_shortcodes = self._load()

    def _load(self) -> set:
        """Loads the set of processed shortcodes from the database file."""
        if not self.db_path.exists():
            return set()
        with open(self.db_path, 'r') as f:
            try:
                return set(json.load(f))
            except json.JSONDecodeError:
                return set()

    def _save(self):
        """Saves the current set of processed shortcodes to the database file."""
        with open(self.db_path, 'w') as f:
            json.dump(list(self.processed_shortcodes), f)

    def has_been_processed(self, shortcode: str) -> bool:
        """Checks if a post shortcode has already been processed."""
        return shortcode in self.processed_shortcodes

    def add_processed(self, shortcode: str):
        """Adds a new shortcode to the set of processed posts and saves."""
        self.processed_shortcodes.add(shortcode)
        self._save()

# --- Service Connectors ---

class GoogleDriveService:
    """Handles all interactions with the Google Drive API."""
    def __init__(self, config: Dict[str, Any], rate_limiter: RateLimiter, auth_service):
        self.auth_service = auth_service
        self.config = config['google_drive'] # Keep non-sensitive config
        self.rate_limiter = rate_limiter
        self.credentials_file = self.auth_service.get_google_credentials_file()
        self.token_file = self.auth_service.get_google_token_file()
        self.service = self._authenticate()

    def _authenticate(self) -> Optional[Any]:
        """Authenticates with the Google Drive API."""
        creds = None
        token_file_path = Path(self.token_file)
        creds_file_path = Path(self.credentials_file)

        if token_file_path.exists():
            with open(token_file_path, 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not creds_file_path.exists():
                    logging.error(f"Google Drive credentials not found at {creds_file_path}")
                    return None
                flow = InstalledAppFlow.from_client_secrets_file(creds_file_path, ['https://www.googleapis.com/auth/drive'])
                creds = flow.run_local_server(port=0)
            with open(token_file_path, 'wb') as token:
                pickle.dump(creds, token)
        
        logging.info("Google Drive service authenticated.")
        return build('drive', 'v3', credentials=creds)

    def get_new_content_file(self) -> Optional[Dict[str, Any]]:
        """Fetches a single, random file from the 'new content' folder."""
        if not self.service:
            return None
        folder_id = self.config['new_content_folder_id']
        try:
            self.rate_limiter.wait()
            results = self.service.files().list(
                q=f"'{folder_id}' in parents and trashed=false",
                fields="files(id, name, mimeType, webViewLink)").execute()
            files = results.get('files', [])
            if not files:
                logging.info("No new content found in Google Drive.")
                return None
            return random.choice(files)
        except HttpError as e:
            logging.error(f"Failed to list files in Drive: {e}")
            return None

    def download_file(self, file_id: str, destination: str):
        """Downloads a file from Google Drive to a local path."""
        if not self.service:
            return
        try:
            self.rate_limiter.wait()
            request = self.service.files().get_media(fileId=file_id)
            fh = io.FileIO(destination, 'wb')
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                logging.info(f"Downloaded {int(status.progress() * 100)}% of Drive file.")
            logging.info(f"Successfully downloaded file {file_id} to {destination}")
        except HttpError as e:
            logging.error(f"Failed to download file {file_id}: {e}")

    def archive_file(self, file_id: str):
        """Moves a file to the 'archived content' folder."""
        if not self.service:
            return
        archive_folder_id = self.config['archived_content_folder_id']
        try:
            self.rate_limiter.wait()
            file = self.service.files().get(fileId=file_id, fields='parents').execute()
            previous_parents = ",".join(file.get('parents'))
            self.service.files().update(
                fileId=file_id,
                addParents=archive_folder_id,
                removeParents=previous_parents,
                fields='id, parents').execute()
            logging.info(f"Archived file {file_id} in Google Drive.")
        except HttpError as e:
            logging.error(f"Failed to archive file {file_id}: {e}")

class InstagramService:
    """Handles scraping and posting to Instagram."""
    def __init__(self, config: Dict[str, Any], rate_limiter: RateLimiter, auth_service):
        self.auth_service = auth_service
        self.config = config['instagram'] # Keep non-sensitive config
        self.rate_limiter = rate_limiter
        self.loader = instaloader.Instaloader()
        self._login()

    def _login(self):
        """Loads an Instagram session from file. Fails fast if session is missing or invalid."""
        username = self.auth_service.get_instagram_login_username()
        session_file = f"{username}.session"

        if not Path(session_file).exists():
            raise RuntimeError(
                f"Instagram session file '{session_file}' not found.\n"
                f"Please generate it manually using:\n"
                f"    instaloader --login={username}\n"
                f"This automation system does not support interactive logins."
            )

        try:
            self.loader.load_session_from_file(username)
            logging.info(f"Successfully loaded Instagram session for @{username}")
        except Exception as e:
            logging.error(f"Failed to load Instagram session for @{username}: {e}")
            raise RuntimeError("Session file is corrupted or expired. Please regenerate using instaloader.")


    def get_top_inspirational_post(self, state_manager: StateManager) -> Optional[Dict[str, Any]]:
        """Finds the top-performing post that has not yet been processed."""
        logging.info(f"Scanning @{self.config['target_username']} for inspirational content.")
        profile = instaloader.Profile.from_username(self.loader.context, self.config['target_username'])
        
        top_post = None
        max_engagement = -1

        for post in profile.get_posts():
            self.rate_limiter.wait()
            if state_manager.has_been_processed(post.shortcode):
                continue
            
            engagement = post.likes + post.comments
            if engagement > max_engagement:
                max_engagement = engagement
                top_post = {
                    'shortcode': post.shortcode,
                    'caption': post.caption,
                    'is_video': post.is_video,
                    'url': f"https://www.instagram.com/p/{post.shortcode}/"
                }
        
        if top_post:
            logging.info(f"Found top inspirational post: {top_post['shortcode']}")
        else:
            logging.warning("No new inspirational posts found to process.")
            
        return top_post

class AIEngine:
    """Handles content generation using OpenAI."""
    def __init__(self, config: Dict[str, Any], rate_limiter: RateLimiter, auth_service):
        self.auth_service = auth_service
        self.config = config['openai'] # Keep non-sensitive config
        self.rate_limiter = rate_limiter
        self.client = openai.OpenAI(api_key=self.auth_service.get_openai_api_key())

    def _call_openai(self, prompt: str) -> Dict[str, str]:
        self.rate_limiter.wait()
        try:
            response = self.client.chat.completions.create(
                model=self.config.get('model', 'gpt-4-turbo'),
                messages=[
                    {"role": "system", "content": "You are a creative social media manager. Always respond with a valid JSON object."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logging.error(f"OpenAI call failed: {e}")
            return {}
    
    def generate_post_from_inspiration(self, post: Dict[str, Any]) -> Dict[str, str]:
        prompt = f"""Analyze this successful Instagram post and generate new, platform-specific content for a clothing brand. Original Post Details: Type: {'Video' if post['is_video'] else 'Image'}, Original Caption: {post['caption']}. Your Task: 1. For Instagram: Write a new, engaging caption with 3-5 relevant hashtags. 2. For Facebook: Write a longer, community-focused post. 3. For YouTube: If it was a video, write a script for a new YouTube Short. If an image, describe a concept for one. Format your response as a JSON object with keys \"instagram_caption\", \"facebook_post\", and \"youtube_script\"."""
        return self._call_openai(prompt)

    def generate_post_from_drive_file(self, file_info: Dict[str, Any]) -> Dict[str, str]:
        content_type = 'video' if 'video' in file_info['mimeType'] else 'image'
        prompt = f"""You are a social media manager for a clothing brand. A new {content_type} has been provided. File Details: Name: {file_info['name']}. Your Task: 1. For Instagram: Write a fresh caption with a call-to-action and 3-5 hashtags. 2. For Facebook: Write a slightly longer post. 3. For YouTube: Write a title and description. Format your response as a JSON object with keys \"instagram_caption\", \"facebook_post\", \"youtube_title\", and \"youtube_description\"."""
        return self._call_openai(prompt)

# --- Social Media Publishers ---

class FacebookPublisher:
    """Handles posting content to a Facebook Page."""
    def __init__(self, config: Dict[str, Any], rate_limiter: RateLimiter, auth_service):
        self.auth_service = auth_service
        self.rate_limiter = rate_limiter
        self.access_token = self.auth_service.get_facebook_token()
        self.page_id = self.auth_service.get_facebook_page_id()
        try:
            self.graph = facebook.GraphAPI(self.access_token)
            logging.info("Facebook service initialized.")
        except Exception as e:
            self.graph = None
            logging.error(f"Failed to initialize Facebook GraphAPI: {e}")

    def post(self, content: str, image_url: Optional[str] = None):
        """Publishes a post to the configured Facebook Page."""
        if not self.graph:
            logging.error("Cannot post to Facebook, service not initialized.")
            return
        
        try:
            self.rate_limiter.wait()
            post_data = {'message': content}
            if image_url:
                self.graph.put_photo(image=image_url, message=content)
            else:
                self.graph.put_object(self.page_id, 'feed', message=content)
            logging.info("Successfully posted to Facebook.")
        except facebook.GraphAPIError as e:
            logging.error(f"Failed to post to Facebook: {e}")

'''
class InstagramPublisher:
    """Handles posting content to an Instagram Business Account."""
    def __init__(self, config: Dict[str, Any], rate_limiter: RateLimiter):
        self.config = config['facebook'] # Instagram posting uses the Facebook Graph API
        self.insta_account_id = config['instagram']['instagram_business_account_id']
        self.rate_limiter = rate_limiter
        try:
            self.graph = facebook.GraphAPI(self.config['access_token'])
            logging.info("Instagram Publisher initialized.")
        except Exception as e:
            self.graph = None
            logging.error(f"Failed to initialize Instagram Publisher: {e}")

    def post(self, media_url: str, caption: str, is_video: bool = False):
        """Uploads and posts an image or video to Instagram."""
        if not self.graph:
            logging.error("Cannot post to Instagram, service not initialized.")
            return

        try:
            self.rate_limiter.wait()
            params = {
                'caption': caption
            }
            if is_video:
                params['video_url'] = media_url
                media_type = 'videos'
            else:
                params['image_url'] = media_url
                media_type = 'media'

            # Create a container for the media
            container = self.graph.post(
                f"{self.insta_account_id}/{media_type}",
                params=params
            )
            container_id = container['id']
            logging.info(f"Created Instagram {media_type} container with ID: {container_id}")

            # Publish the container
            self.graph.post(
                f"{self.insta_account_id}/media_publish",
                params={'creation_id': container_id}
            )
            logging.info(f"Successfully published {media_type} to Instagram.")
        except facebook.GraphAPIError as e:
            logging.error(f"Failed to post {media_type} to Instagram: {e}")
            '''

class YouTubePublisher:
    """Handles uploading videos to YouTube."""
    def __init__(self, config: Dict[str, Any], rate_limiter: RateLimiter, auth_service):
        self.auth_service = auth_service
        self.rate_limiter = rate_limiter
        self.client_secrets_file = self.auth_service.get_youtube_secrets_file()
        self.token_file = self.auth_service.get_youtube_token_file()
        self.service = self._authenticate()

    def _authenticate(self) -> Optional[Any]:
        """Authenticates with the YouTube Data API."""
        creds = None
        token_file_path = Path(self.token_file)
        creds_file_path = Path(self.client_secrets_file)

        if token_file_path.exists():
            with open(token_file_path, 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not creds_file_path.exists():
                    logging.error(f"YouTube client secrets file not found at {creds_file_path}")
                    return None
                flow = InstalledAppFlow.from_client_secrets_file(creds_file_path, ['https://www.googleapis.com/auth/youtube.upload'])
                creds = flow.run_local_server(port=0)
            with open(token_file_path, 'wb') as token:
                pickle.dump(creds, token)
        
        logging.info("YouTube service authenticated.")
        return build('youtube', 'v3', credentials=creds)

    def upload_video(self, video_path: str, title: str, description: str):
        """Uploads a video to YouTube."""
        if not self.service:
            logging.error("Cannot upload to YouTube, service not initialized.")
            return

        try:
            self.rate_limiter.wait()
            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'tags': ['automated', 'business', 'socialmedia'],
                    'categoryId': '22'
                },
                'status': {
                    'privacyStatus': 'private' # Can be 'public', 'private', or 'unlisted'
                }
            }

            media = MediaFileUpload(video_path, chunksize=-1, resumable=True)

            request = self.service.videos().insert(
                part=",".join(body.keys()),
                body=body,
                media_body=media
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    logging.info(f"Uploaded {int(status.progress() * 100)}% to YouTube.")
            
            logging.info(f"Successfully uploaded video to YouTube with ID: {response.get('id')}")
        except HttpError as e:
            logging.error(f"Failed to upload video to YouTube: {e}")

# --- HTML Dashboard Generation ---

def generate_html_dashboard(report_data: Dict[str, Any]):
    """Generates a simple HTML dashboard from the report data."""
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Automation Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #f9f9f9; }}
            h1, h2 {{ color: #333; }}
            .card {{ background: white; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        </style>
    </head>
    <body>
        <h1>Social Media Automation Dashboard</h1>
        <div class="card">
            <h2>Last Run Summary</h2>
            <p><strong>Timestamp:</strong> {report_data.get('timestamp')}</p>
            <p><strong>Action Taken:</strong> {report_data.get('action_taken')}</p>
            <p><strong>Outcome:</strong> {report_data.get('outcome')}</p>
        </div>
        <div class="card">
            <h2>Generated Content</h2>
            <h3>Facebook Post</h3>
            <pre>{report_data.get('facebook_post', 'N/A')}</pre>
            <h3>YouTube Script</h3>
            <pre>{report_data.get('youtube_script', 'N/A')}</pre>
        </div>
    </body>
    </html>
    """
    with open("dashboard.html", "w", encoding="utf-8") as f:
        f.write(html_template)
    logging.info("HTML dashboard has been updated.")

# --- Main Automation Workflow ---

def run_automation_cycle(
    config, state_manager, rate_limiter,
    ig_publisher, fb_publisher, yt_publisher,
    drive_service, ai_engine, instagram_service
):
    logging.info("Starting new automation cycle.")
    report_data = {'timestamp': datetime.now().isoformat()}

    # Path B: new Drive content
    if random.choice([True, False]):
        logging.info("Path B: Google Drive content.")
        new_file = drive_service.get_new_content_file()
        if new_file:
            report_data['action_taken'] = f"Drive file: {new_file['name']}"
            generated = ai_engine.generate_post_from_drive_file(new_file)
            if generated:
                media_url = new_file.get('webViewLink')
                caption   = generated['instagram_caption']
                is_video  = 'video' in new_file['mimeType']

                # Instagram
                if is_video:
                    ig_publisher.post_video(media_url, caption)
                else:
                    ig_publisher.post_image(media_url, caption)

                # Facebook
                fb_publisher.post(generated['facebook_post'], image_url=media_url)

                # YouTube if video
                if is_video:
                    local_file = f"./{new_file['name']}"
                    drive_service.download_file(new_file['id'], local_file)
                    yt_publisher.upload_video(
                        local_file,
                        generated.get('youtube_title', ''),
                        generated.get('youtube_description', '')
                    )
                    os.remove(local_file)

                report_data.update(generated)
                report_data['outcome'] = "Posted Drive content."
                drive_service.archive_file(new_file['id'])
            else:
                report_data['outcome'] = "AI generation failed."
        else:
            report_data.update({
                'action_taken': "No Drive content.",
                'outcome': "Nothing to process."
            })

    # Path A: Instagram inspiration
    else:
        logging.info("Path A: Instagram inspiration.")
        top = instagram_service.get_top_inspirational_post(state_manager)
        if top:
            report_data['action_taken'] = f"Inspired by {top['shortcode']}"
            generated = ai_engine.generate_post_from_inspiration(top)
            if generated:
                media_url = top['url']
                caption   = generated['instagram_caption']
                is_video  = top['is_video']

                # Instagram
                if is_video:
                    ig_publisher.post_video(media_url, caption)
                else:
                    ig_publisher.post_image(media_url, caption)

                # Facebook
                fb_publisher.post(generated['facebook_post'], image_url=media_url)

                report_data.update(generated)
                report_data['outcome'] = "Posted inspired content."
                state_manager.add_processed(top['shortcode'])
            else:
                report_data['outcome'] = "AI generation failed."
        else:
            report_data.update({
                'action_taken': "No new Instagram posts.",
                'outcome': "Nothing to process."
            })

    # Dashboard
    generate_html_dashboard(report_data)
    logging.info("Cycle complete.")


# --- Main Execution Block ---

if __name__ == "__main__":
    try:
        # 1) Load static JSON defaults
        config = load_secure_config()

        # 2) Centralize auth and validate env vars
        
        auth = AuthService()
        
        # All sensitive credentials are now managed by AuthService and passed directly to relevant services.
        # The 'config' object will only contain non-sensitive settings.

        # 3) Setup logging (now that config['settings']['log_file'] is set)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - [%(module)s] - %(message)s',
            handlers=[
                logging.FileHandler(config['settings']['log_file']),
                logging.StreamHandler()
            ]
        )
        logging.info("Logging initialized.")

        # 4) Initialize shared helpers
        state_manager = StateManager(config['settings']['processed_posts_db'])
        rate_limiter  = RateLimiter()

        # 5) Instantiate your publishers (with auth baked in)
        ig_publisher = ImprovedInstagramPublisher(config, rate_limiter, auth)
        fb_publisher = FacebookPublisher(config, rate_limiter, auth)
        yt_publisher = YouTubePublisher(config, rate_limiter, auth)
        drive_service     = GoogleDriveService(config, rate_limiter, auth)
        ai_engine         = AIEngine(config, rate_limiter, auth)
        instagram_service = InstagramService(config, rate_limiter, auth)

        logging.info("Social Media Automation Engine v2.0 Started.")
        print("The automation engine is now running...")

        # 6) Schedule the jobs, passing in the pre-built service instances
        schedule.every().day.at(config['scheduling']['post_time_1']).do(
            run_automation_cycle,
            config, state_manager, rate_limiter,
            ig_publisher, fb_publisher, yt_publisher, drive_service, ai_engine, instagram_service
        )
        schedule.every().day.at(config['scheduling']['post_time_2']).do(
            run_automation_cycle,
            config, state_manager, rate_limiter,
            ig_publisher, fb_publisher, yt_publisher, drive_service, ai_engine, instagram_service
        )

        # 7) Keep the script alive
        while True:
            schedule.run_pending()
            time.sleep(1)

    except (ValueError, FileNotFoundError) as e:
        logging.critical(f"Configuration Error: {e}. The application cannot start.")
        print(f"Configuration Error: {e}. Please check your .env and config.json files.")

    except KeyboardInterrupt:
        logging.info("Automation engine stopped by user.")
        print("Automation engine stopped by user.")

    except Exception as e:
        logging.critical(f"A fatal error occurred: {e}", exc_info=True)
        print(f"A fatal error occurred: {e}. Check the log file for details.")
