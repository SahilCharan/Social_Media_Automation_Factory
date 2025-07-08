import logging
import time
import requests
from typing import Dict

class ImprovedInstagramPublisher:
    """Enhanced Instagram Publisher with better error handling and media support."""

    def __init__(self, config: Dict[str, any], rate_limiter, auth_service):
        self.auth_service = auth_service
        self.rate_limiter = rate_limiter
        self.base_url = f"https://graph.facebook.com/v{config.get('facebook_api_version', '18.0')}"
        self.access_token = self.auth_service.get_facebook_token()
        self.insta_account_id = self.auth_service.get_instagram_business_account_id()

        if not self.access_token:
            raise ValueError("Facebook access token is required for Instagram posting")

    def post_image(self, image_url: str, caption: str) -> bool:
        try:
            self.rate_limiter.wait()
            container_url = f"{self.base_url}/{self.insta_account_id}/media"
            container_params = {
                'image_url': image_url,
                'caption': caption,
                'access_token': self.access_token
            }
            container_response = requests.post(container_url, data=container_params)
            container_response.raise_for_status()
            container_id = container_response.json()['id']

            self.rate_limiter.wait()
            publish_url = f"{self.base_url}/{self.insta_account_id}/media_publish"
            publish_params = {
                'creation_id': container_id,
                'access_token': self.access_token
            }
            publish_response = requests.post(publish_url, data=publish_params)
            publish_response.raise_for_status()

            logging.info("Successfully published image to Instagram")
            return True

        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to post image to Instagram: {e}")
            return False

    def post_video(self, video_url: str, caption: str) -> bool:
        try:
            self.rate_limiter.wait()
            container_url = f"{self.base_url}/{self.insta_account_id}/media"
            container_params = {
                'media_type': 'VIDEO',
                'video_url': video_url,
                'caption': caption,
                'access_token': self.access_token
            }
            container_response = requests.post(container_url, data=container_params)
            container_response.raise_for_status()
            container_id = container_response.json()['id']

            max_wait = 300
            wait_time = 0
            while wait_time < max_wait:
                time.sleep(10)
                wait_time += 10
                status_url = f"{self.base_url}/{container_id}"
                status_params = {
                    'fields': 'status_code',
                    'access_token': self.config['access_token']
                }
                status_response = requests.get(status_url, params=status_params)
                status_data = status_response.json()
                if status_data.get('status_code') == 'FINISHED':
                    break
                elif status_data.get('status_code') == 'ERROR':
                    logging.error("Video processing failed on Instagram")
                    return False

            publish_url = f"{self.base_url}/{self.insta_account_id}/media_publish"
            publish_params = {
                'creation_id': container_id,
                'access_token': self.access_token
            }
            publish_response = requests.post(publish_url, data=publish_params)
            publish_response.raise_for_status()

            logging.info("Successfully published video to Instagram")
            return True

        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to post video to Instagram: {e}")
            return False
