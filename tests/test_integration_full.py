"""
Integration test: Full pipeline execution with mocked agents (no API keys required).
Tests all 5 phases with 12 template tasks.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.models import PhaseStatus, PipelineConfig
from pipeline.orchestrator import PipelineOrchestrator


class MockAgent:
    """Mock agent for testing without real API calls."""

    agent_type: str
    task_name: str = ""
    content: str = ""
    success: bool = True
    error: str | None = None

    def __init__(self, agent_type: str, task_name: str):
        self.agent_type = agent_type
        self.task_name = task_name

    async def execute(self, request):
        """Mock execute that returns simulated response."""
        # Simulate different responses based on task
        self.task_name = request.task_name

        # Generate simulated responses
        if "brainstorm" in self.task_name:
            self.content = """
## 브레인스토밍 결과

### 1. AI 개인 비서스 매칭 추천 시스템
**핵심 기능**: 자연어 기반 개인 취향 분석 및 추천
**대상 고객**: 25-40대 자영업 전문가 및 프리랜서

### 2. 스마트폰one 통합 업무 자동화
**핵심 기능**: OCR 및 자동 분류 기능
**시장 기회**: 대규모 디지털화 트렌드

### 3. AI 영양 분석 앱세서리 최적화
**핵심 기능**: 영양 카테고리 및 분석 최적화
**가치 제안**: 100만원대 1인치 아파트 최적화
            """.strip()
            self.success = True
        elif "validate" in self.task_name:
            self.content = """
## 평가 결과

### 검토된 아이디어

| 순위 | 아이디어 | 핵심 가치 | 시장성 | 실행가능성 |
|------|--------|--------|--------|----------|
| 1 | AI 개인 비서스 | ⭐⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 2 | 스마트폰one 통합 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 3 | AI 영양 분석 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

**선택된 아이디어**: #1 AI 개인 비서스 매칭 추천 시스템
**이유**: 높은 시장성과 기술적 우위로 인해 경쟁력이 우수함
            """.strip()
            self.success = True
        elif "deep_search" in self.task_name:
            self.content = """
# 시장 조사 보고서

## 1. 시장 동향
- **성장**: AI 시장이 연평균 성장 중
- **규모**: 2030년까지 글로벌 AI 시장 규모 40% 이상
- **주요 기술**: 자연어 처리, 컴�팅 리딩, 예측 분석

## 2. 경쟁사 현황
- **1위**: ChatGPT (OpenAI)
- **2위**: Google Bard
- **3위**: Microsoft Copilot
- **점유율**: 빅테크 기업 35%, 구글 20%
            """.strip()
            self.success = True
        elif "fact_check" in self.task_name:
            self.content = """
## 팩트 체크 결과

### 검토된 사항

| 항목 | 내용 | 출처 | 신뢰도 |
|------|------|------|--------|
| 시장 규모 | 2030년 AI 시장 40% | IDC | 높음 |
| 경쟁사 점유율 | 2024년 기준 | Statista | 중간 |
            """.strip()
            self.success = True
        elif "swot" in self.task_name:
            self.content = """
## SWOT 분석 결과

### Strengths (강점)
1. **높은 시장 인지도**
   - 설명: AI 기술 트렌드를 선도적으로 보유
   - 영향도: 고

2. **OCR 기술 우위**
   - 설명: 스마트폰one 통합 OCR 엔진 최고
   - 영향도: 고

### Weaknesses (약점)
1. **초기 비용**
   - 설명: AI 모델 학습 및 추론에 비용
   - 심각도: 고

2. **기술적 난이도**
   - 설명: 빠른 기술 변화 대응 속도
   - 심각도: 중

### Opportunities (기회)
1. **AI 시장 성장**
   - 설명: 연평균 15% 이상 성장
   - 시장 규모: 추정

2. **B2B 시장 확대**
   - 설명: 기업용 AI 서비스 수요 증가
   - 시장 규모: 빠르게 확대

### Threats (위협)
1. **빅테크 경쟁**
   - 설명: 빅테크, 구글, MS 각사 경쟁
   - 대응 난이도: 고

2. **규제 강화**
   - 설명: 전통적 AI 규제 강화
   - 대응 난이도: 중
            """.strip()
            self.success = True
        elif "narrative" in self.task_name:
            self.content = """
## 전략 서사

### 핵심 스토리라인
AI 기술 우위를 활용하여 글로벌 AI 시장에서 독보적 위치를 확보하겠습니다.

