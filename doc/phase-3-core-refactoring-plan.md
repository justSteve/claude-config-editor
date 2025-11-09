# Phase 3: Core Refactoring - Detailed Implementation Plan

## Overview

Phase 3 focuses on refactoring core functionality, consolidating scanner logic, enhancing configuration management, implementing comprehensive logging, creating Pydantic data models for API validation, and building a robust validation system.

## Goals

1. **Consolidate scanner logic** into a single, well-structured module
2. **Enhance configuration management** with YAML support and better validation
3. **Implement logging throughout** the application with consistent patterns
4. **Create Pydantic data models** for API request/response validation
5. **Build validation utilities** for paths, data, and security

## Task Breakdown

### Task 3.1: Extract and Consolidate Scanner Logic

**Status**: Partially Complete
- ✅ Basic scanner exists in `src/core/scanner.py`
- ⚠️ Legacy scanner in `windows_scan.py` needs integration
- ⚠️ Path definitions are hardcoded in scanner

**Subtasks**:

#### 3.1.1: Review and Compare Scanner Implementations
- [ ] Compare `src/core/scanner.py` with `windows_scan.py`
- [ ] Identify unique features from each implementation
- [ ] Document differences and decide on consolidation strategy
- [ ] Create migration plan for any missing functionality

#### 3.1.2: Extract Path Definitions to Configuration
- [ ] Create path definition schema (Pydantic model)
- [ ] Move path definitions from `scanner.py` to configuration file
- [ ] Create `config/paths.yaml` with all path definitions
- [ ] Update scanner to load paths from configuration
- [ ] Add validation for path definitions
- [ ] Support environment-specific path overrides

#### 3.1.3: Enhance Scanner with Missing Features
- [ ] Integrate MCP log enumeration from `windows_scan.py`
- [ ] Add directory item counting (if missing)
- [ ] Improve error handling and reporting
- [ ] Add progress tracking for large scans
- [ ] Support filtering paths by category
- [ ] Add scan result caching (optional)

#### 3.1.4: Refactor Scanner Architecture
- [ ] Separate path resolution logic from scanning logic
- [ ] Create `PathResolver` class for environment variable expansion
- [ ] Create `PathScanner` class for individual path scanning
- [ ] Create `SnapshotCreator` class for snapshot orchestration
- [ ] Add dependency injection for better testability
- [ ] Improve type hints and documentation

#### 3.1.5: Update Legacy Code
- [ ] Deprecate `windows_scan.py` (mark as deprecated)
- [ ] Update `server.py` to use new scanner if needed
- [ ] Create migration guide for users of old scanner
- [ ] Add backward compatibility layer (if needed)

**Files to Modify**:
- `src/core/scanner.py` - Enhance and refactor
- `config/paths.yaml` - Create new path definitions file
- `src/core/config.py` - Add path loading functionality
- `windows_scan.py` - Mark as deprecated, add migration notice
- `server.py` - Update if still using old scanner logic

**Files to Create**:
- `config/paths.yaml` - Path definitions configuration
- `src/core/path_resolver.py` - Environment variable resolution
- `tests/test_scanner.py` - Comprehensive scanner tests
- `tests/test_path_resolver.py` - Path resolver tests

**Testing Requirements**:
- Unit tests for path resolution
- Unit tests for individual path scanning
- Integration tests for full snapshot creation
- Tests for error handling and edge cases
- Tests for configuration loading

**Acceptance Criteria**:
- [ ] All path definitions moved to configuration
- [ ] Scanner uses configuration-based paths
- [ ] All features from `windows_scan.py` integrated
- [ ] Scanner is fully tested (>80% coverage)
- [ ] Legacy code properly deprecated
- [ ] Documentation updated

---

### Task 3.2: Enhance Configuration Management

**Status**: Partially Complete
- ✅ Basic Pydantic Settings exists
- ⚠️ No YAML configuration support
- ⚠️ No environment-specific config files
- ⚠️ No configuration validation beyond Pydantic

**Subtasks**:

#### 3.2.1: Add YAML Configuration Support
- [ ] Add PyYAML dependency to requirements
- [ ] Create YAML configuration loader
- [ ] Support multiple config files (base + environment-specific)
- [ ] Implement configuration merging (base → environment → env vars)
- [ ] Add configuration file validation
- [ ] Create configuration file templates

#### 3.2.2: Create Configuration File Structure
- [ ] Create `config/development.yaml` template
- [ ] Create `config/production.yaml` template
- [ ] Create `config/testing.yaml` template
- [ ] Create `config/paths.yaml` (from Task 3.1.2)
- [ ] Create `config/logging.yaml` for logging configuration
- [ ] Document configuration file format

