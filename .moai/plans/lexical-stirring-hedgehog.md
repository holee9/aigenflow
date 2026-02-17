# Plan: Fix Event Loop Closed Error in Setup Command

## Context

### Problem
`aigenflow setup` 명령이 완료된 후 "RuntimeError: Event loop is closed" 오류가 발생합니다. 이 오류는 Python이 종료될 때 백그라운드 Playwright 서브프로세스들이 cleanup을 시도하지만, 이미 닫힌 이벤트 루프에 접근하려고 하기 때문에 발생합니다.

### Root Cause
1. **setup.py line 201-202**: `asyncio.set_event_loop(None)`이 이벤트 루프를 제거
2. **BrowserPool not cleaned up**: setup 완료 후 BrowserPool singleton이 명시적으로 cleanup되지 않음
3. **Playwright subprocesses**: 브라우저 프로세스와 연결된 서브프로세스들이 백그라운드에서 계속 실행 중

### Recent Changes
- `0985ec0`: headless 파라미터 전달 수정 (ProviderContext, BaseProvider)
- `0b92487`: `from __future__ import annotations` 추가
- `edefc63`: BrowserPool 싱글톤 패턴 도입

## Implementation Plan

### Phase 1: Fix setup.py Event Loop Cleanup

**File**: `src/cli/setup.py`

**Problem**: `asyncio.set_event_loop(None)`이 너무 일찍 호출되어 백그라운드 프로세스 cleanup 방해

**Solution**:
1. `asyncio.set_event_loop(None)` 제거 또는 조건부 실행
2. setup 완료 전 BrowserPool cleanup 추가
3. 신중한 shutdown 순서: tasks → contexts → browser → playwright → loop

```python
# 수정할 부분 (lines 187-204)
finally:
    # Clean up all pending tasks
    pending = [t for t in asyncio.all_tasks(loop) if not t.done()]
    for task in pending:
        task.cancel()
    if pending:
        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))

    # FIX: Cleanup BrowserPool before closing loop
    try:
        from gateway.browser_pool import BrowserPool
        if BrowserPool._instance:
            loop.run_until_complete(BrowserPool._instance.close_all())
    except Exception as e:
        logger.warning(f"BrowserPool cleanup warning: {e}")

    loop.close()
    # FIX: Don't set event loop to None - let Python handle natural cleanup
    # asyncio.set_event_loop(None)
```

### Phase 2: Add Graceful Shutdown Handler

**File**: `src/cli/setup.py`

**Solution**: atexit 핸들러를 추가하여 프로세스 종료 시 cleanup 보장

```python
import atexit

def _cleanup_browser_pool():
    """Cleanup BrowserPool on process exit."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return
        from gateway.browser_pool import BrowserPool
        if BrowserPool._instance and not loop.is_closed():
            loop.run_until_complete(BrowserPool._instance.close_all())
    except Exception:
        pass  # Exit cleanup, ignore errors

# setup() 함수 시작 부분에 추가
atexit.register(_cleanup_browser_pool)
```

### Phase 3: Improve BrowserPool close_all()

**File**: `src/gateway/browser_pool.py`

**Current**: `close_all()` 메서드가 존재하지 않음

**Solution**: 이미 구현된 cleanup 로직을 확인하고, 없으면 추가

기존 `close_all()`이 없는 경우 다음 메서드를 추가:
```python
async def close_all(self) -> None:
    """Close all contexts and browser."""
    # ... (이미 구현된 cleanup 로직 재사용)
```

## Verification

### Test Steps
1. `$ aigenflow setup --provider claude`
2. Claude에 로그인 완료
3. "Setup completed successfully!" 메시지 확인
4. **No "Event loop is closed" error in terminal**
5. `$ aigenflow check`로 세션 유효성 확인

### Expected Behavior
- Setup 완료 후 깨끗하게 종료
- 터미널에 RuntimeError 출력 없음
- 세션이 정상적으로 저장됨

## Files to Modify

1. **src/cli/setup.py** (lines 187-204)
   - Event loop cleanup 순서 수정
   - BrowserPool cleanup 추가
   - `asyncio.set_event_loop(None)` 제거

2. **src/gateway/browser_pool.py** (if needed)
   - `close_all()` 메서드 확인/추가

## Rollback Plan

문제 발생 시 다음 커밋으로 복구:
- `9e43780` (fix: Resolve all ruff lint errors and improve code quality)
