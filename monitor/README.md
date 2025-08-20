# Comet Invitation Hunter - Background Monitoring Service

This directory contains the background monitoring service that continuously searches X (Twitter) for Comet browser invitation posts and sends email notifications to verified users.

## Overview

The monitoring service implements the following workflow:

1. **Search**: Searches X using multiple Comet-related keywords simultaneously
2. **Deduplicate**: Removes duplicate posts across all keyword searches  
3. **Classify**: Identifies posts as either "free" (direct links) or "conditional" (requires actions)
4. **Store**: Saves new invitation posts to the database
5. **Notify**: Sends batched email notifications to all verified users

## Components

### PostClassifier
- Classifies posts into free vs conditional sharing
- Extracts invitation links from free sharing posts
- Identifies required actions for conditional posts

### EmailNotifier  
- Creates HTML and text email notifications
- Implements retry logic with exponential backoff
- Logs all email delivery attempts

### CometMonitor
- Coordinates the entire monitoring workflow
- Handles continuous operation with error recovery
- Manages API rate limiting and database connections

## Configuration

The service uses the following environment variables:

```bash
# Required
UTOOLS_API_KEY=your_utools_api_key
RESEND_API_KEY=your_resend_api_key
FROM_EMAIL=your_verified_email@yourdomain.com

# Optional
MONITORING_INTERVAL=300  # seconds between cycles (default: 5 minutes)
LOG_LEVEL=INFO
```

## Running the Service

### Development
```bash
# From project root
python start_monitor.py
```

### Production
```bash
# Set production environment variables
export UTOOLS_API_KEY="your_production_key"
export RESEND_API_KEY="your_resend_api_key"
export FROM_EMAIL="your_verified_email@yourdomain.com"

# Run the service
python start_monitor.py
```

## Search Keywords

The service searches for posts containing:
- `perplexity.ai/browser/claim` (direct links)
- `comet invitation`
- `comet invite`
- `comet browser invite`
- `comet access`
- `perplexity browser invite`
- `ai browser invite`

## Post Classification

### Free Sharing Posts
- Contain direct Comet invitation links: `https://www.perplexity.ai/browser/claim/[CODE]`
- Users can immediately use the invitation link
- Stored with the extracted invitation link

### Conditional Sharing Posts
- Contain keywords like "DM me", "follow and DM", "comment below"
- Must also mention Comet-related terms
- Stored with extracted conditions/requirements

## Email Notifications

- Sent after each monitoring cycle if new posts are found
- Include both free and conditional posts in a single email
- HTML format with direct links to posts and invitation links
- Retry logic handles temporary email delivery failures

## Error Handling

- API rate limiting: Graceful handling with delays between requests
- Database failures: Retry logic with exponential backoff
- Email failures: Up to 3 retry attempts per batch
- Continuous operation: Service continues running despite individual errors

## Logging

All operations are logged with appropriate levels:
- INFO: Normal operations, found posts, sent notifications
- WARNING: Rate limits, retry attempts, missing configuration
- ERROR: Failed operations, API errors, database issues
- DEBUG: Detailed classification logic, API responses

## Testing

Run the test suite:
```bash
# Unit tests
python backend/test_monitor.py

# Integration tests  
python test_monitor_integration.py
```

## Database Schema

The service uses the following database tables:

- `posts`: Stores processed invitation posts
- `users`: Verified user email addresses
- `email_logs`: Tracks notification batches and delivery status

## Requirements Coverage

This implementation satisfies the following requirements:

- **2.1**: Searches X using multiple keywords simultaneously
- **2.2**: Deduplicates posts across keyword searches  
- **2.3**: Classifies posts as free vs conditional sharing
- **2.7**: Logs errors and continues operation
- **5.2**: Handles rate limiting gracefully
- **5.3**: Implements proper error handling and logging
- **5.6**: Performs health checks and component restart