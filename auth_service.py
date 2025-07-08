# auth_service.py
import os

class AuthService:
    """
    Centralizes all token loading (and optional refreshing) logic.
    """

    def __init__(self):
        # Facebook & Instagram
        self.facebook_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
        if not self.facebook_token:
            raise ValueError("FACEBOOK_ACCESS_TOKEN is required in .env")

        self.instagram_business_account_id = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID')
        if not self.instagram_business_account_id:
            raise ValueError("INSTAGRAM_BUSINESS_ACCOUNT_ID is required in .env")

        self.instagram_login_username = os.getenv('INSTAGRAM_LOGIN_USERNAME')
        if not self.instagram_login_username:
            raise ValueError("INSTAGRAM_LOGIN_USERNAME is required in .env")

        self.facebook_page_id = os.getenv('FACEBOOK_PAGE_ID')
        if not self.facebook_page_id:
            raise ValueError("FACEBOOK_PAGE_ID is required in .env")

        # OpenAI
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required in .env")

        # Google Drive
        self.google_credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE')
        self.google_token_file = os.getenv('GOOGLE_TOKEN_FILE')

        # YouTube
        self.youtube_secrets_file = os.getenv('YOUTUBE_CLIENT_SECRETS_FILE')
        self.youtube_token_file = os.getenv('YOUTUBE_TOKEN_FILE')

    # Facebook/Instagram
    def get_facebook_token(self): return self.facebook_token
    def get_instagram_business_account_id(self): return self.instagram_business_account_id
    def get_instagram_login_username(self): return self.instagram_login_username
    def get_facebook_page_id(self): return self.facebook_page_id

    # OpenAI
    def get_openai_api_key(self): return self.openai_api_key

    # Google Drive
    def get_google_credentials_file(self): return self.google_credentials_file
    def get_google_token_file(self): return self.google_token_file

    # YouTube
    def get_youtube_secrets_file(self): return self.youtube_secrets_file
    def get_youtube_token_file(self): return self.youtube_token_file
    # Add refresh logic here if needed in future
    # def refresh_tokens(self):
    #     pass  # Implement token refresh logic if needed
    # Example: if using OAuth2, you might implement a method to refresh tokens

#     # This could involve checking expiry and using refresh tokens if available
    #     # For now, we assume tokens are static and loaded from environment variables  
    