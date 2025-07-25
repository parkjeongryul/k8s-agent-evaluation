import asyncio
from typing import Dict, Any, List, Optional
from uuid import uuid4
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from .base import BaseEvaluator
from ..data.schemas import (
    K8sQuery, AgentResponse, GroundTruth, 
    EvaluationResult
)


class LLMEvaluationOutput(BaseModel):
    correctness_score: float = Field(..., ge=0.0, le=1.0)
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    completeness_score: float = Field(..., ge=0.0, le=1.0)
    reasoning: str = Field(..., description="Detailed reasoning for the scores")
    missing_points: List[str] = Field(default_factory=list)
    incorrect_points: List[str] = Field(default_factory=list)


class LLMEvaluator(BaseEvaluator):
    """LLM-based evaluator for K8s agent responses"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.llm = ChatOpenAI(
            model=config.get("model", "gpt-4-turbo-preview"),
            temperature=config.get("temperature", 0.0)
        )
        self.parser = PydanticOutputParser(pydantic_object=LLMEvaluationOutput)
        self.prompt = self._create_evaluation_prompt()
        
    def _create_evaluation_prompt(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            ("system", """You are an expert evaluator for K8s troubleshooting agents. 
            Evaluate the agent's response based on correctness, relevance, and completeness.
            
            Consider:
            1. Technical accuracy of the K8s concepts and solutions
            2. Relevance to the user's specific query
            3. Completeness in addressing all aspects of the problem
            4. Practical applicability of the solution
            
            {format_instructions}"""),
            ("human", """Query Type: {query_type}
            User Query: {user_query}
            Context: {context}
            
            Agent Response: {agent_response}
            
            Expected Answer: {expected_answer}
            Key Points to Cover: {key_points}
            
            Please evaluate the agent's response.""")
        ])
    
    async def evaluate_single(
        self, 
        query: K8sQuery, 
        response: AgentResponse, 
        ground_truth: GroundTruth
    ) -> EvaluationResult:
        prompt_value = self.prompt.format_prompt(
            query_type=query.query_type,
            user_query=query.user_query,
            context=str(query.context),
            agent_response=response.answer,
            expected_answer=ground_truth.expected_answer,
            key_points=", ".join(ground_truth.key_points),
            format_instructions=self.parser.get_format_instructions()
        )
        
        llm_output = await self.llm.ainvoke(prompt_value.to_messages())
        evaluation = self.parser.parse(llm_output.content)
        
        overall_score = (
            evaluation.correctness_score * 0.4 +
            evaluation.relevance_score * 0.3 +
            evaluation.completeness_score * 0.3
        )
        
        return EvaluationResult(
            evaluation_id=str(uuid4()),
            query_id=query.query_id,
            response_id=response.response_id,
            correctness_score=evaluation.correctness_score,
            relevance_score=evaluation.relevance_score,
            completeness_score=evaluation.completeness_score,
            overall_score=overall_score,
            feedback={
                "reasoning": evaluation.reasoning,
                "missing_points": evaluation.missing_points,
                "incorrect_points": evaluation.incorrect_points,
                "agent_confidence": response.confidence_score,
                "execution_time": response.execution_time
            }
        )
    
    def calculate_metrics(self, results: List[EvaluationResult]) -> Dict[str, float]:
        if not results:
            return {}
            
        metrics = {
            "avg_correctness": sum(r.correctness_score for r in results) / len(results),
            "avg_relevance": sum(r.relevance_score for r in results) / len(results),
            "avg_completeness": sum(r.completeness_score for r in results) / len(results),
            "avg_overall": sum(r.overall_score for r in results) / len(results),
            "total_evaluations": len(results)
        }
        
        return metrics