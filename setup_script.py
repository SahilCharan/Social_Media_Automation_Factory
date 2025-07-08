#!/usr/bin/env python3
"""
Instagram Business Intelligence - Project Setup Script
Run this to set up the complete project structure
"""

import os
import json
from pathlib import Path

def create_requirements_txt():
    """Create requirements.txt file"""
    requirements = """# Instagram Business Intelligence Requirements
instaloader>=4.9.6
google-auth>=2.17.3
google-auth-oauthlib>=1.0.0
google-auth-httplib2>=0.1.0
google-api-python-client>=2.88.0
textblob>=0.17.1
Pillow>=9.5.0
requests>=2.31.0
python-dotenv>=1.0.0
pandas>=2.0.3
matplotlib>=3.7.1
seaborn>=0.12.2
wordcloud>=1.9.2
schedule>=1.2.0
openai>=1.3.0
facebook-sdk>=3.0.0
"""
    
    with open("requirements.txt", "w") as f:
        f.write(requirements)
    print("Created requirements.txt")

def create_config_json():
    """Create comprehensive configuration file"""
    config = {
        "instagram": {
            "target_username": "sawantrajtejraj",
            "max_posts_to_scan": 25
        },
        "openai": {
            "model": "gpt-4-turbo"
        },
        "scheduling": {
            "post_time_1": "09:00",
            "post_time_2": "17:00"
        },
        "settings": {
            "log_file": "automation.log",
            "processed_posts_db": "processed_posts.json"
        }
    }
    
    with open("config.json", "w") as f:
        json.dump(config, f, indent=2)
    print("Created config.json")

def create_n8n_workflow():
    """Create sample n8n workflow"""
    workflow = {
        "name": "Instagram Content Automation",
        "active": False,
        "nodes": [
            {
                "parameters": {
                    "httpMethod": "POST",
                    "path": "instagram-data",
                    "responseMode": "responseNode"
                },
                "name": "Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [250, 300]
            },
            {
                "parameters": {
                    "functionCode": "// Process Instagram data\nconst posts = items[0].json.posts || [];\nconst analysis = items[0].json.analysis || {};\n\n// Extract insights\nconst insights = {\n  totalPosts: posts.length,\n  avgEngagement: posts.reduce((sum, p) => sum + p.likes + p.comments, 0) / posts.length,\n  topPerformer: posts.reduce((max, p) => (p.likes + p.comments) > (max.likes + max.comments) ? p : max, posts[0]),\n  recommendations: analysis.performance_insights?.content_recommendations || []\n};\n\nreturn [{json: insights}];"
                },
                "name": "Process Data",
                "type": "n8n-nodes-base.function",
                "typeVersion": 1,
                "position": [450, 300]
            },
            {
                "parameters": {
                    "channel": "#instagram-insights",
                    "text": "New Instagram analysis complete!\n\nTotal Posts: {{$json.totalPosts}}\nAvg Engagement: {{$json.avgEngagement}}\nTop Post: {{$json.topPerformer.shortcode}}\n\nRecommendations:\n{{$json.recommendations.join('\\n')}}"
                },
                "name": "Send to Slack",
                "type": "n8n-nodes-base.slack",
                "typeVersion": 1,
                "position": [650, 300]
            }
        ],
        "connections": {
            "Webhook": {
                "main": [
                    [
                        {
                            "node": "Process Data",
                            "type": "main",
                            "index": 0
                        }
                    ]
                ]
            },
            "Process Data": {
                "main": [
                    [
                        {
                            "node": "Send to Slack",
                            "type": "main",
                            "index": 0
                        }
                    ]
                ]
            }
        }
    }
    
    with open("n8n_workflow_sample.json", "w") as f:
        json.dump(workflow, f, indent=2)
    print("Created n8n_workflow_sample.json")

