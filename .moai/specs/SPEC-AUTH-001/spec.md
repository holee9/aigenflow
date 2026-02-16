# SPEC-AUTH-001: Authentication and Session Management

**SPEC ID:** SPEC-AUTH-001
**Title:** Authentication and Session Management for AI Providers
**Created:** 2026-02-17
**Status:** Planned
**Priority:** High
**Tags:** authentication, session-management, playwright, security, cookies
**Related SPECs:** None
**Constitution Reference:** Python 3.13+, Playwright async API, Pydantic v2.9

---

## Problem Analysis

### Current State

The aigenflow CLI has a complete command structure for setup and session management but lacks the actual authentication implementation. All four AI providers (ChatGPT, Claude, Gemini, Perplexity) have placeholder implementations with the following issues:

- `login_flow()` returns `pass` - no actual browser automation
- `check_session()` returns `False` - no session validation
- `save_session()` returns `pass` - no cookie persistence
- `load_session()` returns `False` - no session restoration

This prevents users from running `aigenflow setup` to authenticate with AI providers and maintain sessions across CLI invocations.

### Root Cause Analysis (Five Whys)

**Surface Problem:** Users cannot authenticate with AI providers via the CLI.

**First Why:** The provider classes have unimplemented authentication methods.

**Second Why:** Playwright browser automation code was never written for login flows.

**Third Why:** No cookie extraction and storage infrastructure exists.

**Fourth Why:** Session validation logic using DOM element detection is missing.

**Root Cause:** Authentication infrastructure was deferred during initial development, leaving only the interface skeleton.

### Assumptions

| Assumption | Confidence | Evidence | Risk if Wrong | Validation Method |
|------------|------------|----------|---------------|-------------------|
| Playwright can access provider login pages | High | Playwright supports Chromium, Firefox, WebKit | Medium - cloudflare protection may block automation | Test with `playwright open chat.openai.com` |
| Cookies can be extracted from browser context | High | Playwright API supports `context.cookies()` | Low - well-documented feature | Review Playwright documentation |
| Sessions remain valid for days/weeks | Medium | Personal experience with AI providers | Medium - session duration varies | Document session lifetime after implementation |
| Headless mode may trigger bot detection | Medium | Some sites detect headless browsers | High - may require headed mode for login | Test both headless and headed modes |
| User data directory provides session persistence | High | Playwright browser contexts support `user_data_dir` | Low - standard browser behavior | Test session persistence across restarts |

---

## Environment

### Technology Stack

- **Language:** Python 3.13+
- **Browser Automation:** Playwright 1.40+ (async API)
- **Data Validation:** Pydantic v2.9
- **Configuration:** Pydantic Settings with `.env` support
- **Storage:** JSON files in `~/.aigenflow/profiles/`
- **Encryption:** cryptography library for cookie encryption at rest

### Platform Constraints

- **Operating Systems:** Windows, macOS, Linux
- **Browser:** Chromium (primary), Firefox (fallback)
- **Python Version:** 3.13+ required for modern async patterns

### Provider URLs

| Provider | Base URL | Login URL |
|----------|----------|-----------|
| ChatGPT | https://chat.openai.com | https://chat.openai.com/auth/login |
| Claude | https://claude.ai | https://claude.ai/login |
| Gemini | https://gemini.google.com | https://accounts.google.com |
| Perplexity | https://www.perplexity.ai | https://www.perplexity.ai/login |

### Directory Structure

```
~/.aigenflow/
├── profiles/
│   ├── chatgpt/
│   │   ├── cookies.json          # Encrypted cookies
│   │   ├── cookies.json.key      # Encryption key
│   │   └── session_meta.json     # Session metadata
│   ├── claude/
│   │   ├── cookies.json
│   │   ├── cookies.json.key
│   │   └── session_meta.json
│   ├── gemini/
│   │   ├── cookies.json
│   │   ├── cookies.json.key
│   │   └── session_meta.json
│   └── perplexity/
│       ├── cookies.json
│       ├── cookies.json.key
│       └── session_meta.json
└── config.json                    # Global configuration
```

---

## Requirements (EARS Format)

### Ubiquitous Requirements (Always Active)

**REQ-AUTH-001:** The system **shall** always encrypt cookies before writing to disk.

**REQ-AUTH-002:** The system **shall** always validate session integrity before using stored credentials.

**REQ-AUTH-003:** The system **shall** always log authentication events with appropriate severity levels.

**REQ-AUTH-004:** The system **shall** always clean up browser resources after authentication operations.

### Event-Driven Requirements (Trigger-Response)

**REQ-AUTH-005:** **WHEN** `aigenflow setup` is invoked **THEN** the system **shall** launch a headed browser for user login.

**REQ-AUTH-006:** **WHEN** a user completes login in the browser **THEN** the system **shall** automatically detect successful authentication via DOM element presence.

**REQ-AUTH-007:** **WHEN** authentication is detected **THEN** the system **shall** extract all relevant cookies from the browser context.

**REQ-AUTH-008:** **WHEN** cookies are extracted **THEN** the system **shall** encrypt and persist them to the provider's profile directory.