#### 3.2.3: Enhance Settings Class
- [ ] Add YAML file loading to Settings
- [ ] Add configuration file path detection
- [ ] Add configuration validation methods
- [ ] Add configuration reloading capability
- [ ] Add configuration export functionality
- [ ] Improve error messages for invalid configurations

#### 3.2.4: Add Configuration Utilities
- [ ] Create configuration validator
- [ ] Create configuration diff tool
- [ ] Create configuration migration tool
- [ ] Add configuration documentation generator
- [ ] Create configuration schema (JSON Schema)

#### 3.2.5: Update Configuration Usage
- [ ] Update all modules to use enhanced configuration
- [ ] Remove hardcoded configuration values
- [ ] Add configuration logging on startup
- [ ] Add configuration validation on startup
- [ ] Create configuration CLI commands

**Files to Modify**:
- `src/core/config.py` - Enhance Settings class
- `pyproject.toml` - Add PyYAML dependency
- `requirements.txt` - Add PyYAML dependency
- All modules using configuration - Update to use new system

**Files to Create**:
- `config/development.yaml` - Development configuration
- `config/production.yaml` - Production configuration
- `config/testing.yaml` - Testing configuration
- `config/paths.yaml` - Path definitions
- `config/logging.yaml` - Logging configuration
- `config/.env.example` - Environment variables template
- `src/core/config_loader.py` - YAML configuration loader
- `src/core/config_validator.py` - Configuration validator
- `tests/test_config.py` - Configuration tests
- `docs/CONFIGURATION.md` - Configuration documentation

**Testing Requirements**:
- Unit tests for YAML loading
- Unit tests for configuration merging
- Unit tests for configuration validation
- Integration tests for configuration loading
- Tests for environment-specific configurations
- Tests for configuration reloading

**Acceptance Criteria**:
- [ ] YAML configuration files created and working
- [ ] Configuration merging works correctly
- [ ] Environment-specific configs supported
- [ ] Configuration validation implemented
- [ ] All hardcoded configs removed
- [ ] Configuration documented
- [ ] Configuration tests pass

---

### Task 3.3: Implement Logging Throughout Application

**Status**: Partially Complete
- ✅ Logging setup exists in `src/utils/logger.py`
- ⚠️ Not all modules use logging consistently
- ⚠️ No structured logging (JSON format)
- ⚠️ No request logging for API
- ⚠️ No separate log files (access, error, app)

**Subtasks**:

#### 3.3.1: Enhance Logging Setup
- [ ] Add structured logging support (JSON format option)
- [ ] Add separate log handlers (app, error, access)
- [ ] Add log filtering by module
- [ ] Add log context (request ID, user, etc.)
- [ ] Add log rotation configuration
- [ ] Add log compression for old logs

#### 3.3.2: Add Logging to Core Modules
- [ ] Add logging to `src/core/scanner.py`
- [ ] Add logging to `src/core/database.py`
- [ ] Add logging to `src/core/config.py`
- [ ] Add logging to `src/core/models.py` (if needed)
- [ ] Ensure consistent log levels and messages
- [ ] Add performance logging for slow operations

#### 3.3.3: Add Logging to API Layer
- [ ] Add request logging middleware
- [ ] Add response logging
- [ ] Add error logging with stack traces
- [ ] Add access log (separate file)
- [ ] Add request ID tracking
- [ ] Add performance metrics logging

#### 3.3.4: Add Logging to CLI
- [ ] Add logging to CLI commands
- [ ] Add progress logging for long operations
- [ ] Add error logging with user-friendly messages
- [ ] Add debug logging for troubleshooting
- [ ] Ensure CLI output doesn't conflict with logs

#### 3.3.5: Create Logging Utilities
- [ ] Create log decorator for function logging
- [ ] Create context manager for operation logging
- [ ] Create log formatter utilities
- [ ] Create log analysis tools
- [ ] Add log level configuration per module

#### 3.3.6: Update Logging Configuration
- [ ] Create `config/logging.yaml` for logging config
- [ ] Support different log levels per module
- [ ] Support different log formats per handler
- [ ] Add log file path configuration
- [ ] Add log rotation configuration

**Files to Modify**:
- `src/utils/logger.py` - Enhance logging setup
- `src/core/scanner.py` - Add comprehensive logging
- `src/core/database.py` - Add database operation logging
- `src/core/config.py` - Add configuration logging
- `src/cli/commands.py` - Add CLI logging
- All API modules - Add request/response logging

**Files to Create**:
- `config/logging.yaml` - Logging configuration
- `src/utils/logging_decorators.py` - Logging decorators
- `src/utils/logging_context.py` - Logging context managers
- `src/utils/request_logger.py` - Request logging utilities
- `tests/test_logging.py` - Logging tests
- `docs/LOGGING.md` - Logging documentation

