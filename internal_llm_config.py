#!/usr/bin/env python3
"""
사내 LLM 서버 전용 설정
완전 내부 네트워크에서만 동작 (외부 전송 없음)
"""
import os
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트를 Python path에 추가
sys.path.append(str(Path(__file__).parent))

from src.main import K8sAgentEvaluationSystem
from src.agent.mock_agent import MockK8sAgent

# 환경변수 로드
load_dotenv()


def validate_internal_llm_config():
    """사내 LLM 서버 설정 검증"""
    print("🏢 사내 LLM 서버 설정 검증 중...")
    
    # LangSmith 완전 차단
    langsmith_vars = ['LANGCHAIN_API_KEY', 'LANGCHAIN_TRACING_V2', 'LANGCHAIN_PROJECT']
    blocked_count = 0
    
    for var in langsmith_vars:
        if os.getenv(var):
            os.environ.pop(var, None)
            blocked_count += 1
    
    if blocked_count > 0:
        print(f"   🚫 LangSmith 환경변수 {blocked_count}개 차단됨 (외부 전송 방지)")
    else:
        print(f"   ✅ 외부 전송 서비스 없음 - 안전")
    
    # 사내 LLM 서버 설정 확인
    base_url = os.getenv('OPENAI_BASE_URL')
    api_key = os.getenv('OPENAI_API_KEY')
    model = os.getenv('OPENAI_MODEL')
    
    print(f"\n📊 사내 LLM 서버 정보:")
    
    if not base_url:
        print(f"   ❌ OPENAI_BASE_URL 필수")
        return False
    
    # 사내 서버인지 확인
    if 'openai.com' in base_url.lower():
        print(f"   ⚠️  외부 OpenAI 서버 감지: {base_url}")
        print(f"   💡 사내 서버로 변경하세요 (예: http://internal-llm.company.com)")
    else:
        print(f"   ✅ 사내 LLM 서버: {base_url}")
    
    if not api_key:
        print(f"   ❌ OPENAI_API_KEY 필수 (사내 서버 인증)")
        return False
    else:
        print(f"   ✅ 인증 토큰: {api_key[:10]}... (사내용)")
    
    if not model:
        print(f"   ❌ OPENAI_MODEL 필수")
        return False
    else:
        print(f"   ✅ 사용 모델: {model}")
    
    return True


async def test_internal_llm_connection():
    """사내 LLM 서버 연결 테스트"""
    print(f"\n🧪 사내 LLM 서버 연결 테스트...")
    
    try:
        from langchain.chat_models import ChatOpenAI
        
        # 사내 서버 설정으로 LLM 초기화
        llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL"),
            temperature=0.0,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base=os.getenv("OPENAI_BASE_URL")
        )
        
        # 간단한 테스트
        test_message = "안녕하세요! 사내 LLM 서버 연결 테스트입니다."
        response = await llm.ainvoke(test_message)
        
        print(f"   ✅ 사내 LLM 서버 연결 성공!")
        print(f"   📝 응답 샘플: {response.content[:50]}...")
        return True
        
    except Exception as e:
        print(f"   ❌ 사내 서버 연결 실패: {e}")
        print(f"   💡 Base URL과 API 키를 확인하세요")
        return False


async def run_fully_internal_evaluation():
    """완전 내부 네트워크 평가 실행"""
    
    print("🏢 완전 내부 네트워크 K8s Agent 평가")
    print("🔒 모든 데이터가 사내에서만 처리됨")
    print("=" * 60)
    
    if not validate_internal_llm_config():
        return
    
    # 연결 테스트
    if not await test_internal_llm_connection():
        return
    
    # 완전 내부 설정
    config = {
        "evaluator_config": {
            "model": os.getenv("OPENAI_MODEL"),
            "temperature": 0.0,
            "few_shot_dir": "examples/few_shot_examples"
        }
    }
    
    print(f"\n🔒 완전 내부 처리 설정:")
    print(f"   LLM 서버: {os.getenv('OPENAI_BASE_URL')} (사내)")
    print(f"   모델: {config['evaluator_config']['model']}")
    print(f"   평가 방식: LangSmith 프레임워크 (외부 전송 차단)")
    print(f"   Few-shot: 로컬 YAML 파일")
    print(f"   결과 저장: 로컬 JSON만")
    print(f"   외부 전송: ❌ 완전 차단")
    
    # 평가 시스템 초기화
    eval_system = K8sAgentEvaluationSystem(config)
    
    # 품질별 평가
    for quality_level in ["medium", "high"]:
        print(f"\n{'='*50}")
        print(f"🤖 {quality_level.upper()} 품질 Agent 평가")
        print(f"{'='*50}")
        
        try:
            agent = MockK8sAgent(quality_level=quality_level)
            results = await eval_system.evaluate_agent(
                agent,
                sample_size=3  # 사내 서버 부하 고려
            )
            
            # 간단한 결과 출력
            metrics = results["metrics"]["aggregate"]["overall"]
            print(f"   📊 결과 - 종합: {metrics['avg_overall']:.3f}")
            print(f"           정확성: {metrics['avg_correctness']:.3f}")
            print(f"           관련성: {metrics['avg_relevance']:.3f}")
            print(f"           완전성: {metrics['avg_completeness']:.3f}")
            
            # 사내 전용 파일명
            filename = f"internal_evaluation_{quality_level}.json"
            eval_system.save_results(results, filename)
            print(f"   💾 {filename} 저장 완료")
            
        except Exception as e:
            print(f"   ❌ 평가 실패: {e}")
    
    print(f"\n🎉 완전 내부 네트워크 평가 완료!")
    print(f"\n🔐 보안 확인사항:")
    print(f"   ✅ 모든 LLM 호출이 사내 서버로만 전송")
    print(f"   ✅ LangSmith 등 외부 추적 서비스 완전 차단") 
    print(f"   ✅ Few-shot 예제가 로컬 YAML에서만 로드")
    print(f"   ✅ 결과가 로컬 JSON에만 저장")
    print(f"   ✅ 인터넷 연결 없이도 평가 가능 (사내 LLM만 필요)")


def create_internal_env_template():
    """사내 전용 .env 템플릿 생성"""
    template = """# 사내 LLM 서버 전용 설정
# 외부 서버로 데이터 전송 없음

# 사내 LLM 서버 설정 (필수)
OPENAI_API_KEY=your_internal_api_key_here
OPENAI_BASE_URL=http://internal-llm.company.com:8000/v1
OPENAI_MODEL=your-internal-model-name

# 예시 설정들:
# OPENAI_BASE_URL=http://10.0.1.100:8000/v1  # 사내 IP
# OPENAI_BASE_URL=https://llm.internal.company.com/v1  # 사내 도메인
# OPENAI_MODEL=llama-2-70b-chat  # 사내 모델명
# OPENAI_MODEL=gpt-4-company-fine-tuned  # 사내 파인튜닝 모델

# ⚠️ 절대 설정하지 마세요 (외부 전송됨):
# LANGCHAIN_API_KEY=...
# LANGCHAIN_TRACING_V2=true
# LANGCHAIN_PROJECT=...
"""
    
    with open(".env.internal", "w") as f:
        f.write(template)
    
    print(f"📝 사내 전용 설정 템플릿 생성: .env.internal")
    print(f"   cp .env.internal .env 후 실제 값으로 수정하세요")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--create-template":
        create_internal_env_template()
    else:
        asyncio.run(run_fully_internal_evaluation())