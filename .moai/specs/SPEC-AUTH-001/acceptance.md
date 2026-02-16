# Acceptance Criteria: SPEC-AUTH-001

**SPEC ID:** SPEC-AUTH-001
**Title:** Authentication and Session Management Acceptance Criteria
**Created:** 2026-02-17
**Status:** Planned
**Test Framework:** pytest with pytest-asyncio

---

## Test Strategy Overview

This document defines acceptance criteria using Given-When-Then (Gherkin) format for behavioral testing. All tests must pass before SPEC can be marked as complete.

---

## Functional Acceptance Criteria

### AC-AUTH-001: Setup Command - Happy Path

**Given** Playwright browser is installed
**And** No existing session files exist
**When** user runs `aigenflow setup --provider chatgpt --headed`
**Then** browser opens in headed mode
**And** user can login to ChatGPT manually
**And** system detects successful login
**And** cookies are saved to `~/.aigenflow/profiles/chatgpt/cookies.json`
**And** success message is displayed

**Test ID:** TEST-AUTH-001
**Priority:** Critical
**Automation:** Manual + Automated verification

---

### AC-AUTH-002: Setup Command - All Providers

**Given** Playwright browser is installed
**And** No existing sessions exist
**When** user runs `aigenflow setup --headed`
**Then** browser opens for each provider sequentially
**And** user can login to ChatGPT, Claude, Gemini, Perplexity
**And** all sessions are saved
**And** success message lists all authenticated providers

**Test ID:** TEST-AUTH-002
**Priority:** Critical
**Automation:** Manual + Automated verification

---

### AC-AUTH-003: Setup Command - Browser Not Installed

**Given** Playwright browser is NOT installed
**When** user runs `aigenflow setup`
**Then** error message displays installation instructions
**And** command exits with code 1
**And** no browser is launched

**Test ID:** TEST-AUTH-003
**Priority:** High
**Automation:** Automated

---

### AC-AUTH-004: Setup Command - Headed Mode

**Given** Playwright browser is installed
**And** `--headed` flag is provided
**When** user runs `aigenflow setup --headed`
**Then** browser opens in visible window mode
**And** user can see login page
**And** automation is visible to user

**Test ID:** TEST-AUTH-004
**Priority:** High
**Automation:** Manual verification

---

### AC-AUTH-005: Setup Command - Headless Mode (Default)

**Given** Playwright browser is installed
**And** no `--headed` flag is provided
**When** user runs `aigenflow setup`
**Then** browser runs in headless mode
**And** no visible window appears
**And** authentication still completes

**Test ID:** TEST-AUTH-005
**Priority:** Medium
**Automation:** Automated (with mock login)

---

### AC-AUTH-006: Check Command - All Sessions Valid

**Given** all providers have valid sessions saved
**When** user runs `aigenflow check`
**Then** table displays all providers as "Valid"
**And** last validated timestamp is shown
**And** command exits with code 0

**Test ID:** TEST-AUTH-006
**Priority:** Critical
**Automation:** Automated

---

### AC-AUTH-007: Check Command - Some Sessions Invalid

**Given** ChatGPT session is valid
**And** Claude session is expired
**When** user runs `aigenflow check`
**Then** table shows ChatGPT as "Valid"
**And** table shows Claude as "Expired"
**And** re-authentication option is offered

**Test ID:** TEST-AUTH-007
**Priority:** High
**Automation:** Automated

---

### AC-AUTH-008: Check Command - No Sessions

**Given** no session files exist
**When** user runs `aigenflow check`
**Then** table shows all providers as "No Session"
**And** setup command is suggested
**And** command exits with code 0

**Test ID:** TEST-AUTH-008
**Priority:** Medium
**Automation:** Automated

---

### AC-AUTH-009: Session Persistence

**Given** user completed setup for ChatGPT
**And** CLI exited
**When** user runs `aigenflow check` in new CLI session
**Then** ChatGPT session is still valid
**And** no re-authentication required

**Test ID:** TEST-AUTH-009
**Priority:** Critical
**Automation:** Automated

---

### AC-AUTH-010: Re-Authentication

**Given** Claude session is expired
**When** user runs `aigenflow relogin --provider claude --headed`
**Then** existing session files are cleared
**And** new login flow is initiated
**And** new session is saved

**Test ID:** TEST-AUTH-010
**Priority:** High
**Automation:** Manual + Automated verification

