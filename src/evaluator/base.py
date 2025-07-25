from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..data.schemas import (
    K8sQuery, AgentResponse, GroundTruth, 
    EvaluationResult, TestCase
)


class BaseEvaluator(ABC):
    """Base class for all evaluators"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
    @abstractmethod
    async def evaluate_single(
        self, 
        query: K8sQuery, 
        response: AgentResponse, 
        ground_truth: GroundTruth
    ) -> EvaluationResult:
        """Evaluate a single agent response"""
        pass
    
    async def evaluate_batch(
        self, 
        test_cases: List[TestCase],
        responses: List[AgentResponse]
    ) -> List[EvaluationResult]:
        """Evaluate multiple responses"""
        results = []
        for test_case, response in zip(test_cases, responses):
            result = await self.evaluate_single(
                test_case.query, 
                response, 
                test_case.ground_truth
            )
            results.append(result)
        return results
    
    @abstractmethod
    def calculate_metrics(
        self, 
        results: List[EvaluationResult]
    ) -> Dict[str, float]:
        """Calculate aggregate metrics from evaluation results"""
        pass