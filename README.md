# Instagram Business Intelligence & Content Automation

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
