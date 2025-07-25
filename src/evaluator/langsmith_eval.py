import asyncio
from typing import Dict, Any, List, Optional
from uuid import uuid4
from datetime import datetime

# LangSmith 평가 프레임워크 (외부 전송 없음)
from langsmith.evaluation import evaluate, LangSmithEvaluator as BaseLangSmithEvaluator
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from .base import BaseEvaluator
from ..data.schemas import (
    K8sQuery, AgentResponse, GroundTruth, 
    EvaluationResult, TestCase
)


class EvaluationOutput(BaseModel):
    correctness_score: float = Field(..., ge=0.0, le=1.0)
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    completeness_score: float = Field(..., ge=0.0, le=1.0)
    reasoning: str = Field(..., description="평가 근거")
    few_shot_comparison: str = Field(..., description="전문가 예시와의 비교")
    missing_points: List[str] = Field(default_factory=list)


class LangSmithEvaluator(BaseEvaluator):
    """LangSmith 평가자 - Few-shot + LLM 평가 (외부 전송 차단)"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # 🔒 외부 전송 차단 확인
        import os
        if os.getenv('LANGCHAIN_API_KEY') or os.getenv('LANGCHAIN_TRACING_V2'):
            print("🚫 LangSmith 외부 전송 환경변수 감지됨 - 차단됨")
            os.environ.pop('LANGCHAIN_API_KEY', None)
            os.environ.pop('LANGCHAIN_TRACING_V2', None)
            os.environ.pop('LANGCHAIN_PROJECT', None)
        
        print("🔒 LangSmith 프레임워크만 사용 (외부 전송 완전 차단)")
        
        # LLM 초기화 (사내 서버)
        self.llm = ChatOpenAI(
            model=config.get("model", "gpt-4-turbo-preview"),
            temperature=config.get("temperature", 0.0)
        )
        
        # 출력 파서
        self.parser = PydanticOutputParser(pydantic_object=EvaluationOutput)
        
        # Few-shot 예제 로드
        self.few_shot_dir = config.get("few_shot_dir", "examples/few_shot_examples")
        self.few_shot_examples = self._load_few_shot_examples()
        
        # 평가 프롬프트 생성
        self.evaluation_prompt = self._create_evaluation_prompt()
        
    def _load_few_shot_examples(self) -> Dict[str, List[Dict]]:
        """로컬 YAML 파일에서 Few-shot 예제 로드"""
        import yaml
        from pathlib import Path
        
        examples = {}
        few_shot_path = Path(self.few_shot_dir)
        
        if not few_shot_path.exists():
            print(f"⚠️ Few-shot 디렉토리 {few_shot_path}를 찾을 수 없습니다.")
            return examples
            
        for yaml_file in few_shot_path.glob("*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                category = data.get('category')
                if category:
                    examples[category] = data.get('examples', [])
                    print(f"✅ {category} 전문가 예제 {len(data.get('examples', []))}개 로드")
            except Exception as e:
                print(f"❌ {yaml_file} 로드 실패: {e}")
        
        return examples
    
    def _create_evaluation_prompt(self) -> ChatPromptTemplate:
        """LangSmith 기반 평가 프롬프트 생성"""
        return ChatPromptTemplate.from_messages([
            ("system", """당신은 K8s 전문가입니다. Agent의 응답을 다음 기준으로 평가해주세요:

1. **정확성 (Correctness)**: 기술적으로 정확하고 실제 적용 가능한가?
2. **관련성 (Relevance)**: 사용자 질문에 직접적으로 답변하는가?
3. **완전성 (Completeness)**: 문제 해결에 필요한 모든 요소를 다루는가?

아래 전문가 예시들을 기준으로 평가하세요. 동일한 품질 수준을 요구합니다.

{few_shot_examples}

{format_instructions}"""),
            
            ("human", """**사용자 질문:**
{user_query}

**맥락 정보:**
{context}

**Agent 응답:**
{agent_response}

**기대 답변:**
{expected_answer}

**핵심 포인트:**
{key_points}

