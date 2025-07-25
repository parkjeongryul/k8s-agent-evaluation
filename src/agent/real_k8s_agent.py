"""
실제 K8s Agent 예시 - 사내 LLM을 사용하는 진짜 Agent
"""
import asyncio
from typing import Dict, Any
from uuid import uuid4
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from ..data.schemas import K8sQuery, AgentResponse


class RealK8sAgent:
    """실제 K8s 문의 처리 Agent - 사내 LLM 사용"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # 사내 LLM 초기화
        self.llm = ChatOpenAI(
            model=self.config.get("model", "gpt-4"),
            temperature=self.config.get("temperature", 0.7)
        )
        
        # K8s 전문가 프롬프트
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 K8s 전문가입니다. 
            사용자의 K8s 관련 문의에 대해 정확하고 실용적인 해결책을 제시하세요.
            
            응답 시 다음을 포함하세요:
            1. 문제 원인 분석
            2. 단계별 해결 방법
            3. 예방 조치
            4. 관련 kubectl 명령어"""),
            
            ("human", """쿼리 타입: {query_type}
            문의 내용: {user_query}
            
            컨텍스트 정보:
            {context}
            
            위 K8s 문제에 대한 해결책을 제시해주세요.""")
        ])
        
    async def process_query(self, query: K8sQuery) -> AgentResponse:
        """실제 LLM을 사용해 K8s 문의 처리"""
        
        # 프롬프트 구성
        prompt_value = self.prompt.format_prompt(
            query_type=query.query_type if isinstance(query.query_type, str) else query.query_type.value,
            user_query=query.user_query,
            context=str(query.context)
        )
        
        # 사내 LLM 호출
        start_time = asyncio.get_event_loop().time()
        llm_response = await self.llm.ainvoke(prompt_value.to_messages())
        execution_time = asyncio.get_event_loop().time() - start_time
        
        # 신뢰도 계산 (실제로는 더 정교한 로직 필요)
        confidence_score = self._calculate_confidence(llm_response.content)
        
        # 소스 생성
        sources = self._generate_sources(query.query_type)
        
        return AgentResponse(
            response_id=str(uuid4()),
            query_id=query.query_id,
            answer=llm_response.content,
            reasoning=f"사내 LLM을 통한 실시간 분석",
            confidence_score=confidence_score,
            sources=sources,
            execution_time=execution_time
        )
    
    def _calculate_confidence(self, response: str) -> float:
        """응답 신뢰도 계산 (간단한 예시)"""
        # 실제로는 응답 길이, 구체성, 키워드 등을 분석
        if len(response) > 500 and "kubectl" in response:
            return 0.9
        elif len(response) > 200:
            return 0.7
        else:
            return 0.5
    
    def _generate_sources(self, query_type) -> list:
        """참고 소스 생성"""
        base_sources = [
            "Kubernetes Official Documentation",
            "사내 K8s 운영 가이드"
        ]
        
        type_specific = {
            "error_analysis": ["K8s 에러 코드 참조", "사내 장애 대응 매뉴얼"],
            "performance": ["K8s 성능 최적화 가이드", "모니터링 대시보드"],
            "configuration": ["K8s 리소스 스펙", "사내 설정 템플릿"]
        }
        
        query_type_str = query_type if isinstance(query_type, str) else query_type.value
        return base_sources + type_specific.get(query_type_str, [])


# 사용 예시
async def compare_agents():
    """Mock vs Real Agent 비교"""
    from .mock_agent import MockK8sAgent
    
    query = K8sQuery(
        query_id="test_001",
        user_query="Pod가 OOMKilled 에러로 재시작됩니다. 어떻게 해결하나요?",
        query_type="error_analysis",
        context={"error": "OOMKilled", "namespace": "production"}
    )
    
    print("🤖 Mock Agent (템플릿 기반):")
    mock_agent = MockK8sAgent(quality_level="high")
    mock_response = await mock_agent.process_query(query)
    print(f"응답: {mock_response.answer[:100]}...")
    print(f"LLM 호출: ❌ 없음 (템플릿만 사용)")
    
    print("\n🤖 Real Agent (사내 LLM 사용):")
    real_agent = RealK8sAgent()
    real_response = await real_agent.process_query(query)
    print(f"응답: {real_response.answer[:100]}...")
    print(f"LLM 호출: ✅ 사내 서버 1회")
    print(f"실행 시간: {real_response.execution_time:.2f}초")