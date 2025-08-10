# Requirements Document

## Introduction

The Comet Invitation Hunter is a service that automatically tracks and monitors X (Twitter) posts containing Comet browser invitation links. Since Comet is currently in private beta with high demand, users need invitation links to access the browser. This product helps users discover both free and conditional invitation sharing posts on X and notifies them via email when new opportunities are found. The service is exclusively available to followers of @0xSky99.

## Requirements

### Requirement 1

**User Story:** As a user seeking Comet browser access, I want to provide my email and verify my X account, so that I can receive notifications when new invitation links are shared on X.

#### Acceptance Criteria

1. WHEN a user visits the website THEN the system SHALL display an email collection form
2. WHEN a user submits their email THEN the system SHALL proceed to X account verification step
3. WHEN in the verification step THEN the system SHALL ask the user to verify their X account follows @0xSky99
4. IF the user is not following @0xSky99 THEN the system SHALL display instructions to follow the account
5. WHEN the user is verified as a follower THEN the system SHALL store the email and display a success message
6. WHEN the process is complete THEN the system SHALL confirm the user will receive notifications

### Requirement 2

**User Story:** As the system administrator, I want to continuously monitor X for Comet invitation posts, so that users can be notified of new opportunities promptly.

#### Acceptance Criteria

1. WHEN the system runs THEN it SHALL search X using multiple Comet invitation keywords simultaneously
2. WHEN search results are collected from all keywords THEN the system SHALL deduplicate posts across all keyword searches
3. WHEN deduplication is complete THEN the system SHALL iterate through all posts one by one
4. WHEN processing each post THEN the system SHALL identify free sharing posts with direct invitation links in the post body
5. WHEN processing each post THEN the system SHALL identify conditional sharing posts requiring DM, follow, or comment actions
6. WHEN a new invitation post is identified THEN the system SHALL store the post details including type (free/conditional), content, link and timestamp
7. WHEN the monitoring process encounters errors THEN the system SHALL log the errors and continue operation

### Requirement 3

**User Story:** As a verified user, I want to receive email notifications about new Comet invitation opportunities, so that I can quickly act on them before they expire.

#### Acceptance Criteria

1. WHEN the system completes a keyword search cycle THEN it SHALL check if any new sharing posts were found
2. IF new sharing posts are found THEN the system SHALL wrap them up into a single email notification
3. WHEN creating the notification email THEN the system SHALL include all discovered posts in the current search cycle with their content, links (if available), and sharing conditions
4. WHEN creating the notification email THEN the system SHALL include direct links to each X post
5. WHEN the batched email is ready THEN the system SHALL send it to all verified users
6. IF email delivery fails THEN the system SHALL retry sending up to 3 times with exponential backoff
7. WHEN notifications are sent THEN the system SHALL log successful deliveries and failures

### Requirement 4

**User Story:** As the system administrator, I want to verify user compliance with follow requirements, so that only eligible users receive the service.

#### Acceptance Criteria

1. WHEN a user provides their email THEN the system SHALL verify user's X account and  use X API to verify the user follows @0xSky99(id: 1260183271930904577).
2. WHEN verification fails THEN the system SHALL provide clear instructions on how to meet the follow requirement
3. WHEN verification succeeds THEN the system SHALL allow the user to complete the process
4. IF X API is unavailable THEN the system SHALL display an error message asking users to try again later
5. WHEN API rate limits are reached THEN the system SHALL queue verification requests and process them when limits reset

### Requirement 5

**User Story:** As a system administrator, I want to manage the backend workflow efficiently, so that the system operates reliably and scales with user demand.

#### Acceptance Criteria

1. WHEN the system starts THEN it SHALL initialize all required services including X API client, email service, and database connections
2. WHEN collecting posts THEN the system SHALL handle rate limiting from X API gracefully
3. WHEN the system encounters errors THEN it SHALL log detailed error information for debugging
4. WHEN database operations fail THEN the system SHALL retry with exponential backoff up to 3 times
5. WHEN system resources are low THEN it SHALL prioritize critical operations like user notifications
6. WHEN the system runs continuously THEN it SHALL perform health checks and restart failed components automatically

### Requirement 6

**User Story:** As a user, I want the system to handle my personal data securely, so that my privacy is protected while using the service.

#### Acceptance Criteria

1. WHEN users want to unsubscribe THEN the system SHALL provide an easy unsubscribe mechanism in all emails
2. WHEN transmitting data THEN the system SHALL use secure HTTPS connections