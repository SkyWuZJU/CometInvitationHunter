# Requirements Document

## Introduction

The email notification system for Comet Invitation Hunter is not working properly. Users who complete the verification process are not receiving email notifications when new Comet invitations are found. This feature addresses the core functionality issues preventing users from receiving timely notifications about new invitation opportunities.

## Requirements

### Requirement 1

**User Story:** As a verified user, I want my email to be properly stored in the database after completing verification, so that I can receive notifications.

#### Acceptance Criteria

1. WHEN a user completes the verification process THEN the system SHALL store their email address in the users table
2. WHEN a user's email is already in the database THEN the system SHALL acknowledge the existing registration without error
3. WHEN the database is accessed THEN it SHALL persist data across backend process restarts
4. WHEN a user's email is successfully stored THEN the system SHALL confirm the registration with a success message

### Requirement 2

**User Story:** As a system administrator, I want the monitoring service to run continuously, so that new invitation posts are detected and processed.

#### Acceptance Criteria

1. WHEN the monitoring service is started THEN it SHALL run continuously without manual intervention
2. WHEN the monitoring service encounters errors THEN it SHALL log the errors and continue running
3. WHEN the monitoring service finds new posts THEN it SHALL classify and store them in the database
4. IF the monitoring service stops unexpectedly THEN it SHALL provide clear error logs for troubleshooting

### Requirement 3

**User Story:** As a verified user, I want to receive email notifications when new Comet invitations are found, so that I can act on them quickly.

#### Acceptance Criteria

1. WHEN new invitation posts are found and classified THEN the system SHALL send email notifications to all verified users
2. WHEN sending email notifications THEN the system SHALL use the configured Resend API with proper error handling
3. IF email sending fails THEN the system SHALL retry with exponential backoff and log the failure
4. WHEN emails are sent successfully THEN the system SHALL log the batch information for tracking