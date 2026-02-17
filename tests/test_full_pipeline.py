"""
Full pipeline integration test with mocked agents.
"""
import asyncio
import sys
from pathlib import Path

# Setup path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


async def test_full_pipeline():
    """Test full pipeline with mocked agents."""
    from agents.router import AgentType
    from core.models import PhaseStatus, PipelineConfig
    from pipeline.orchestrator import PipelineOrchestrator

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
    class MockAgent:
        def __init__(self, agent_type):
            self.agent_type = agent_type

        async def execute(self, request):
            from core.models import AgentResponse
            return AgentResponse(
                agent_name=self.agent_type,
                task_name=request.task_name,
                content=f"Mock {self.agent_type} response for {request.task_name}",
                success=True
            )

    for agentType in [AgentType.CHATGPT, AgentType.CLAUDE, AgentType.GEMINI, AgentType.PERPLEXITY]:
        mock_agent = MockAgent(agentType.value)
        orchestrator.agent_router.register_agent(agentType.value, mock_agent)
        print(f"✅ {agentType.value} Mock Agent 등록 완료")

    # Create session
    session = orchestrator.create_session(config=config)
    print(f"✅ Session ID: {session.session_id}")
    print(f"   Topic: {config.topic}")
    print(f"   State: {session.state}")

    # Run all phases
    total_phases = 5
    for phase_num in range(1, total_phases + 1):
        print(f"\n{'='*60}")
        print(f"[Phase {phase_num}] 실행 시작...")
        result = await orchestrator.execute_phase(session, phase_num)
        session.add_result(result)

        status_icon = "✅" if result.status == PhaseStatus.COMPLETED else "❌"
        print(f"   상태: {result.status} {status_icon}")
        print(f"   응답 수: {len(result.ai_responses)}")

        for i, resp in enumerate(result.ai_responses):
            icon = "✅" if resp.success else "❌"
            print(f"   [{i+1}] {icon} {resp.agent_name}: {len(resp.content)} chars")

        if result.status == PhaseStatus.FAILED:
            print("   Phase 실패로 중단")
            break

    # Final state
    print(f"\n{'='*60}")
    print(f"최종 상태: {session.state}")
    print(f"총 결과 수: {len(session.results)}")

    # Summary
    success_count = sum(1 for r in session.results if r.status == PhaseStatus.COMPLETED)
    print(f"\n성공한 Phase: {success_count}/{total_phases}")


if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