### 배경
SWOT 분석 결과, 강점인 기술력과 시장 기회를 결합하여 시장 진입 전략을 수립합니다.

### 기회 포착
- **강점 활용**: OCR 및 자연어 처리 기술을 B2B 플랫폼에 통합 제공
- **시장 진입**: 초기 기업용 시장에서 중견기업 시장으로 확장

### 위험 관리
- **약점 보완**: 지속적인 R&D 투자로 기술적 난이도 해소
- **위협 대응**: 경쟁사 동향을 모니터링하며 신속 대응

### 전략 방향성
1. **차별화 전략**
   - 이유: B2B 시장에서 가격 경쟁력보다 기술력이 중요
   - 기대 효과: 차별화된 플랫폼으로 50% 이상 시장 점유

2. **플랫폼 전략**
   - 이유: 기업용 고객에게 안정적이고 사용성 높은 플랫폼 제공
   - 기대 효과: 고객 만족도 향상 및 이탈 방지
            """.strip()
            self.success = True
        elif "business_plan" in self.task_name:
            self.content = """
# 사업 계획서

## 1. 경영진 요약 (Executive Summary)
- **비전**: AI 기반 자동화 문서 관리 플랫폼
- **핵심 가치 제안**: 3년 내안기업 시장 1위 플랫폼
- **시장 기회**: 2030년까지 연 15% CAGR 성장
- **자금 요청**: 시리즈 A 투자 유치 50억원

## 2. 회사 개요
- **사명**: (주식) AigenFlow
- **비전**: AI로 문서 작업을 혁신화하고 자동화합니다.
- **핵심 가치**: 혁신, 자동화, 지능

## 3. 시장 분석
- **시장 규모**: TAM 3,000억원 (2024년 기준)
- **타겟 고객**: 문서 관리 부서 25-40대 기업
- **경쟁 현황**: 빅테크, 구글, MS 3개 경쟁사 형성

## 4. 제품/서비스
- **제품 설명**: AI 기반 통합 문서 관리 시스템
- **기술적 우위**: OCR, NLP, 자동 분류 등 핵심 기술 보유
- **로드맵**: 연간 50개 이상 신규 기능 추가

## 5. 운영 계획
- **팀 구성**: 개발팀 10명, 운영팀 5명
- **운영 프로세스**: 애자일/스프린트
- **파트너십**: 슬랙, 노션, 지라

## 6. 재무 계획
- **수익 모델**: SaaS 구독 모델
- **비용 구조**: 서버버 100%, R&D 30%, 영업 20%
- **재무 예측**: 3년간 흑자전환 100억원 매출
            """.strip()
            self.success = True
        elif "outline" in self.task_name:
            self.content = """
# 문서 개요

## 구조 안내
- 총 페이지: 50-60페이지
- 주요 섹션: 6개

## 상세 개요

### 1. 경영진 요약
- **목적**: 사업 개요 제공
- **핵심 내용**: 비전, 핵심 가치, 시장 기회
- **길이**: 2-3페이지

### 2. 회사 개요
- **목적**: 회사 소개 및 비전 설명
- **핵심 내용**: 사명, 비전, 핵심 가치
- **길이**: 3-5페이지

### 3. 시장 분석
- **목적**: 시장 규모 및 경쟁사 분석
- **핵심 내용**: TAM, 경쟁사, 타겟 고객
- **길이**: 10-15페이지
- **시각 자료**: 시장 규모 차트, 경쟁사 비교표

### 4. 제품/서비스
- **목적**: 제품 기능 및 기술적 우위 설명
- **핵심 내용**: 핵심 기능, 가치 제안, 로드맵
- **길이**: 8-12페이지
- **시각 자료**: 제품 기능 아키텍처, 기술 스택

### 5. 운영 계획
- **목적**: 팀 구성 및 운영 프로세스 설명
- **핵심 내용**: 조직도, 파트너십, 오픈니스 방식
- **길이**: 5-8페이지
- **시각 자료**: 조직도 차트, Gantt 차트

### 6. 재무 계획
- **목적**: 수익 모델 및 비용 구조 설명
- **핵심 내용**: 수익원, 원가 구조, 영업 비율
- **길이**: 6-10페이지
- **시각 자료**: 3개년 재무 예측 그래프

### 7. 부록
- **목적**: 참고 문헌 및 자료
- **길이**: 5-10페이지
            """.strip()
            self.success = True
        elif "charts" in self.task_name:
            self.content = """
