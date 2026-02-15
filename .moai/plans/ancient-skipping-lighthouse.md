# Plan: README.md 작성

## Context

aigenflow 프로젝트 루트에 README.md가 존재하지 않음. SPEC-PIPELINE-001이 작성 완료되어 프로젝트의 목적, 파이프라인 동작 방식, 언어 처리 흐름이 명확히 정의되어 있음. 사용자가 파이프라인 동작 방식과 언어 처리 플로우를 README에 반영해달라고 요청함.

## Approach

프로젝트 루트에 `README.md` 신규 생성. 한국어로 작성 (language.yaml documentation: "ko" 설정).

## README 구성

1. **프로젝트 소개** - aigenflow 개요, 핵심 가치
2. **AI 에이전트 배치표** - 4개 AI별 역할 및 단계별 투입 (final-summary.md 기반)
3. **파이프라인 동작 흐름** - 5단계 시각적 플로우 다이어그램 (ASCII art)
4. **언어 처리 흐름** - 입력→프롬프트→AI→출력 언어 변환 플로우
5. **CLI 사용법** - 주요 명령어 예시 (run, check, resume, config)
6. **출력 결과물 구조** - output 디렉토리 트리
7. **기술 스택** - Python 3.13+, 주요 의존성
8. **시스템 요구사항** - Proxima v3.0.0, OS, 네트워크

## Source Files

- `.moai/specs/SPEC-PIPELINE-001/spec.md` - 전체 SPEC
- `.moai/project/product.md` - 프로젝트 개요
- `final-summary.md` - 4개 AI 교차검증 결과

## Verification

- README.md 파일 생성 확인
- Markdown 렌더링 정상 여부 (테이블, 코드 블록, 다이어그램)
