# Implementation Plan

- [x] 1. Set up project structure and development environment
  - Create directory structure for frontend, backend, and monitoring services
  - Set up Python virtual environment and install dependencies (FastAPI, SQLAlchemy, requests, asyncio)
  - Set up TypeScript/Vite project for frontend with necessary dependencies
  - Create configuration files for development and production environments
  - _Requirements: 5.1_

- [x] 2. Implement database layer and data models
  - Create SQLite database schema with Users, Posts, and Email Logs tables
  - Implement SQLAlchemy ORM models for all database entities
  - Create database initialization and migration scripts
  - Write database utility functions for connection management and error handling
  - _Requirements: 1.5, 2.6, 5.4_

- [x] 3. Build Utools API integration layer
  - Create Utools API client class with proper authentication using provided API key
  - Implement search functionality using /search endpoint with complex response parsing
  - Implement follower verification using /followersids and /userByScreenNameV2 endpoints
  - Add proper error handling for API rate limiting and network failures
  - Write unit tests for API integration with mock responses
  - _Requirements: 2.1, 2.2, 4.1, 4.4, 4.5_

- [x] 4. Develop post classification and processing system
  - Implement post classification algorithm to identify free vs conditional sharing
  - Create pattern matching for Comet invitation links (https://www.perplexity.ai/browser/claim/[CODE])
  - Build post deduplication logic to handle multiple keyword searches
  - Add post storage functionality with proper data validation
  - Write comprehensive tests for classification algorithm with various post examples
  - _Requirements: 2.3, 2.4, 2.5, 2.6_

- [x] 5. Create FastAPI backend service
  - Set up FastAPI application with proper CORS configuration
  - Implement POST /api/users/verify endpoint for email collection and X verification
  - Add GET /api/health endpoint for service monitoring
  - Integrate Utools API client for follower verification
  - Add proper request validation using Pydantic models
  - Implement error handling and logging for all endpoints
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 4.1, 4.2, 4.3_

- [x] 6. Build background monitoring service
  - Create async monitoring service that runs continuously
  - Implement keyword-based search using multiple Comet-related terms
  - Add post processing pipeline: search → deduplicate → classify → store
  - Integrate email notification system for batched alerts
  - Add proper logging and error handling for continuous operation
  - _Requirements: 2.1, 2.2, 2.3, 2.7, 5.2, 5.3, 5.6_

- [x] 7. Implement Resend email notification system
  - Replace SMTP implementation with Resend HTTP API integration
  - Install resend Python package and update EmailNotifier class
  - Create professional email templates using Resend's format for invitation notifications
  - Implement batched email sending with Resend API after each search cycle
  - Add retry logic with exponential backoff for failed Resend API calls
  - Include unsubscribe mechanism and proper email headers
  - Log all Resend API delivery attempts and track email status
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 6.1_

- [x] 8. Develop frontend user interface
  - Create responsive HTML/CSS layout for email collection form
  - Implement TypeScript form validation and user interaction logic
  - Build three-step user flow: email input → X verification → success message
  - Add proper error handling and user feedback for verification failures
  - Implement loading states and user-friendly error messages
  - Set up Vite build configuration for production deployment
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.6, 4.2_

- [x] 9. Add comprehensive error handling and logging
  - Implement structured logging throughout all services
  - Add proper exception handling for database operations with retry logic
  - Create monitoring and alerting for service health checks
  - Add graceful degradation when external services are unavailable
  - Implement rate limiting protection for Utools API calls
  - _Requirements: 2.7, 4.4, 4.5, 5.2, 5.3, 5.4, 5.6_

- [x] 10. Write comprehensive tests
  - Create unit tests for all core functions (classification, API integration, database operations)
  - Write integration tests for the complete user verification flow
  - Add end-to-end tests for the monitoring and notification pipeline
  - Create mock data and responses for testing Utools API integration
  - Test email notification system with various post scenarios
  - _Requirements: All requirements validation_

- [x] 11. Set up deployment and configuration
  - Create production configuration with environment variables
  - Set up HTTPS configuration for secure data transmission
  - Configure database for production use with proper indexing
  - Add monitoring and logging for production environment
  - Create deployment scripts and documentation
  - _Requirements: 5.1, 6.2_

- [ ] 12. Perform final testing and optimization
  - Test complete system with real Utools API calls
  - Verify follower verification works correctly with @0xSky99 account
  - Test email notifications with actual Comet invitation posts
  - Optimize database queries and API call efficiency
  - Validate all user flows and error scenarios
  - _Requirements: All requirements final validation_