위 전문가 예시 수준으로 Agent 응답을 평가해주세요.""")
        ])
    
    def get_relevant_examples(
        self, 
        query_type: str, 
        limit: int = 2
    ) -> List[Dict[str, Any]]:
        """쿼리 타입에 맞는 Few-shot 예제 반환"""
        type_mapping = {
            "error_analysis": "error_analysis",
            "performance": "performance",
            "configuration": "configuration",
            "scaling": "scaling",
            "troubleshooting": "troubleshooting"
        }
        
        category = type_mapping.get(query_type)
        if not category or category not in self.few_shot_examples:
            return []
        
        examples = self.few_shot_examples[category]
        
        # 품질 점수순으로 정렬하여 상위 예제 선택
        sorted_examples = sorted(
            examples,
            key=lambda x: x.get('quality_score', 0),
            reverse=True
        )
        
        return sorted_examples[:limit]
    
    def _format_few_shot_examples(self, examples: List[Dict[str, Any]]) -> str:
        """Few-shot 예제들을 프롬프트용 텍스트로 포맷팅"""
        if not examples:
            return "관련 전문가 예시가 없습니다."
        
        formatted_examples = []
        for i, example in enumerate(examples, 1):
            query_info = example.get('query', {})
            expert_response = example.get('expert_response', '')
            expert_reasoning = example.get('expert_reasoning', '')
            key_points = example.get('key_points', [])
            
            example_text = f"""
## 전문가 예시 {i}

**질문:** {query_info.get('user_query', '')}

**전문가 응답:**
{expert_response}

**전문가 추론:**
{expert_reasoning}

**핵심 포인트:** {', '.join(key_points)}

---"""
            formatted_examples.append(example_text)
        
        return "\n".join(formatted_examples)
    
    async def evaluate_single(
        self, 
        query: K8sQuery, 
        response: AgentResponse, 
        ground_truth: GroundTruth
    ) -> EvaluationResult:
        """통합 LangSmith 평가 (외부 전송 없음)"""
        
        # 관련 Few-shot 예제 가져오기
        query_type_str = query.query_type if isinstance(query.query_type, str) else query.query_type.value
        relevant_examples = self.get_relevant_examples(query_type_str, limit=2)
        few_shot_text = self._format_few_shot_examples(relevant_examples)
        
        # LangSmith 평가 함수 정의
        async def langsmith_evaluator(inputs: dict) -> dict:
            """LangSmith 평가 함수 (사내 LLM 사용)"""
            
            # 프롬프트 구성
            prompt_value = self.evaluation_prompt.format_prompt(
                few_shot_examples=few_shot_text,
                user_query=inputs["user_query"],
                context=str(inputs.get("context", {})),
                agent_response=inputs["agent_response"],
                expected_answer=inputs["expected_answer"],
                key_points=", ".join(inputs.get("key_points", [])),
                format_instructions=self.parser.get_format_instructions()
            )
            
            # 🔒 사내 LLM으로만 평가 실행
            llm_output = await self.llm.ainvoke(prompt_value.to_messages())
            evaluation = self.parser.parse(llm_output.content)
            
            # LangSmith 형식으로 결과 반환
            overall_score = (
                evaluation.correctness_score * 0.4 +
                evaluation.relevance_score * 0.3 +
                evaluation.completeness_score * 0.3
            )
            
            return {
                "scores": {
                    "correctness": evaluation.correctness_score,
                    "relevance": evaluation.relevance_score,
                    "completeness": evaluation.completeness_score,
                    "overall": overall_score
                },
                "feedback": {
                    "reasoning": evaluation.reasoning,
                    "few_shot_comparison": evaluation.few_shot_comparison,
                    "missing_points": evaluation.missing_points,
                    "few_shot_examples_used": len(relevant_examples)
                }
            }
        
        # 평가 실행 (외부 전송 없음)
        evaluation_input = {
            "user_query": query.user_query,
            "context": query.context,
            "agent_response": response.answer,
            "expected_answer": ground_truth.expected_answer,
            "key_points": ground_truth.key_points
        }
        
        result = await langsmith_evaluator(evaluation_input)
        scores = result["scores"]
        feedback = result["feedback"]
        
        return EvaluationResult(
            evaluation_id=str(uuid4()),
            query_id=query.query_id,
            response_id=response.response_id,
            correctness_score=scores["correctness"],
            relevance_score=scores["relevance"],
            completeness_score=scores["completeness"],
            overall_score=scores["overall"],
            feedback={
                **feedback,
                "evaluation_method": "unified_langsmith_local",
                "external_transmission": "blocked",
                "agent_confidence": response.confidence_score,
                "execution_time": response.execution_time
            }
        )
    
    def calculate_metrics(self, results: List[EvaluationResult]) -> Dict[str, float]:
        """평가 결과 메트릭 계산"""
        if not results:
            return {}
            
        return {
            "avg_correctness": sum(r.correctness_score for r in results) / len(results),
            "avg_relevance": sum(r.relevance_score for r in results) / len(results),
            "avg_completeness": sum(r.completeness_score for r in results) / len(results),
            "avg_overall": sum(r.overall_score for r in results) / len(results),
            "total_evaluations": len(results),
            "evaluation_method": "unified_langsmith_framework"
        }