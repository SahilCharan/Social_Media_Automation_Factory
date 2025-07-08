# launcher.py
import os
import subprocess
from dotenv import load_dotenv

def main():
    # Load environment variables from .env file
    load_dotenv()

    # Check for a critical API key to determine mode
    # We'll use FACEBOOK_ACCESS_TOKEN as an indicator for real credentials
    CRITICAL_ENV_VARS = [
        ("FACEBOOK_ACCESS_TOKEN", "YOUR_FACEBOOK_PAGE_ACCESS_TOKEN"),
        ("INSTAGRAM_LOGIN_USERNAME", "your_instagram_username"),
        ("OPENAI_API_KEY", "your_openai_api_key")
    ]

    run_production = True
    for env_var, placeholder in CRITICAL_ENV_VARS:
        value = os.getenv(env_var)
        if not value or value.strip() == "" or value.strip() == placeholder:
            run_production = False
            break

    if run_production:
        print("All critical API keys detected. Starting automation in PRODUCTION MODE.")
        script_to_run = "instagram_automation.py"
    else:
        print("One or more critical API keys are missing or are placeholders. Starting automation in DEVELOPMENT MODE (mock services).")
        script_to_run = "dev_runner.py"

    # Execute the chosen script
    try:
        # Use subprocess.run to execute the script
        # capture_output=False to allow the subprocess to print directly to console
        # check=True will raise an exception if the subprocess returns a non-zero exit code
        subprocess.run(["python", script_to_run], check=True, capture_output=False)
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_to_run}: {e}")
    except FileNotFoundError:
        print(f"Error: Python or {script_to_run} not found. Make sure Python is in your PATH and the script exists.")

if __name__ == "__main__":
    main()