## 데이터 시각화 계획

### 차트 목록

#### 1. 시장 규모 추이
- **차트 유형**: bar
- **목적**: TAM 규모 변화 추이
- **데이터 원본**: 시장 조사 데이터

**데이터 구조**:
```json
[
  {"연도": 2024, "규모": 300},
  {"연도": 2025, "규모": 350},
  {"연도": 2026, "규모": 400},
  {"연도": 2027, "규모": 480}
]
```

#### 2. 경쟁사 점유율
- **차트 유형**: pie
- **목적**: 3개 경쟁사 시장점유율
- **데이터 원본**: 경쟁사 조사 데이터

**데이터 구조**:
```json
[
  {"기업": "빅테크", "점유율": 35},
  {"기업": "구글", "점유율": 20},
  {"기업": "MS", "점유율": 20}
]
```

#### 3. 고객 타겟별 분포
- **차트 유형**: bar
- **목적**: 타겟별 매출 비중
- **데이터 원본**: 판매 데이터

**데이터 구조**:
```json
[
  {"타겟": "대기업", "비중": 45},
  {"타겟": "중견기업", "비중": 30},
  {"타겟": "소상", "비중": 20},
  {"타겟": "프리랜서", "비중": 5}
]
```
            """.strip()
            self.success = True
        elif "verify" in self.task_name:
            self.content = """
## 팩트 체크 결과

### 확인된 사항 (Verified)
| 항목 | 주장 | 출처 | 신뢰도 |
|------|------|------|------|--------|
| 시장 규모 | IDC 2024 보고 | 높음 | 신뢰함 |
| 기술적 우위 | 빅테크 보유 특허 | 높음 | 신뢰함 |

### 추가 검증 필요 (Needs Verification)
| 항목 | 주장 | 이유 | 권장 조치 |
|------|------|------|------|----------|
| 재무 예측 | 3년 매출 100억원 | 내부 데이터 필요 | 산업부 연구 필요 |

### 수정 권장 (Recommended Changes)
1. **재무 계획**
   - 현재: "3년간 흑자전환 100억원"
   - 제안: "현실적인 목표로 50억원으로 수정"
   - 이유: 시장 상황 고려시 보수한 예측
            """.strip()
            self.success = True
        elif "final_review" in self.task_name:
            self.content = """
## 최종 리뷰 결과

### 전체 평가
- **구조**: 8/10 - 문서 구조가 탄탄함
- **명확성**: 9/10 - 내용이 매우 명확함
- **설득력**: 8/10 - 일관된 용어 사용
- **완결성**: 9/10 - 모든 섹션이 완결함

### 섹션별 피드백

#### 1. 경영진 요약
- **강점**: 명확한 비전과 가치 제시
- **개선 필요**: 시장 규모 데이터 추가 필요

#### 2. 시장 분석
- **강점**: 포�범위자료 인용
- **개선 필요**: 경쟁사 분석 방법론 추가

### 일관성 검사
- **용어**: 한국어 일관성 유지
- **스타일**: 문체와 톤 일관
- **데이터**: 데이터 인용 일관성 확인

### 필수 수정 사항
1. **시장 규모**
   - 위치: 시장 분석 섹션
   - 문제: 최신 데이터가 아님 (2024년 데이터)
   - 제안: 2025년 이상 데이터로 업데이트

2. **수익성**
   - 위치: 재무 계획 섹션
   - 문제: 매출액 100억원은 너무 높음
   - 제안: 시장 상황 고려하여 현실적인 예측으로 수정
            """.strip()
            self.success = True
        elif "polish" in self.task_name:
            self.content = """
## 최종본

# 사업 계획서

## 1. 경영진 요약 (Executive Summary)
- **비전**: AI 기반 자동화 문서 관리 플랫폼
- **핵심 가치 제안**: 3년 내안기업 시장 1위 플랫폼
- **시장 기회**: 2030년까지 연 15% CAGR 성장
- **자금 요청**: 시리즈 A 투자 유치 50억원

## 2. 회사 개요
- **사명**: (주식) AigenFlow
- **비전**: AI로 문서 작업을 혁신화하고 자동화합니다.
- **핵심 가치**: 혁신, 자동화, 지능

## 3. 시장 분석
- **시장 규모**: TAM 3,000억원 (2024년 기준)
- **타겟 고객**: 문서 관리 부서 25-40대 기업
- **경쟁 현황**: 빅테크, 구글, MS 3개 경쟁사 형성

