# dev_runner.py
import logging
import json

# Import the core logic function from the original script
from instagram_automation import run_automation_cycle, RateLimiter, StateManager

# Import all our mock services
from mock_services import (
    MockAIEngine,
    MockFacebookPublisher,
    MockGoogleDriveService,
    MockInstagramPublisher,
    MockInstagramService,
    MockYouTubePublisher
)

def main():
    """
    Runs the automation cycle in development mode using mock services.
    """
    print("Starting automation in DEVELOPMENT MODE.")
    print("No real API calls will be made.")

    # 1. Load configuration
    try:
        with open("config.json", 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        logging.critical("config.json not found. Please run the setup script first.")
        return

    # 2. Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - [%(module)s] - %(message)s',
        handlers=[
            logging.FileHandler(config['settings']['log_file']),
            logging.StreamHandler()
        ]
    )
    logging.info("Logging initialized for DEVELOPMENT run.")

    # 3. Initialize shared helpers (these are safe to use)
    state_manager = StateManager(config['settings']['processed_posts_db'])
    rate_limiter  = RateLimiter(min_delay=0.1, max_delay=0.2) # Speed up delays for testing

    # 4. Instantiate MOCK services
    logging.info("Instantiating MOCK services...")
    drive_service = MockGoogleDriveService()
    ai_engine = MockAIEngine()
    ig_publisher = MockInstagramPublisher()
    fb_publisher = MockFacebookPublisher()
    yt_publisher = MockYouTubePublisher()
    instagram_service = MockInstagramService()
    logging.info("All MOCK services are ready.")

    # 5. Run the core automation cycle with the mock objects
    try:
        run_automation_cycle(
            config=config,
            state_manager=state_manager,
            rate_limiter=rate_limiter,
            ig_publisher=ig_publisher,
            fb_publisher=fb_publisher,
            yt_publisher=yt_publisher,
            drive_service=drive_service,
            ai_engine=ai_engine,
            instagram_service=instagram_service
        )
    except Exception as e:
        logging.critical(f"An error occurred during the mock automation cycle: {e}", exc_info=True)

    print("\nDEVELOPMENT run complete. Check 'automation.log' and 'dashboard.html' for output.")

if __name__ == "__main__":
    main()