---

## Security Acceptance Criteria

### AC-SEC-001: Cookie Encryption

**Given** user completes setup for any provider
**When** cookies are saved to disk
**Then** cookies.json file contains encrypted data
**And** file is NOT readable as plaintext
**And** encryption key exists in cookies.json.key

**Test ID:** TEST-SEC-001
**Priority:** Critical
**Automation:** Automated

```python
# Test verification
def test_cookies_encrypted():
    cookies_file = profile_dir / "cookies.json"
    content = cookies_file.read_text()
    # Should not contain plaintext cookie names
    assert "_puid" not in content
    assert "session" not in content.lower()
    # Should be valid Fernet token
    from cryptography.fernet import Fernet
    key = (profile_dir / "cookies.json.key").read_bytes()
    cipher = Fernet(key)
    decrypted = cipher.decrypt(content.encode())
    assert decrypted is not None
```

---

### AC-SEC-002: Key File Permissions

**Given** encryption key file is created
**When** filesystem permissions are checked
**Then** key file has permissions 600 (owner read/write only)
**And** key file is not readable by other users

**Test ID:** TEST-SEC-002
**Priority:** High
**Automation:** Automated (Unix only)

```python
# Test verification (Unix)
import stat
def test_key_file_permissions():
    key_file = profile_dir / "cookies.json.key"
    mode = key_file.stat().st_mode
    assert stat.S_IMODE(mode) == 0o600
```

---

### AC-SEC-003: No Credentials in Logs

**Given** authentication process runs
**When** logs are generated
**Then** no cookie values appear in logs
**And** no session tokens appear in logs
**And** no encryption keys appear in logs

**Test ID:** TEST-SEC-003
**Priority:** Critical
**Automation:** Automated

```python
# Test verification
def test_no_credentials_in_logs(caplog):
    # Run authentication
    # Check all log records
    for record in caplog.records:
        message = record.getMessage()
        assert "session-token" not in message.lower()
        assert "cookie=" not in message.lower()
        assert "key=" not in message.lower()
```

---

### AC-SEC-004: Session Isolation

**Given** ChatGPT session is saved
**And** Claude session is saved
**When** loading sessions
**Then** ChatGPT cookies are NOT injected into Claude browser
**And** Claude cookies are NOT injected into ChatGPT browser

**Test ID:** TEST-SEC-004
**Priority:** High
**Automation:** Automated

---

## Performance Acceptance Criteria

### AC-PERF-001: Login Flow Duration

**Given** user initiates login flow
**And** user completes login within 5 minutes
**When** login flow completes
**Then** total duration is logged
**And** duration is less than 300 seconds

**Test ID:** TEST-PERF-001
**Priority:** Medium
**Automation:** Automated

---

### AC-PERF-002: Session Validation Duration

**Given** valid session exists
**When** check_session() is called
**Then** validation completes in less than 10 seconds
**And** result is returned

**Test ID:** TEST-PERF-002
**Priority:** Medium
**Automation:** Automated

---

### AC-PERF-003: Cookie Encryption Performance

**Given** 50 cookies to encrypt
**When** encryption is performed
**Then** operation completes in less than 100ms
**And** no memory leak detected

**Test ID:** TEST-PERF-003
**Priority:** Low
**Automation:** Automated

---

## Error Handling Acceptance Criteria

### AC-ERR-001: Login Timeout

**Given** user does not complete login within 5 minutes
**When** timeout occurs
**Then** error message "Login timeout exceeded" is displayed
**And** browser is closed
**And** partial session files are cleaned up

**Test ID:** TEST-ERR-001
**Priority:** High
**Automation:** Automated (with timeout mock)

---

### AC-ERR-002: Corrupted Session File

**Given** cookies.json file is corrupted
**When** check_session() is called
**Then** decryption error is caught
**And** corrupted files are deleted
**And** False is returned
**And** re-authentication is suggested

**Test ID:** TEST-ERR-002
**Priority:** High
**Automation:** Automated

---

### AC-ERR-003: Missing Encryption Key

**Given** cookies.json exists
**And** cookies.json.key is missing
**When** load_session() is called
**Then** error is logged
**And** False is returned
**And** re-authentication is suggested

**Test ID:** TEST-ERR-003
**Priority:** High
**Automation:** Automated

---

### AC-ERR-004: Network Error During Validation

