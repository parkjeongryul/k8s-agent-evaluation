import asyncio
import json
from typing import Dict, Any, List
from datetime import datetime
import os
from dotenv import load_dotenv

from .data.test_dataset import create_test_dataset
from .agent.mock_agent import MockK8sAgent
from .evaluator.langsmith_eval import LangSmithEvaluator
from .metrics.evaluator_metrics import MetricsCalculator
from .data.schemas import EvaluationResult, AgentResponse

load_dotenv()


class K8sAgentEvaluationSystem:
    """Main evaluation system for K8s agents"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.dataset = create_test_dataset()
        self.evaluator = LangSmithEvaluator(config.get("evaluator_config", {}))
        self.metrics_calculator = MetricsCalculator()
        
    async def evaluate_agent(
        self, 
        agent: MockK8sAgent,
        sample_size: int = None
    ) -> Dict[str, Any]:
        """Evaluate an agent on the test dataset"""
        test_cases = self.dataset.test_cases[:sample_size] if sample_size else self.dataset.test_cases
        
        print(f"Starting evaluation of {len(test_cases)} test cases...")
        
        # Generate agent responses
        responses = []
        for test_case in test_cases:
            print(f"Processing query: {test_case.query.query_id}")
            response = await agent.process_query(test_case.query)
            responses.append(response)
        
        # Evaluate responses using unified LangSmith evaluator
        evaluation_results = []
        for test_case, response in zip(test_cases, responses):
            print(f"Evaluating response for: {test_case.query.query_id}")
            result = await self.evaluator.evaluate_single(
                test_case.query,
                response,
                test_case.ground_truth
            )
            evaluation_results.append(result)
        
        # Calculate metrics
        type_mapping = {tc.query.query_id: tc.query.query_type for tc in test_cases}
        agent_confidences = {r.response_id: r.confidence_score for r in responses}
        
        metrics = {
            "aggregate": self.metrics_calculator.calculate_aggregate_metrics(evaluation_results),
            "by_query_type": self.metrics_calculator.calculate_metrics_by_type(
                evaluation_results, type_mapping
            ),
            "confidence_analysis": self.metrics_calculator.calculate_confidence_correlation(
                evaluation_results, agent_confidences
            ),
            "improvement_areas": self.metrics_calculator.identify_improvement_areas(
                evaluation_results
            ),
            "evaluation_metadata": {
                "total_test_cases": len(test_cases),
                "evaluator_used": "langsmith",
                "timestamp": datetime.now().isoformat(),
                "agent_quality_level": agent.quality_level
            }
        }
        
        return {
            "results": evaluation_results,
            "metrics": metrics,
            "responses": responses
        }
    
    def save_results(self, results: Dict[str, Any], filepath: str):
        """Save evaluation results to file"""
        # Convert objects to dict for JSON serialization
        serializable_results = {
            "metrics": results["metrics"],
            "evaluation_metadata": results["metrics"]["evaluation_metadata"],
            "results_summary": [
                {
                    "query_id": r.query_id,
                    "overall_score": r.overall_score,
                    "correctness": r.correctness_score,
                    "relevance": r.relevance_score,
                    "completeness": r.completeness_score
                }
                for r in results["results"]
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        print(f"Results saved to {filepath}")
    
    def print_summary(self, results: Dict[str, Any]):
        """Print evaluation summary"""
        metrics = results["metrics"]
        
        print("\n" + "="*60)
        print("EVALUATION SUMMARY")
        print("="*60)
        
        print(f"\nAgent Quality Level: {metrics['evaluation_metadata']['agent_quality_level']}")
        print(f"Total Test Cases: {metrics['evaluation_metadata']['total_test_cases']}")
        
        print("\nOVERALL METRICS:")
        for key, value in metrics["aggregate"]["overall"].items():
            if isinstance(value, float):
                print(f"  {key}: {value:.3f}")
            else:
                print(f"  {key}: {value}")
        
        print("\nSCORE DISTRIBUTION:")
        for range_key, count in metrics["aggregate"]["distribution"].items():
            print(f"  {range_key}: {count} cases")
        
        print("\nPERFORMANCE BY QUERY TYPE:")
        for query_type, type_metrics in metrics["by_query_type"].items():
            print(f"\n  {query_type.upper()}:")
            for key, value in type_metrics.items():
                if isinstance(value, float):
                    print(f"    {key}: {value:.3f}")
                else:
                    print(f"    {key}: {value}")
        
        print("\nAREAS NEEDING IMPROVEMENT:")
        improvement = metrics["improvement_areas"]
        print(f"  Low performing cases: {improvement['low_performing_count']} ({improvement['low_performing_percentage']:.1f}%)")
        if improvement['areas_needing_improvement']:
            print(f"  Most common issue: {improvement['most_common_issue']}")
        
        print("\n" + "="*60)


async def main():
    """Main function to run the evaluation"""
    config = {
        "llm_config": {
            "model": "gpt-4-turbo-preview",
            "temperature": 0.0
        },
        "langsmith_config": {
            "dataset_name": "k8s-agent-evaluation",
            "project_name": "k8s-agent-eval"
        }
    }
    
    evaluation_system = K8sAgentEvaluationSystem(config)
    
    # Test different quality levels
    for quality_level in ["low", "medium", "high"]:
        print(f"\n\n{'='*80}")
        print(f"EVALUATING {quality_level.upper()} QUALITY AGENT")
        print(f"{'='*80}\n")
        
        agent = MockK8sAgent(quality_level=quality_level)
        results = await evaluation_system.evaluate_agent(
            agent, 
            sample_size=5  # Use subset for demo
        )
        
        evaluation_system.print_summary(results)
        evaluation_system.save_results(
            results, 
            f"evaluation_results_{quality_level}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )


if __name__ == "__main__":
    asyncio.run(main())