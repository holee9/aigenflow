# L1-L8 구현 개선 계획

작업일: 2026-02-15
상태: 42/53 테스트 통과 (79%)

## 실패한 테스트 분석 (11개)

### 1. Core Models (1개)
**test_topic_validation**
- **원인**: `PipelineConfig`이 빈 문자열에 대해 ValueError를 발생시키지 않음
- **해결**: topic 필드에 대한 validation 로직 추가 필요
- **파일**: `src/core/models.py:PipelineConfig`

### 2. Gateway Session (4개)
**SessionManager 테스트들**
- **원인**: `__init__`에서 `settings` 파라미터 필수
- **현재 상태**: Pydantic BaseModel 상속받아 커스텀 __init__ 불가
- **해결**:
  - 옵션 A: BaseModel을 제거하고 순수 파이써 클래스로 변경
  - 옵션 B: settings를 필드가 아닌 __init__ 전용 파라미터로 유지

### 3. Pipeline Orchestrator (3개)
**PipelineOrchestrator 테스트들**
- **원인**: `template_manager`, `session_manager` 파라미터 누락
- **해결**: 테스트에서 적절한 파라미터 전달

### 4. Output (1개)
**FileExporter.test_init**
- **원인**: `output_dir`이 BaseModel 필드가 아님
- **해결**: formatter.py에서 FileExporter를 BaseModel로 변경하거나 테스트 수정

### 5. Integration (1개)
**test_full_pipeline_flow**
- **원인**: PipelineOrchestrator 파라미터 문제

## 개선 우선순위

### Phase 1: 핵심 모률 수정 (고우선)
1. **SessionManager 리팩토링**
   - BaseModel → 순수 클래스 변경
   - settings 파라미터 처리

2. **FileExporter 수정**
   - BaseModel vs 일반 클래스 결정

### Phase 2: 유회 로직 강화
3. **PipelineConfig validation**
   - topic 빈 문자열 체크

4. **PipelineOrchestrator 인터페이스 개선**
   - 필수 파라미터 처리

### Phase 3: 테스트 커버리지 개선
5. **통합 테스트 강화**
   - 실제 파이프라인 실행 테스트

## 구현 세부 사항

### SessionManager 재구현
```python
# src/gateway/session.py
class SessionManager:
    """Manage AI provider sessions with auto-recovery."""

    def __init__(self, settings: Any) -> None:
        self.settings = settings
        self.providers: dict[AgentType, BaseProvider] = {}

    def register_provider(...) -> None: ...
```

### FileExporter 옵션 선택
**옵션 A**: BaseModel 유지
```python
class FileExporter(BaseModel):
    output_dir: Path

    def save_json(self, filename: str, data: dict) -> Path:
        # self.output_dir 사용
```

**옵션 B**: 순수 클래스
```python
class FileExporter:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
```

### PipelineConfig validation 추가
```python
@field_validator("topic")
def validate_topic(cls, v: str) -> str:
    if not v or not v.strip():
        raise ValueError("topic cannot be empty")
    return v.strip()
```

## 테스트 목표
- **현재**: 42/53 (79%)
- **목표**: 50/53 (94%)
- **최정 목표**: 53/53 (100%)

## 다음 단계
1. Phase 1부터 순차적 구현
2. 각 Phase 완료 후 테스트 실행
3. 커버리지 개선 및 중간 테스트 추가