**REQ-AUTH-009:** **WHEN** `aigenflow check` is invoked **THEN** the system **shall** validate all provider sessions and report status.

**REQ-AUTH-010:** **WHEN** a session expires **THEN** the system **shall** notify the user and offer re-authentication options.

**REQ-AUTH-011:** **WHEN** `load_session()` is called **THEN** the system **shall** decrypt cookies and inject them into the browser context.

**REQ-AUTH-012:** **WHEN** browser context is created **THEN** the system **shall** set appropriate anti-detection parameters.

### State-Driven Requirements (Conditional Behavior)

**REQ-AUTH-013:** **IF** `--headed` flag is set **THEN** the system **shall** run browser in visible mode for debugging.

**IF** `--headed` flag is NOT set **THEN** the system **shall** run browser in headless mode for automation.

**REQ-AUTH-014:** **IF** session file exists **AND** session is valid **THEN** the system **shall** skip login flow.

**IF** session file does NOT exist **OR** session is invalid **THEN** the system **shall** trigger login flow.

**REQ-AUTH-015:** **IF** specific provider is requested via `--provider` flag **THEN** the system **shall** authenticate only that provider.

**IF** `--provider all` is specified **THEN** the system **shall** authenticate all providers sequentially.

**REQ-AUTH-016:** **IF** Playwright browser is not installed **THEN** the system **shall** display installation instructions and exit with error code 1.

**REQ-AUTH-017:** **IF** cookie decryption fails **THEN** the system **shall** delete corrupted files and prompt for re-authentication.

**REQ-AUTH-018:** **IF** login timeout exceeds 5 minutes **THEN** the system **shall** cancel authentication and report timeout error.

### Unwanted Behavior Requirements (Prohibited Actions)

**REQ-AUTH-019:** The system **shall not** store plaintext cookies or session tokens in any file.

**REQ-AUTH-020:** The system **shall not** expose session credentials in logs or error messages.

**REQ-AUTH-021:** The system **shall not** allow concurrent login flows for the same provider.

**REQ-AUTH-022:** The system **shall not** persist browser contexts between CLI invocations (use cookie storage instead).

**REQ-AUTH-023:** The system **shall not** skip encryption when saving cookies regardless of environment.

### Optional Requirements (Enhancement Features)

**REQ-AUTH-024:** **Where possible**, the system **shall** provide automatic session refresh before expiration.

**REQ-AUTH-025:** **Where possible**, the system **shall** support session migration between machines via encrypted export.

**REQ-AUTH-026:** **Where possible**, the system **shall** detect and handle CAPTCHA challenges by alerting the user.

---

## Specifications

### SP-AUTH-001: Browser Initialization

The system shall initialize Playwright browser with the following configuration:

```python
browser_args = {
    "headless": settings.gateway_headless,
    "args": [
        "--disable-blink-features=AutomationControlled",
        "--disable-infobars",
        "--disable-dev-shm-usage",
        "--no-sandbox",
    ]
}

context_args = {
    "viewport": {"width": 1280, "height": 720},
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "locale": "en-US",
}
```

**Verification:** Browser launches without detection warnings and accepts cookies.

### SP-AUTH-002: Login Flow Implementation

Each provider shall implement the following login flow:

**Step 1: Navigate to Provider URL**
```
await page.goto(provider.base_url, wait_until="networkidle")
```

**Step 2: Wait for User Authentication**
- Detect login completion by checking for authenticated session indicators
- Provider-specific detection elements:
  - ChatGPT: Presence of chat input textarea with data-testid
  - Claude: Presence of composer textfield
  - Gemini: Presence of input textarea
  - Perplexity: Presence of search input

**Step 3: Extract Cookies**
```python
cookies = await context.cookies()
encrypted_cookies = encrypt_cookies(cookies, encryption_key)
```

**Step 4: Persist Session**
```python
save_encrypted_cookies(encrypted_cookies, profile_dir / "cookies.json")
save_session_metadata(profile_dir / "session_meta.json", metadata)
```

**Verification:** Login flow completes within 5 minutes and saves encrypted cookies.

### SP-AUTH-003: Session Validation

The system shall validate sessions using the following approach:

**Step 1: Load Cookies**
```python
encrypted_cookies = load_encrypted_cookies(profile_dir / "cookies.json")
cookies = decrypt_cookies(encrypted_cookies, encryption_key)
```

**Step 2: Inject Cookies into Context**
```python
await context.add_cookies(cookies)
```

**Step 3: Navigate and Verify**
```python
await page.goto(provider.base_url, wait_until="networkidle")
is_valid = await check_auth_element_present(page)
```

**Verification:** `check_session()` returns True for valid sessions, False for expired.

### SP-AUTH-004: Cookie Encryption

The system shall encrypt cookies using AES-256-GCM:

**Key Generation:**
```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()
cipher = Fernet(key)
```

**Encryption:**
```python
encrypted_data = cipher.encrypt(json.dumps(cookies).encode())
```

**Decryption:**
```python
decrypted_data = cipher.decrypt(encrypted_data).decode()
cookies = json.loads(decrypted_data)
```

