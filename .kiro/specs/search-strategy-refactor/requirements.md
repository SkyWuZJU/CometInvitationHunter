# Requirements Document

## Introduction

The Comet Invitation Hunter currently has search keywords and processing strategies scattered throughout the codebase, making it difficult to quickly adjust search strategies. This refactoring will centralize all configurable search and processing parameters into easily accessible configuration files or the beginning of files, enabling rapid strategy adjustments without diving deep into the code.

## Requirements

### Requirement 1

**User Story:** As a system administrator, I want all search keywords centralized in one easily accessible location, so that I can quickly modify search terms without hunting through multiple files.

#### Acceptance Criteria

1. WHEN I need to modify search keywords THEN I SHALL find them all in a single configuration file or at the top of the main files
2. WHEN keywords are updated THEN the system SHALL use the new keywords immediately without code changes in multiple locations
3. WHEN adding new keywords THEN I SHALL only need to update one location
4. WHEN removing keywords THEN I SHALL only need to update one location

### Requirement 2

**User Story:** As a system administrator, I want post classification patterns and rules centralized, so that I can easily adjust what constitutes a valid invitation post.

#### Acceptance Criteria

1. WHEN I need to modify invitation link patterns THEN I SHALL find them in a centralized configuration
2. WHEN I need to adjust conditional sharing keywords THEN I SHALL find them in a centralized configuration  
3. WHEN I need to modify comet-related keywords THEN I SHALL find them in a centralized configuration
4. WHEN classification rules change THEN I SHALL only need to update configuration, not scattered code

### Requirement 3

**User Story:** As a system administrator, I want monitoring parameters easily configurable, so that I can adjust monitoring behavior without code changes.

#### Acceptance Criteria

1. WHEN I need to change monitoring intervals THEN I SHALL find them in configuration
2. WHEN I need to adjust API rate limiting parameters THEN I SHALL find them in configuration
3. WHEN I need to modify search result limits THEN I SHALL find them in configuration
4. WHEN I need to change retry logic parameters THEN I SHALL find them in configuration