**Testing Requirements**:
- Unit tests for logging setup
- Unit tests for log handlers
- Unit tests for log formatters
- Integration tests for logging in modules
- Tests for log rotation
- Tests for structured logging

**Acceptance Criteria**:
- [ ] All modules use logging consistently
- [ ] Structured logging (JSON) supported
- [ ] Separate log files (app, error, access) working
- [ ] Request logging implemented
- [ ] Log levels configurable per module
- [ ] Logging documented
- [ ] Logging tests pass

---

### Task 3.4: Add Pydantic Data Models for API

**Status**: Not Started
- ❌ No Pydantic models for API requests/responses
- ❌ No API schema validation
- ❌ No API documentation models

**Subtasks**:

#### 3.4.1: Create Request Models
- [ ] Create snapshot creation request model
- [ ] Create snapshot query request model
- [ ] Create snapshot comparison request model
- [ ] Create path scan request model
- [ ] Create configuration update request model
- [ ] Add request validation and error handling

#### 3.4.2: Create Response Models
- [ ] Create snapshot response model
- [ ] Create snapshot list response model
- [ ] Create path response model
- [ ] Create change response model
- [ ] Create error response model
- [ ] Add response serialization

#### 3.4.3: Create API Schema Models
- [ ] Create OpenAPI schema models
- [ ] Create API documentation models
- [ ] Create API version models
- [ ] Add schema validation
- [ ] Add schema examples

#### 3.4.4: Integrate Models with API
- [ ] Update API routes to use Pydantic models
- [ ] Add request validation
- [ ] Add response serialization
- [ ] Add error handling for validation errors
- [ ] Update API documentation

#### 3.4.5: Create Model Utilities
- [ ] Create model conversion utilities (DB → API)
- [ ] Create model validation utilities
- [ ] Create model serialization utilities
- [ ] Add model versioning support
- [ ] Add model migration utilities

**Files to Create**:
- `src/core/schemas/__init__.py` - Schemas package
- `src/core/schemas/requests.py` - Request models
- `src/core/schemas/responses.py` - Response models
- `src/core/schemas/snapshots.py` - Snapshot-specific models
- `src/core/schemas/paths.py` - Path-specific models
- `src/core/schemas/changes.py` - Change-specific models
- `src/core/schemas/errors.py` - Error models
- `src/core/schemas/common.py` - Common models (pagination, filters, etc.)
- `src/core/schemas/converters.py` - DB model to API model converters
- `tests/test_schemas.py` - Schema tests

**Files to Modify**:
- `src/api/routes.py` - Use Pydantic models (when created in Phase 5)
- `src/api/server.py` - Add model validation (when created in Phase 5)

**Testing Requirements**:
- Unit tests for all request models
- Unit tests for all response models
- Unit tests for model validation
- Unit tests for model conversion
- Integration tests for API with models
- Tests for error handling

**Acceptance Criteria**:
- [ ] All API requests have Pydantic models
- [ ] All API responses have Pydantic models
- [ ] Request validation working
- [ ] Response serialization working
- [ ] Error handling implemented
- [ ] Models documented
- [ ] Model tests pass

---

### Task 3.5: Add Validation Utilities

**Status**: Not Started
- ❌ No validation utilities exist
- ❌ No path validation
- ❌ No data validation beyond Pydantic
- ❌ No security validation

**Subtasks**:

#### 3.5.1: Create Path Validators
- [ ] Create path existence validator
- [ ] Create path traversal prevention validator
- [ ] Create path permission validator
- [ ] Create path format validator
- [ ] Create Windows path validator
- [ ] Add path sanitization utilities

#### 3.5.2: Create Data Validators
- [ ] Create JSON schema validator
- [ ] Create configuration validator
- [ ] Create snapshot data validator
- [ ] Create file content validator
- [ ] Create hash validator
- [ ] Add data sanitization utilities

#### 3.5.3: Create Security Validators
- [ ] Create input sanitization validator
- [ ] Create SQL injection prevention
- [ ] Create XSS prevention validator
- [ ] Create path traversal prevention
- [ ] Create file type validator
- [ ] Create file size validator

#### 3.5.4: Create Validation Utilities
- [ ] Create validation error formatter
- [ ] Create validation result container
- [ ] Create validation decorator
- [ ] Create batch validation utility
- [ ] Add validation logging

#### 3.5.5: Integrate Validators
- [ ] Integrate path validators in scanner
- [ ] Integrate data validators in API
- [ ] Integrate security validators in API
- [ ] Add validation to configuration loading
- [ ] Add validation to database operations