def create_readme():
    """Create comprehensive README"""
    readme = """# Instagram Business Intelligence & Content Automation

Advanced Instagram scraping, analysis, and automation tool for business intelligence.

## Features

- **Advanced Analytics**: Sentiment analysis, engagement prediction, optimal posting times
- **Smart Scraping**: Rate-limited Instagram content extraction with metadata
- **Business Intelligence**: Performance insights and actionable recommendations  
- **Google Drive Integration**: Automatic backup and organization
- **n8n Automation**: Webhook integration for workflow automation
- **Dashboard**: HTML dashboard for visual insights

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Google Drive Setup (Optional)
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google Drive API
4. Create credentials (OAuth 2.0) and download as `credentials.json`
5. Place `credentials.json` in project root

### 3. Configuration
Edit `config.json` to customize settings:
- Instagram scraping parameters
- Google Drive settings
- n8n webhook URLs
- Notification preferences

## Usage

### Basic Usage
```bash
python instagram_automation.py --username your_target_username
```

### Advanced Options
```bash
# Scrape more posts
python instagram_automation.py --username username --max-posts 50

# Skip Google Drive upload
python instagram_automation.py --username username --skip-drive

# Custom output directory
python instagram_automation.py --username username --output-path ./custom_output

# Verbose logging
python instagram_automation.py --username username --verbose
```

## Outputs

The tool generates comprehensive reports including:

- **Enhanced Metadata**: Complete post data with sentiment analysis
- **Performance Insights**: Engagement patterns and trends
- **Content Recommendations**: Data-driven suggestions
- **n8n Webhook Data**: Ready for automation workflows
- **Google Drive Backup**: Organized cloud storage

## n8n Integration

1. Import `n8n_workflow_sample.json` into your n8n instance
2. Configure webhook URL in `config.json`
3. Set up Slack/Discord notifications (optional)
4. The workflow will automatically trigger on new analysis

## Dashboard

Access the generated HTML dashboard for visual insights:
- Engagement trends over time
- Optimal posting times
- Hashtag performance
- Content recommendations

## Advanced Features

### Sentiment Analysis
- Analyzes caption sentiment using TextBlob
- Correlates sentiment with engagement
- Provides mood-based recommendations

### Hashtag Intelligence
- Tracks trending hashtags
- Identifies high-performing tags
- Suggests optimal hashtag combinations

### Engagement Prediction
- Analyzes patterns in high-performing content
- Predicts optimal posting times
- Identifies content features that drive engagement

## Project Structure

```
instagram-automation/
├── instagram_automation.py    # Main script
├── config.json               # Configuration
├── requirements.txt          # Dependencies
├── n8n_workflow_sample.json  # n8n workflow
├── scraped_content/          # Output directory
├── credentials.json          # Google Drive credentials
└── README.md                # This file
```

## Important Notes

- **Rate Limiting**: Built-in delays to respect Instagram's limits
- **Legal Compliance**: Only scrape public content you have permission to access
- **Data Privacy**: Be mindful of data protection regulations
- **Instagram ToS**: Review Instagram's Terms of Service before use

## Troubleshooting

### Common Issues

**"Login required" errors**:
- Instagram may require login for some profiles
- Try with public profiles first

**Google Drive upload fails**:
- Check credentials.json file
- Verify Google Drive API is enabled
- Ensure proper OAuth scopes

**Rate limiting**:
- Increase delays in config.json
- Reduce max_posts parameter
- Run during off-peak hours

## Security

- Never commit `credentials.json` to version control
- Use environment variables for sensitive data
- Regularly rotate API keys and tokens
- Monitor for unusual activity

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review Instagram and Google API documentation
3. Check n8n community forums for workflow help

## License

This project is for educational and business intelligence purposes. Ensure compliance with all applicable terms of service and regulations.

---

**Happy Automating!**
"""
    
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme)
    print("Created README.md")

def create_gitignore():
    """Create .gitignore file"""
    gitignore = """# Instagram Automation
scraped_content/
*.log
credentials.json
token.pickle
config.json
.env

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
"""
    
    with open(".gitignore", "w") as f:
        f.write(gitignore)
    print("Created .gitignore")

def create_env_template():
    """Create environment template"""
    env_template = """# Social Media Automation Engine Environment Variables
# Copy this file to .env and fill in your values

# Instagram Credentials
INSTAGRAM_LOGIN_USERNAME=your_instagram_username
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_instagram_business_account_id

# Facebook Credentials
FACEBOOK_PAGE_ID=your_facebook_page_id
FACEBOOK_ACCESS_TOKEN=your_facebook_page_access_token

# OpenAI Credentials
OPENAI_API_KEY=your_openai_api_key

# Google Drive Credentials
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_TOKEN_FILE=token.pickle
GOOGLE_DRIVE_NEW_CONTENT_FOLDER_ID=your_google_drive_folder_id_for_new_content
GOOGLE_DRIVE_ARCHIVED_CONTENT_FOLDER_ID=your_google_drive_folder_id_for_archived_content

# YouTube Credentials
YOUTUBE_CLIENT_SECRETS_FILE=youtube_credentials.json
YOUTUBE_TOKEN_FILE=youtube_token.pickle

# Advanced Settings (Optional)
INSTAGRAM_MIN_DELAY=2
INSTAGRAM_MAX_DELAY=6
DEFAULT_MAX_POSTS=10
"""
    
    with open(".env.template", "w") as f:
        f.write(env_template)
    print("Created .env.template")

def main():
    """Main setup function"""
    print("Setting up Instagram Business Intelligence Project")
    print("=" * 60)
    
    # Create all project files
    create_requirements_txt()
    create_config_json()
    create_n8n_workflow()
    create_readme()
    create_gitignore()
    create_env_template()
    
    # Create directories
    os.makedirs("scraped_content", exist_ok=True)
    print("Created scraped_content directory")
    
    print("\nProject setup complete!")
    print("\nNext steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. (Optional) Set up Google Drive credentials")
    print("3. (Optional) Configure n8n webhook")
    print("4. Run: python instagram_automation.py --username [target_username]")
    
    print("\nFor Google Drive integration:")
    print("   - Get credentials.json from Google Cloud Console")
    print("   - Enable Google Drive API")
    print("   - Place credentials.json in this directory")
    
    print("\nFor n8n integration:")
    print("   - Import n8n_workflow_sample.json into n8n")
    print("   - Update webhook URL in config.json")
    
    print("\nCheck README.md for detailed instructions!")

if __name__ == "__main__":
    main()
