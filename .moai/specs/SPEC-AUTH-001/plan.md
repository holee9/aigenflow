# Implementation Plan: SPEC-AUTH-001

**SPEC ID:** SPEC-AUTH-001
**Title:** Authentication and Session Management Implementation Plan
**Created:** 2026-02-17
**Status:** Planned
**Estimated Complexity:** Medium-High
**Primary Goal:** Enable functional authentication for all four AI providers

---

## Overview

This plan outlines the implementation strategy for authentication and session management functionality across ChatGPT, Claude, Gemini, and Perplexity providers using Playwright browser automation.

---

## Implementation Phases

### Phase 1: Browser Infrastructure (Priority: Critical)

**Goal:** Establish browser initialization and management infrastructure.

**Tasks:**

1.1. Create `BrowserManager` class in `src/gateway/browser_manager.py`
- Initialize Playwright async context
- Configure anti-detection parameters
- Handle headed vs headless mode switching
- Implement resource cleanup

1.2. Update `BaseProvider` to use `BrowserManager`
- Add `browser_manager` property
- Initialize browser on first access
- Store browser context reference

1.3. Implement browser lifecycle management
- Launch browser on demand
- Close browser after operations
- Handle browser crashes gracefully

**Files to Create/Modify:**
- CREATE: `src/gateway/browser_manager.py`
- MODIFY: `src/gateway/base.py`
- MODIFY: `src/core/config.py` (add browser settings)

**Success Criteria:**
- Browser launches successfully in both headed and headless modes
- Anti-detection parameters applied correctly
- Resources cleaned up on exit

---

### Phase 2: Cookie Encryption Infrastructure (Priority: Critical)

**Goal:** Implement secure cookie storage with encryption at rest.

**Tasks:**

2.1. Create `CookieEncryption` class in `src/gateway/cookie_encryption.py`
- Generate encryption keys using Fernet (AES-256)
- Encrypt cookie dictionaries to JSON
- Decrypt JSON back to cookie dictionaries
- Handle key storage and retrieval

2.2. Implement key management
- Generate unique key per provider
- Store keys with filesystem permission 600
- Validate key file integrity

2.3. Create `CookieStorage` class in `src/gateway/cookie_storage.py`
- Save encrypted cookies to file
- Load and decrypt cookies from file
- Handle corrupted file recovery
- Manage session metadata

**Files to Create/Modify:**
- CREATE: `src/gateway/cookie_encryption.py`
- CREATE: `src/gateway/cookie_storage.py`
- MODIFY: `src/gateway/base.py` (integrate storage)

**Success Criteria:**
- Cookies encrypted before writing to disk
- Cookies decrypted correctly on reading
- Key files have correct permissions
- Corrupted files handled gracefully

---

### Phase 3: Provider Login Flows (Priority: High)

**Goal:** Implement login flow for each provider.

**Tasks:**

3.1. Implement ChatGPT login flow in `src/gateway/chatgpt_provider.py`
- Navigate to chat.openai.com
- Wait for authentication element detection
- Extract cookies on successful login
- Save encrypted session

3.2. Implement Claude login flow in `src/gateway/claude_provider.py`
- Navigate to claude.ai
- Wait for composer element detection
- Extract cookies on successful login
- Save encrypted session

3.3. Implement Gemini login flow in `src/gateway/gemini_provider.py`
- Navigate to gemini.google.com
- Wait for input element detection
- Extract cookies on successful login
- Save encrypted session

3.4. Implement Perplexity login flow in `src/gateway/perplexity_provider.py`
- Navigate to perplexity.ai
- Wait for search input detection
- Extract cookies on successful login
- Save encrypted session

**Files to Modify:**
- MODIFY: `src/gateway/chatgpt_provider.py`
- MODIFY: `src/gateway/claude_provider.py`
- MODIFY: `src/gateway/gemini_provider.py`
- MODIFY: `src/gateway/perplexity_provider.py`

**Success Criteria:**
- Each provider detects successful login
- Cookies extracted and encrypted correctly
- Session persists across CLI restarts

---

### Phase 4: Session Validation (Priority: High)

**Goal:** Implement session validation for each provider.

**Tasks:**

4.1. Implement `check_session()` for all providers
- Load cookies from storage
- Inject cookies into browser context
- Navigate to provider URL
- Check for authentication element presence
- Return validity status

4.2. Implement session metadata management
- Update `last_validated` timestamp
- Track session creation time
- Store browser version and user agent hash

4.3. Add session expiration detection
- Define session lifetime expectations per provider
- Warn users when sessions approach expiration
- Trigger re-authentication when expired

**Files to Modify:**
- MODIFY: `src/gateway/chatgpt_provider.py`
- MODIFY: `src/gateway/claude_provider.py`
- MODIFY: `src/gateway/gemini_provider.py`
- MODIFY: `src/gateway/perplexity_provider.py`
- MODIFY: `src/gateway/session.py`

**Success Criteria:**
- `check_session()` returns True for valid sessions
- `check_session()` returns False for expired sessions
- Session metadata updated correctly

---

### Phase 5: CLI Integration (Priority: Medium)

**Goal:** Complete CLI command integration for setup and check.

**Tasks:**

5.1. Update `aigenflow setup` command in `src/cli/setup.py`
- Verify Playwright browser installation
- Initialize browser in headed mode
- Call provider login flows
- Display success/failure messages
- Handle errors gracefully

