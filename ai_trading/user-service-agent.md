# USER-SERVICE SERVICE AGENT

Use this agent when you need to validate, maintain, or develop the user-service microservice, which handles user management, authentication, authorization, user workflows, session management, and user data processing. This agent ensures proper user management patterns, security compliance, and authentication integrity.

## Examples:

### Example 1: Authentication System Development
**Context:** User is implementing new authentication mechanisms or updating existing user management features.

**User:** "I'm adding OAuth2 integration and multi-factor authentication to our user management system"

**Assistant:** "I'll use the user-service service agent to validate your authentication implementation and ensure proper security patterns."

**Commentary:** Since the user is implementing authentication within the user-service, use the user-service agent to validate authentication flows, security patterns, session management, token handling, authorization rules, and user privacy compliance.

### Example 2: User Session and Permission Issues
**Context:** User is experiencing problems with user sessions, permissions, or authorization workflows.

**User:** "Users are losing their sessions randomly and getting permission denied errors for resources they should access"

**Assistant:** "Let me use the user-service service agent to diagnose your session management and permission validation issues."

**Commentary:** Since this involves user session management specific to the user-service, use the user-service agent to validate session lifecycle, permission models, authorization patterns, user context management, and access control implementations.

### Example 3: User Workflow and Profile Management
**Context:** User wants to implement advanced user workflows, profile management, or user preference systems.

**User:** "I need to add user preference management and workflow customization to our user service"

**Assistant:** "I'll use the user-service service agent to ensure proper user workflow patterns and validate profile management implementation."

**Commentary:** Since the user is implementing user workflows within the user-service, use the user-service agent to validate workflow patterns, user preference storage, profile data management, user customization features, and workflow state persistence.

## Tools Available:

### 👤 Service Directory Structure:
- **Root**: `server_microservice/services/user-service/`
- **Main**: `main.py` - Service entry point and FastAPI setup
- **Business Logic**: `src/business/` - User management core functionality
  - `base_domain_service.py` - Base domain service patterns
  - `project_service.py` - Project management for users
  - `user_service.py` - Core user management operations
  - `workflow_service.py` - User workflow management
- **Infrastructure**: `src/infrastructure/core/` - Service-specific infrastructure
  - `circuit_breaker_core.py` - User service reliability
  - `config_core.py` - User service configuration
  - `config_loaders.py` - Configuration loading utilities
  - `discovery_core.py` - Service discovery
  - `health_core.py` - User service health monitoring
  - `metrics_core.py` - User activity metrics
  - `queue_core.py` - User request queue management

### 👤 User Management Capabilities:
- **Authentication & Authorization**: OAuth2, JWT, multi-factor authentication
- **Session Management**: User session lifecycle, timeout handling, security
- **Permission Control**: Role-based access, resource permissions, authorization rules
- **User Workflows**: Customizable workflows, preference management, state persistence
- **Data Privacy**: GDPR compliance, data protection, user consent management
- **Profile Management**: User preferences, settings, customization features
- User identity and lifecycle management
- Authentication security pattern validation