**Key Storage:** Store encryption key in `cookies.json.key` with filesystem permissions 600.

**Verification:** Encrypted cookies cannot be read without the key file.

### SP-AUTH-005: Session Metadata Schema

Each session shall store metadata in the following schema:

```json
{
  "provider_name": "chatgpt",
  "created_at": "2026-02-17T10:30:00Z",
  "last_validated": "2026-02-17T10:35:00Z",
  "is_valid": true,
  "login_method": "manual",
  "browser_version": "chromium-121.0",
  "user_agent_hash": "sha256:abc123...",
  "cookie_count": 15,
  "encryption_version": "1.0"
}
```

**Verification:** Metadata file is created and updated on each session operation.

---

## Provider-Specific Specifications

### ChatGPT Provider

**URL:** https://chat.openai.com

**Authentication Detection:**
- Element: `textarea[data-testid="chat-input"]`
- Wait timeout: 300 seconds (5 minutes)
- Success indicator: Element visible and enabled

**Session Cookies to Capture:**
- `_puid`
- `__Secure-next-auth.session-token`
- All `openai.com` domain cookies

### Claude Provider

**URL:** https://claude.ai

**Authentication Detection:**
- Element: `div[contenteditable="true"].ProseMirror`
- Wait timeout: 300 seconds
- Success indicator: Element visible and focused

**Session Cookies to Capture:**
- `sessionKey`
- All `claude.ai` domain cookies

### Gemini Provider

**URL:** https://gemini.google.com

**Authentication Detection:**
- Element: `textarea[aria-label="Enter a prompt here"]`
- Wait timeout: 300 seconds
- Success indicator: Element visible and enabled

**Session Cookies to Capture:**
- All `google.com` domain cookies
- `SID`, `HSID`, `SSID` authentication cookies

### Perplexity Provider

**URL:** https://www.perplexity.ai

**Authentication Detection:**
- Element: `textarea[placeholder="Ask anything..."]`
- Wait timeout: 300 seconds
- Success indicator: Element visible and enabled

**Session Cookies to Capture:**
- All `perplexity.ai` domain cookies
- Session authentication tokens

---

## Security Considerations

### Encryption at Rest

All cookies and session data shall be encrypted using AES-256-GCM before writing to disk. Encryption keys shall be stored in separate files with restricted permissions (600 on Unix, owner-only on Windows).

### Key Management

- Generate unique encryption key per provider
- Store keys in `{profile_dir}/cookies.json.key`
- Never log or expose encryption keys
- Rotate keys on suspicious activity detection

### Anti-Detection Measures

The system shall implement the following anti-detection techniques:

1. **User Agent Spoofing:** Use realistic user agent strings
2. **Automation Control Disabled:** Set `--disable-blink-features=AutomationControlled`
3. **Viewport Configuration:** Use common viewport sizes
4. **Locale Consistency:** Maintain consistent locale settings

### Audit Logging

All authentication events shall be logged with the following information:

```json
{
  "timestamp": "2026-02-17T10:30:00Z",
  "event": "authentication_success",
  "provider": "chatgpt",
  "session_id": "abc123",
  "ip_address": "[REDACTED]",
  "user_agent": "Mozilla/5.0...",
  "duration_seconds": 45
}
```

---

## Error Handling

### Error Categories

| Error Code | Description | Recovery Action |
|------------|-------------|-----------------|
| AUTH_001 | Browser launch failed | Display installation instructions |
| AUTH_002 | Login timeout exceeded | Offer retry or manual cookie entry |
| AUTH_003 | Cookie encryption failed | Check filesystem permissions |
| AUTH_004 | Cookie decryption failed | Delete corrupted files, prompt re-auth |
| AUTH_005 | Session validation failed | Trigger login flow |
| AUTH_006 | Network error | Retry with exponential backoff |
| AUTH_007 | Bot detection triggered | Switch to headed mode, alert user |
| AUTH_008 | Provider unavailable | Skip provider, continue with others |

### Retry Strategy

- Maximum retries: 3
- Initial delay: 1 second
- Backoff multiplier: 2
- Maximum delay: 30 seconds

---

## Testing Strategy

### Unit Tests

- Cookie encryption/decryption round-trip
- Session metadata serialization
- Provider URL validation
- Error code generation

### Integration Tests

- Login flow with mock browser
- Session save/load cycle
- Multi-provider authentication
- Headed vs headless mode switching

### End-to-End Tests

- Complete `aigenflow setup` workflow
- Session persistence across CLI restarts
- Session expiration and re-authentication
- Error recovery scenarios

---

## Traceability Tags

**Block:** AUTH-001
**Requirements:** REQ-AUTH-001 through REQ-AUTH-026
**Specifications:** SP-AUTH-001 through SP-AUTH-005
**Test Scenarios:** TEST-AUTH-001 through TEST-AUTH-020

**Referenced By:**
- plan.md - Implementation milestones
- acceptance.md - Test scenarios and acceptance criteria

---

## Changelog

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-02-17 | SPEC Builder | Initial SPEC creation |

---

**SPEC Status:** Ready for Implementation
**Next Step:** Review plan.md for implementation milestones
