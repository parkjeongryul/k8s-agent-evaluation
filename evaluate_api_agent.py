#!/usr/bin/env python3
"""
실제 K8s Agent API를 평가하는 스크립트
"""
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트를 Python path에 추가
sys.path.append(str(Path(__file__).parent))

from src.main import K8sAgentEvaluationSystem
from src.agent.api_k8s_agent import APIK8sAgent, CustomAPIK8sAgent

# 환경변수 로드
load_dotenv()


def validate_environment():
    """환경변수 검증"""
    print("🔍 환경변수 검증 중...")
    
    # 평가용 LLM 서버 확인
    llm_vars = {
        'OPENAI_API_KEY': '🔑 평가용 사내 LLM API 키',
        'OPENAI_BASE_URL': '🌐 평가용 사내 LLM URL',
        'OPENAI_MODEL': '🤖 평가용 모델명'
    }
    
    # K8s Agent API 확인
    agent_vars = {
        'K8S_AGENT_API_URL': '🌐 K8s Agent API URL',
        'K8S_AGENT_API_KEY': '🔑 K8s Agent API 키 (선택)',
        'K8S_AGENT_TIMEOUT': '⏱️ API 타임아웃 (선택)'
    }
    
    missing = []
    
    print(f"\n📊 평가용 LLM 서버:")
    for var, desc in llm_vars.items():
        value = os.getenv(var)
        if not value and var != 'K8S_AGENT_API_KEY':
            missing.append(f"   ❌ {var}: {desc}")
        else:
            display = value[:20] + '...' if value and len(value) > 20 else value
            print(f"   ✅ {var}: {display or '미설정'}")
    
    print(f"\n🤖 K8s Agent API:")
    for var, desc in agent_vars.items():
        value = os.getenv(var)
        if not value and var == 'K8S_AGENT_API_URL':
            missing.append(f"   ❌ {var}: {desc}")
        else:
            display = value[:30] + '...' if value and len(value) > 30 else value
            print(f"   {'✅' if value else '⚪'} {var}: {display or '미설정'}")
    
    if missing:
        print(f"\n❌ 필수 환경변수 누락:")
        for m in missing:
            print(m)
        return False
    
    return True


async def test_api_connection():
    """API 연결 테스트"""
    print(f"\n🧪 K8s Agent API 연결 테스트...")
    
    agent = APIK8sAgent()
    health = await agent.health_check()
    
    if health['status'] == 'healthy':
        print(f"   ✅ API 연결 성공!")
        print(f"   📋 API 버전: {health.get('api_version', 'unknown')}")
        return True
    else:
        print(f"   ❌ API 연결 실패: {health.get('error', 'Unknown error')}")
        return False


async def evaluate_api_agent():
    """실제 API Agent 평가"""
    
    print("🚀 K8s Agent API 평가 시작")
    print("=" * 60)
    
    if not validate_environment():
        return
    
    # API 연결 테스트
    if not await test_api_connection():
        print(f"\n💡 API가 실행 중인지 확인하세요:")
        print(f"   - URL: {os.getenv('K8S_AGENT_API_URL')}")
        print(f"   - 네트워크 접근 가능 여부")
        print(f"   - 인증 설정")
        return
    
    # 평가 시스템 설정
    config = {
        "evaluator_config": {
            "model": os.getenv("OPENAI_MODEL"),
            "temperature": 0.0,
            "few_shot_dir": "examples/few_shot_examples"
        }
    }
    
    print(f"\n📋 평가 설정:")
    print(f"   평가 대상: {os.getenv('K8S_AGENT_API_URL')}")
    print(f"   평가 모델: {config['evaluator_config']['model']} (사내)")
    print(f"   Few-shot: 로컬 YAML 파일")
    
    # 평가 시스템 초기화
    eval_system = K8sAgentEvaluationSystem(config)
    
    # API Agent 생성
    api_agent = APIK8sAgent()
    
    # 평가 옵션 선택
    print(f"\n📊 평가 옵션:")
    print(f"   1. 빠른 테스트 (3개 케이스)")
    print(f"   2. 전체 테스트 (모든 케이스)")
    
    # 여기서는 빠른 테스트로 진행
    sample_size = 3
    
    print(f"\n🔄 평가 진행 중... (샘플: {sample_size}개)")
    
    try:
        # 평가 실행
        results = await eval_system.evaluate_agent(
            api_agent,
            sample_size=sample_size
        )
        
        # 결과 출력
        eval_system.print_summary(results)
        
        # 결과 저장
        filename = f"api_evaluation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        eval_system.save_results(results, filename)
        print(f"\n💾 평가 결과 저장: {filename}")
        
        # 주요 메트릭 강조
        metrics = results["metrics"]["aggregate"]["overall"]
        print(f"\n🎯 핵심 평가 결과:")
        print(f"   종합 점수: {metrics['avg_overall']:.1%}")
        print(f"   정확성: {metrics['avg_correctness']:.1%}")
        print(f"   관련성: {metrics['avg_relevance']:.1%}")
        print(f"   완전성: {metrics['avg_completeness']:.1%}")
        
    except Exception as e:
        print(f"\n❌ 평가 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


async def evaluate_custom_api():
    """커스텀 API 형식 평가 예시"""
    
    print("\n🔧 커스텀 API 형식 예시:")
    
    # 커스텀 설정
    custom_config = {
        "api_base_url": os.getenv('K8S_AGENT_API_URL'),
        "api_key": os.getenv('K8S_AGENT_API_KEY'),
        "request_format": "simple",  # simple, detailed, standard
        "response_format": "nested"   # simple, nested, standard
    }
    
    custom_agent = CustomAPIK8sAgent(custom_config)
    
    # 테스트 쿼리
    from src.data.schemas import K8sQuery, QueryType
    
    test_query = K8sQuery(
        query_id="custom_test_001",
        user_query="Pod가 Pending 상태에서 멈췄습니다. 어떻게 해결하나요?",
        query_type=QueryType.TROUBLESHOOTING,
        context={"namespace": "default", "pod_name": "test-pod"}
    )
    
    print(f"   요청 형식: {custom_config['request_format']}")
    print(f"   응답 형식: {custom_config['response_format']}")
    
    try:
        response = await custom_agent.process_query(test_query)
        print(f"   ✅ 커스텀 API 호출 성공")
        print(f"   응답: {response.answer[:100]}...")
    except Exception as e:
        print(f"   ❌ 커스텀 API 호출 실패: {e}")


if __name__ == "__main__":
    import sys
    from datetime import datetime
    
    if len(sys.argv) > 1 and sys.argv[1] == "--custom":
        # 커스텀 API 테스트
        asyncio.run(evaluate_custom_api())
    else:
        # 기본 평가 실행
        asyncio.run(evaluate_api_agent())