5.2. Update `aigenflow check` command in `src/cli/check.py`
- Load all provider sessions
- Validate each session
- Display session status table
- Offer re-authentication for expired sessions

5.3. Update `aigenflow relogin` command in `src/cli/relogin.py`
- Force re-authentication for specified provider
- Clear existing session files
- Run login flow from scratch

**Files to Modify:**
- MODIFY: `src/cli/setup.py`
- MODIFY: `src/cli/check.py`
- MODIFY: `src/cli/relogin.py`

**Success Criteria:**
- `aigenflow setup` completes successfully for all providers
- `aigenflow check` displays accurate session status
- `aigenflow relogin` forces re-authentication

---

### Phase 6: Testing and Documentation (Priority: Medium)

**Goal:** Ensure quality and provide user documentation.

**Tasks:**

6.1. Write unit tests
- Test cookie encryption/decryption
- Test browser manager initialization
- Test session metadata serialization
- Test error handling

6.2. Write integration tests
- Test login flow with mock browser
- Test session save/load cycle
- Test multi-provider authentication

6.3. Write end-to-end tests
- Test complete setup workflow
- Test session persistence
- Test error recovery

6.4. Update user documentation
- Document `aigenflow setup` usage
- Document `aigenflow check` usage
- Document troubleshooting steps

**Files to Create/Modify:**
- CREATE: `tests/gateway/test_browser_manager.py`
- CREATE: `tests/gateway/test_cookie_encryption.py`
- CREATE: `tests/gateway/test_cookie_storage.py`
- MODIFY: `tests/gateway/test_session.py`
- MODIFY: `README.md`

**Success Criteria:**
- Test coverage >= 85%
- All tests passing
- Documentation complete and accurate

---

## Architecture Design

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          CLI Layer                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │  setup   │  │  check   │  │ relogin  │  │  config  │        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
└───────┼─────────────┼─────────────┼─────────────┼───────────────┘
        │             │             │             │
┌───────┼─────────────┼─────────────┼─────────────┼───────────────┐
│       └─────────────┴──────┬──────┴─────────────┘               │
│                     Session Manager                             │
│                    ┌──────┴──────┐                              │
│                    │   Providers │                              │
│                    └──────┬──────┘                              │
└───────────────────────────┼─────────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────────┐
│                    Gateway Layer                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ ChatGPT      │  │ Claude       │  │ Gemini       │          │
│  │ Provider     │  │ Provider     │  │ Provider     │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                   │
│  ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐             │
│  │ Perplexity  │  │   Base      │  │   Browser   │             │
│  │ Provider    │  │   Provider  │  │   Manager   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────────┐
│                    Storage Layer                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Cookie     │  │   Cookie     │  │   Session    │          │
│  │   Storage    │  │   Encryption │  │   Metadata   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
1. Login Flow:
   CLI → SessionManager → Provider → BrowserManager → Playwright
                      ↓
              CookieExtraction → CookieEncryption → CookieStorage → Disk

2. Check Session Flow:
   CLI → SessionManager → Provider → CookieStorage → Disk
                      ↓
              CookieDecryption → BrowserManager → InjectCookies
                      ↓
              NavigateToProvider → CheckAuthElement → ReturnStatus

3. Load Session Flow:
   CLI → SessionManager → Provider → CookieStorage → Disk
                      ↓
              CookieDecryption → BrowserManager → InjectCookies
                      ↓
              ReadyForUse
```

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Bot detection blocks login | Medium | High | Use headed mode for setup, anti-detection measures |
| Session expires quickly | Medium | Medium | Implement session validation, warn users |
| Encryption key loss | Low | High | Backup keys, document recovery procedure |
| Playwright installation issues | Medium | Medium | Clear installation instructions, pre-flight checks |
| Provider UI changes | Medium | High | Use stable selectors, implement fallback selectors |
| Cookie size limits | Low | Low | Compress large cookies, split if necessary |

---

## Dependencies

### Internal Dependencies

- `src/core/config.py` - Configuration management
- `src/core/logger.py` - Logging infrastructure
- `src/core/exceptions.py` - Exception definitions
- `src/gateway/base.py` - Base provider interface
- `src/gateway/session.py` - Session manager

### External Dependencies

- `playwright>=1.40.0` - Browser automation
- `cryptography>=41.0.0` - Encryption
- `pydantic>=2.9.0` - Data validation
- `typer>=0.9.0` - CLI framework
- `rich>=13.0.0` - Terminal output

---

## Rollback Plan

If authentication implementation causes critical issues:

1. Revert provider files to placeholder implementations
2. Remove cookie encryption and storage files
3. Restore CLI commands to previous state
4. Document issue and create follow-up SPEC

Rollback commands:
```bash
git revert <commit-hash>
rm -rf ~/.aigenflow/profiles/*/cookies.json*
```

---

## Performance Targets

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Login flow duration | < 60 seconds | Timer in login_flow() |
| Session validation | < 10 seconds | Timer in check_session() |
| Cookie encryption | < 100ms | Timer in encrypt/decrypt |
| Memory usage | < 500MB | Process monitoring |

---

## Definition of Done

- [ ] All 6 implementation phases completed
- [ ] Test coverage >= 85%
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Code review completed
- [ ] Manual testing completed for all providers
- [ ] Security review completed
- [ ] Performance targets met

---

**Plan Status:** Ready for Implementation
**Next Step:** Begin Phase 1 - Browser Infrastructure
