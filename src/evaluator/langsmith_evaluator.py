import asyncio
from typing import Dict, Any, List, Optional
from uuid import uuid4
from datetime import datetime
import langsmith
from langsmith import Client
from langsmith.evaluation import evaluate, EvaluationResult as LSEvaluationResult
from langsmith.schemas import Run, Example

from .base import BaseEvaluator
from ..data.schemas import (
    K8sQuery, AgentResponse, GroundTruth, 
    EvaluationResult, TestCase
)


class LangSmithEvaluator(BaseEvaluator):
    """LangSmith-integrated evaluator with few-shot capabilities"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.client = Client()
        self.dataset_name = config.get("dataset_name", "k8s-agent-evaluation")
        self.project_name = config.get("project_name", "k8s-agent-eval")
        self._ensure_dataset()
        
    def _ensure_dataset(self):
        """Ensure LangSmith dataset exists"""
        try:
            self.dataset = self.client.read_dataset(dataset_name=self.dataset_name)
        except:
            self.dataset = self.client.create_dataset(
                dataset_name=self.dataset_name,
                description="K8s agent evaluation dataset with few-shot examples"
            )
    
    def add_few_shot_example(
        self, 
        test_case: TestCase,
        response: AgentResponse,
        evaluation: EvaluationResult
    ):
        """Add a few-shot example to LangSmith dataset"""
        example = self.client.create_example(
            dataset_id=self.dataset.id,
            inputs={
                "query_type": test_case.query.query_type,
                "user_query": test_case.query.user_query,
                "context": test_case.query.context
            },
            outputs={
                "expected_answer": test_case.ground_truth.expected_answer,
                "key_points": test_case.ground_truth.key_points,
                "agent_response": response.answer,
                "evaluation_scores": {
                    "correctness": evaluation.correctness_score,
                    "relevance": evaluation.relevance_score,
                    "completeness": evaluation.completeness_score,
                    "overall": evaluation.overall_score
                }
            },
            metadata={
                "query_id": test_case.query.query_id,
                "response_id": response.response_id,
                "evaluation_id": evaluation.evaluation_id,
                "timestamp": datetime.now().isoformat()
            }
        )
        return example
    
    def get_few_shot_examples(
        self, 
        query_type: str = None, 
        limit: int = 5
    ) -> List[Example]:
        """Retrieve few-shot examples from LangSmith"""
        examples = list(self.client.list_examples(dataset_id=self.dataset.id))
        
        if query_type:
            examples = [
                ex for ex in examples 
                if ex.inputs.get("query_type") == query_type
            ]
        
        examples.sort(
            key=lambda x: x.outputs.get("evaluation_scores", {}).get("overall", 0),
            reverse=True
        )
        
        return examples[:limit]
    
    async def evaluate_single(
        self, 
        query: K8sQuery, 
        response: AgentResponse, 
        ground_truth: GroundTruth
    ) -> EvaluationResult:
        """Evaluate using LangSmith with few-shot examples"""
        few_shot_examples = self.get_few_shot_examples(
            query_type=query.query_type.value
        )
        
        def evaluator(run: Run, example: Example) -> LSEvaluationResult:
            correctness = self._evaluate_correctness(
                run.outputs.get("answer", ""),
                example.outputs.get("expected_answer", ""),
                example.outputs.get("key_points", [])
            )
            
            relevance = self._evaluate_relevance(
                run.outputs.get("answer", ""),
                example.inputs.get("user_query", "")
            )
            
            completeness = self._evaluate_completeness(
                run.outputs.get("answer", ""),
                example.outputs.get("key_points", [])
            )
            
            return LSEvaluationResult(
                key="k8s_agent_evaluation",
                score=(correctness + relevance + completeness) / 3,
                value={
                    "correctness": correctness,
                    "relevance": relevance,
                    "completeness": completeness
                }
            )
        
        run_results = await evaluate(
            lambda inputs: {"answer": response.answer},
            data=[{
                "inputs": {
                    "query_type": query.query_type,
                    "user_query": query.user_query,
                    "context": query.context
                },
                "outputs": {
                    "expected_answer": ground_truth.expected_answer,
                    "key_points": ground_truth.key_points
                }
            }],
            evaluators=[evaluator],
            project_name=self.project_name,
            metadata={
                "few_shot_count": len(few_shot_examples),
                "query_id": query.query_id
            }
        )
        
        result = run_results[0]["evaluation_results"][0]
        scores = result.value
        
        return EvaluationResult(
            evaluation_id=str(uuid4()),
            query_id=query.query_id,
            response_id=response.response_id,
            correctness_score=scores["correctness"],
            relevance_score=scores["relevance"],
            completeness_score=scores["completeness"],
            overall_score=result.score,
            feedback={
                "langsmith_run_id": str(run_results[0]["run"].id),
                "few_shot_examples_used": len(few_shot_examples)
            }
        )
    
    def _evaluate_correctness(
        self, 
        answer: str, 
        expected: str, 
        key_points: List[str]
    ) -> float:
        """Simple correctness evaluation (can be enhanced with LLM)"""
        score = 0.0
        covered_points = sum(1 for point in key_points if point.lower() in answer.lower())
        score = covered_points / len(key_points) if key_points else 0.5
        return min(score, 1.0)
    
    def _evaluate_relevance(self, answer: str, query: str) -> float:
        """Simple relevance evaluation (can be enhanced with LLM)"""
        query_terms = set(query.lower().split())
        answer_terms = set(answer.lower().split())
        overlap = len(query_terms & answer_terms) / len(query_terms) if query_terms else 0
        return min(overlap * 2, 1.0)
    
    def _evaluate_completeness(self, answer: str, key_points: List[str]) -> float:
        """Simple completeness evaluation (can be enhanced with LLM)"""
        return self._evaluate_correctness(answer, "", key_points)
    
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