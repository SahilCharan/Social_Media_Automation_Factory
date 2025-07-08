# mock_services.py
import logging

class MockGoogleDriveService:
    def get_new_content_file(self):
        logging.info("MOCK: Pretending to look for new files in Google Drive.")
        return None  # Simulate no new files for now

    def download_file(self, file_id, destination):
        logging.info(f"MOCK: Pretending to download file {file_id} to {destination}")

    def archive_file(self, file_id):
        logging.info(f"MOCK: Pretending to archive file {file_id}")

class MockAIEngine:
    def generate_post_from_inspiration(self, post):
        logging.info("MOCK: Pretending to generate content from inspiration.")
        return {
            "instagram_caption": "A mock caption for Instagram.",
            "facebook_post": "A mock post for Facebook.",
            "youtube_script": "A mock script for YouTube."
        }

    def generate_post_from_drive_file(self, file_info):
        logging.info("MOCK: Pretending to generate content from a Drive file.")
        return {
            "instagram_caption": "A mock caption for a Drive file.",
            "facebook_post": "A mock post for a Drive file.",
            "youtube_title": "A mock YouTube title.",
            "youtube_description": "A mock YouTube description."
        }

class MockInstagramPublisher:
    def post_image(self, image_url, caption):
        logging.info(f"MOCK: Pretending to post image to Instagram: {caption}")
        return True

    def post_video(self, video_url, caption):
        logging.info(f"MOCK: Pretending to post video to Instagram: {caption}")
        return True

class MockFacebookPublisher:
    def post(self, content, image_url=None):
        logging.info(f"MOCK: Pretending to post to Facebook: {content}")

class MockYouTubePublisher:
    def upload_video(self, video_path, title, description):
        logging.info(f"MOCK: Pretending to upload video to YouTube: {title}")

class MockInstagramService:
    def get_top_inspirational_post(self, state_manager):
        logging.info("MOCK: Pretending to get top inspirational post.")
        return {
            'shortcode': 'mock_post',
            'caption': 'This is a mock post.',
            'is_video': False,
            'url': 'http://fake.com/p/mock_post'
        }