**Files to Create**:
- `src/utils/validators.py` - Main validators module
- `src/utils/validators/path_validators.py` - Path validation
- `src/utils/validators/data_validators.py` - Data validation
- `src/utils/validators/security_validators.py` - Security validation
- `src/utils/validators/__init__.py` - Validators package
- `tests/test_validators.py` - Validator tests
- `tests/test_path_validators.py` - Path validator tests
- `tests/test_security_validators.py` - Security validator tests

**Files to Modify**:
- `src/core/scanner.py` - Add path validation
- `src/core/config.py` - Add configuration validation
- `src/api/routes.py` - Add request validation (when created in Phase 5)
- `src/core/database.py` - Add data validation

**Testing Requirements**:
- Unit tests for all validators
- Unit tests for validation error handling
- Integration tests for validators in use
- Tests for security validators
- Tests for edge cases
- Performance tests for validators

**Acceptance Criteria**:
- [ ] Path validators implemented and tested
- [ ] Data validators implemented and tested
- [ ] Security validators implemented and tested
- [ ] Validators integrated throughout application
- [ ] Validation errors handled properly
- [ ] Validators documented
- [ ] Validator tests pass

---

## Implementation Order

1. **Task 3.1** (Scanner Consolidation) - Foundation for other tasks
2. **Task 3.2** (Configuration Enhancement) - Needed by other tasks
3. **Task 3.3** (Logging Implementation) - Can be done in parallel
4. **Task 3.4** (Pydantic Models) - Needed for Phase 5 (API)
5. **Task 3.5** (Validators) - Can be done in parallel with 3.4

## Dependencies

### External Dependencies
- `pyyaml` - YAML configuration support
- `pydantic` - Already in use, may need updates
- `pydantic-settings` - Already in use

### Internal Dependencies
- Phase 2 (Database Layer) - Must be complete
- Phase 1 (Project Structure) - Must be complete

## Testing Strategy

### Unit Testing
- Each module should have >80% test coverage
- All validators must be tested
- All models must be tested
- All configuration loading must be tested

### Integration Testing
- Test scanner with configuration
- Test API with Pydantic models
- Test logging throughout application
- Test validators in real scenarios

### Performance Testing
- Test scanner performance with large scans
- Test configuration loading performance
- Test validator performance
- Test logging performance impact

## Documentation Requirements

### Code Documentation
- All functions must have docstrings
- All classes must have docstrings
- All modules must have module docstrings
- Type hints required for all functions

### User Documentation
- Configuration guide
- Logging guide
- API documentation (when Phase 5 is complete)
- Validation guide

### Developer Documentation
- Architecture decisions
- Module design decisions
- Testing strategies
- Contribution guidelines

## Success Metrics

1. **Code Quality**
   - >80% test coverage
   - All linters passing
   - All type checkers passing
   - No critical security issues

2. **Functionality**
   - All Phase 3 tasks completed
   - All acceptance criteria met
   - All tests passing
   - Documentation complete

3. **Performance**
   - Scanner performance maintained or improved
   - Configuration loading <100ms
   - Logging overhead <5%
   - Validator performance acceptable

## Timeline Estimate

- **Task 3.1** (Scanner Consolidation): 2-3 days
- **Task 3.2** (Configuration Enhancement): 2-3 days
- **Task 3.3** (Logging Implementation): 2-3 days
- **Task 3.4** (Pydantic Models): 2-3 days
- **Task 3.5** (Validators): 2-3 days

**Total**: 10-15 days (2-3 weeks)

## Risk Assessment

### High Risk
- **Scanner consolidation** - May break existing functionality
  - *Mitigation*: Comprehensive testing, backward compatibility layer
- **Configuration changes** - May break existing setups
  - *Mitigation*: Migration guide, backward compatibility

### Medium Risk
- **Logging performance** - May impact application performance
  - *Mitigation*: Performance testing, async logging where possible
- **Validation overhead** - May slow down operations
  - *Mitigation*: Performance testing, caching where appropriate

### Low Risk
- **Pydantic models** - Well-established library
- **Documentation** - Time-consuming but low risk

## Next Steps After Phase 3

1. **Phase 4**: CLI Enhancement (depends on Phase 3 completion)
2. **Phase 5**: API Enhancement (depends on Phase 3 completion, especially Pydantic models)
3. **Phase 6**: Testing & Documentation (can start in parallel with Phase 3)

## Notes

- This phase is critical for establishing a solid foundation
- Take time to get the architecture right
- Don't skip testing - it will save time later
- Document as you go - it's easier than retrofitting
- Consider future requirements when designing
- Keep backward compatibility in mind where possible