**Given** session validation is in progress
**And** network becomes unavailable
**When** navigation fails
**Then** retry occurs up to 3 times
**And** error is logged
**And** False is returned

**Test ID:** TEST-ERR-004
**Priority:** Medium
**Automation:** Automated (with network mock)

---

### AC-ERR-005: Browser Crash Recovery

**Given** browser crashes during operation
**When** crash is detected
**Then** error is logged
**And** browser is restarted
**And** operation is retried once

**Test ID:** TEST-ERR-005
**Priority:** Medium
**Automation:** Automated (with crash simulation)

---

## Provider-Specific Acceptance Criteria

### AC-PROV-001: ChatGPT Authentication Detection

**Given** browser navigates to chat.openai.com
**When** user logs in successfully
**Then** system detects `textarea[data-testid="chat-input"]` element
**And** cookies are extracted within 10 seconds of detection

**Test ID:** TEST-PROV-001
**Priority:** Critical
**Automation:** Manual + Automated verification

---

### AC-PROV-002: Claude Authentication Detection

**Given** browser navigates to claude.ai
**When** user logs in successfully
**Then** system detects composer element
**And** cookies are extracted within 10 seconds of detection

**Test ID:** TEST-PROV-002
**Priority:** Critical
**Automation:** Manual + Automated verification

---

### AC-PROV-003: Gemini Authentication Detection

**Given** browser navigates to gemini.google.com
**When** user logs in successfully
**Then** system detects input textarea
**And** cookies are extracted within 10 seconds of detection

**Test ID:** TEST-PROV-003
**Priority:** Critical
**Automation:** Manual + Automated verification

---

### AC-PROV-004: Perplexity Authentication Detection

**Given** browser navigates to perplexity.ai
**When** user logs in successfully
**Then** system detects search input element
**And** cookies are extracted within 10 seconds of detection

**Test ID:** TEST-PROV-004
**Priority:** Critical
**Automation:** Manual + Automated verification

---

## Integration Acceptance Criteria

### AC-INT-001: CLI Exit Code on Success

**Given** all operations complete successfully
**When** CLI command exits
**Then** exit code is 0

**Test ID:** TEST-INT-001
**Priority:** High
**Automation:** Automated

---

### AC-INT-002: CLI Exit Code on Failure

**Given** any operation fails
**When** CLI command exits
**Then** exit code is 1
**And** error message is displayed

**Test ID:** TEST-INT-002
**Priority:** High
**Automation:** Automated

---

### AC-INT-003: Rich Output Formatting

**Given** CLI command runs
**When** output is displayed
**Then** success messages use green color
**And** error messages use red color
**And** warnings use yellow color
**And** tables are properly formatted

**Test ID:** TEST-INT-003
**Priority:** Medium
**Automation:** Automated (snapshot testing)

---

## Test Coverage Requirements

| Category | Minimum Coverage | Target Coverage |
|----------|------------------|-----------------|
| Cookie Encryption | 90% | 95% |
| Browser Manager | 85% | 90% |
| Provider Implementations | 85% | 90% |
| Session Manager | 85% | 90% |
| CLI Commands | 80% | 85% |
| **Overall** | **85%** | **90%** |

---

## Test Execution Plan

### Phase 1: Unit Tests (Automated)

Execute after each code change:
```bash
pytest tests/gateway/test_cookie_encryption.py -v
pytest tests/gateway/test_cookie_storage.py -v
pytest tests/gateway/test_browser_manager.py -v
```

### Phase 2: Integration Tests (Automated)

Execute before merge:
```bash
pytest tests/gateway/ -v --cov=src/gateway --cov-report=term-missing
```

### Phase 3: End-to-End Tests (Manual + Automated)

Execute before release:
1. Run `aigenflow setup --headed` for each provider
2. Verify login detection works
3. Verify cookies are saved
4. Run `aigenflow check` and verify output
5. Restart CLI and verify session persistence

---

## Definition of Done Checklist

- [ ] All acceptance criteria implemented
- [ ] All automated tests passing
- [ ] All manual tests completed successfully
- [ ] Test coverage >= 85%
- [ ] Security review completed
- [ ] Performance targets met
- [ ] Documentation updated
- [ ] Code review approved
- [ ] No critical bugs remaining

---

**Acceptance Criteria Status:** Ready for Implementation
**Total Test Cases:** 30
**Critical Tests:** 12
**High Priority Tests:** 10
**Medium Priority Tests:** 8