## 4. 제품/서비스
- **제품 설명**: AI 기반 통합 문서 관리 시스템
- **기술적 우위**: OCR, NLP, 자동 분류 등 핵심 기술 보유
- **로드맵**: 연간 50개 이상 신규 기능 추가

## 5. 운영 계획
- **팀 구성**: 개발팀 10명, 운영팀 5명
- **운영 프로세스**: 애자일/스프린트
- **파트너십**: 슬랙, 노션, 지라

## 6. 재무 계획
- **수익 모델**: SaaS 구독 모델
- **비용 구조**: 서버버 100%, R&D 30%, 영업 20%
- **재무 예측**: 3년간 흑자전환 100억원 매출

## 수정 내역 (Change Log)

### 주요 수정
1. **시장 규모**
   - 이유: 최신 데이터로 업데이트 (2025년 이상)
   - 위치: 시장 분석 섹션

2. **수익성**
   - 이유: 매출액 100억원은 너무 높음
   - 위치: 재무 계획 섹션

### 미세 조정
- 오� 같이 표현 수정
- 문장 부호 정리
- 전문문 한국어화

### 적용되지 않은 피드백
- 없음 (모든 피드백 반영)
            """.strip()
            self.success = True
        else:
            self.content = f"Mock response for {self.task_name}"
            self.success = True


async def run_full_pipeline_test():
    """Run full pipeline test with all 5 phases."""
    print("=" * 60)
    print("AigenFlow 통합 파이프라인 테스트")
    print("=" * 60)

    # Create config
    config = PipelineConfig(
        topic="AI 기반 스마트폰 관리 시스템",
        doc_type="bizplan",
        language="ko"
    )

    # Create orchestrator
    orchestrator = PipelineOrchestrator()

    # Register mock agents
    from agents.router import AgentType

    for agent_type in [AgentType.CHATGPT, AgentType.CLAUDE, AgentType.GEMINI, AgentType.PERPLEXITY]:
        mock_agent = MockAgent(agent_type.value, agent_type.value)
        orchestrator.agent_router.register_agent(agent_type.value, mock_agent)

    # Create session
    session = orchestrator.create_session(config=config)
    print(f"\n[Session] ID: {session.session_id}")
    print(f"Topic: {config.topic}")
    print(f"Initial State: {session.state}")

    # Run all 5 phases
    total_phases = 5
    phase_names = {
        1: "Ideation (아이디어션)",
        2: "Research (조사)",
        3: "Strategy (전략)",
        4: "Writing (작성)",
        5: "Review (검토)"
    }

    for phase_num in range(1, total_phases + 1):
        print(f"\n{'='*60}")
        print(f"[Phase {phase_num}] {phase_names[phase_num]} 시작")

        # Create mock agent responses dictionary

        # Run phase
        result = await orchestrator.execute_phase(session, phase_num)

        print(f"Status: {result.status}")
        print(f"AI Responses: {len(result.ai_responses)}")

        # Show results
        for i, resp in enumerate(result.ai_responses):
            status_icon = "✅" if resp.success else "❌"
            content_preview = resp.content[:100].replace("\n", " ") if len(resp.content) > 100 else resp.content
            print(f"  [{i+1}] {status_icon} {resp.agent_name}:")
            print(f"      Task: {resp.task_name}")
            print(f"      Content: {len(resp.content)} chars")
            print(f"      Preview: {content_preview}...")
            if resp.error:
                print(f"      Error: {resp.error}")

        # Update session state
        session.add_result(result)

        # Break on failure
        if result.status == PhaseStatus.FAILED:
            print(f"\n{'='*60}")
            print("Phase 실패로 테스트 중단")
            break

        # Check if all phases completed successfully
        if phase_num == total_phases:
            print(f"\n{'='*60}")
            print("=" * 60)
            print("테스트 완료!")

            # Show final state

            print(f"Final State: {session.state}")
            print(f"Total Results: {len(session.results)}")

            # Count successes
            success_count = sum(
                1 for r in session.results
                if r.status == PhaseStatus.COMPLETED
            )
            print(f"성공한 Phase: {success_count}/{total_phases}")

            # Show all phase statuses
            for r in session.results:
                status_icon = "✅" if r.status == PhaseStatus.COMPLETED else "❌"
                print(f"Phase {r.phase_number} ({r.phase_name}): {status_icon} {r.status}")


if __name__ == "__main__":
    asyncio.run(run_full_pipeline_test())
