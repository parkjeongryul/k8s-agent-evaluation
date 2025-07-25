import numpy as np
from typing import List, Dict, Any
from collections import defaultdict
from ..data.schemas import EvaluationResult, QueryType


class MetricsCalculator:
    """Calculate various metrics for evaluation results"""
    
    @staticmethod
    def calculate_aggregate_metrics(results: List[EvaluationResult]) -> Dict[str, Any]:
        """Calculate overall metrics across all evaluations"""
        if not results:
            return {}
        
        metrics = {
            "overall": {
                "avg_correctness": np.mean([r.correctness_score for r in results]),
                "avg_relevance": np.mean([r.relevance_score for r in results]),
                "avg_completeness": np.mean([r.completeness_score for r in results]),
                "avg_overall": np.mean([r.overall_score for r in results]),
                "std_correctness": np.std([r.correctness_score for r in results]),
                "std_relevance": np.std([r.relevance_score for r in results]),
                "std_completeness": np.std([r.completeness_score for r in results]),
                "std_overall": np.std([r.overall_score for r in results]),
                "min_overall": min(r.overall_score for r in results),
                "max_overall": max(r.overall_score for r in results),
                "total_evaluations": len(results)
            }
        }
        
        percentiles = [25, 50, 75, 90, 95]
        for p in percentiles:
            metrics["overall"][f"p{p}_overall"] = np.percentile(
                [r.overall_score for r in results], p
            )
        
        metrics["distribution"] = MetricsCalculator._calculate_score_distribution(results)
        
        return metrics
    
    @staticmethod
    def calculate_metrics_by_type(
        results: List[EvaluationResult], 
        type_mapping: Dict[str, QueryType]
    ) -> Dict[str, Dict[str, float]]:
        """Calculate metrics grouped by query type"""
        grouped_results = defaultdict(list)
        
        for result in results:
            query_type = type_mapping.get(result.query_id)
            if query_type:
                grouped_results[query_type.value].append(result)
        
        metrics_by_type = {}
        for query_type, type_results in grouped_results.items():
            metrics_by_type[query_type] = {
                "avg_correctness": np.mean([r.correctness_score for r in type_results]),
                "avg_relevance": np.mean([r.relevance_score for r in type_results]),
                "avg_completeness": np.mean([r.completeness_score for r in type_results]),
                "avg_overall": np.mean([r.overall_score for r in type_results]),
                "count": len(type_results)
            }
        
        return metrics_by_type
    
    @staticmethod
    def calculate_confidence_correlation(
        results: List[EvaluationResult],
        agent_confidences: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate correlation between agent confidence and actual performance"""
        confidences = []
        scores = []
        
        for result in results:
            agent_conf = agent_confidences.get(result.response_id)
            if agent_conf is not None:
                confidences.append(agent_conf)
                scores.append(result.overall_score)
        
        if len(confidences) < 2:
            return {"correlation": None, "sample_size": len(confidences)}
        
        correlation = np.corrcoef(confidences, scores)[0, 1]
        
        return {
            "correlation": correlation,
            "sample_size": len(confidences),
            "avg_confidence": np.mean(confidences),
            "avg_score": np.mean(scores),
            "confidence_accuracy_gap": abs(np.mean(confidences) - np.mean(scores))
        }
    
    @staticmethod
    def _calculate_score_distribution(results: List[EvaluationResult]) -> Dict[str, int]:
        """Calculate score distribution in buckets"""
        buckets = {
            "0.0-0.2": 0,
            "0.2-0.4": 0,
            "0.4-0.6": 0,
            "0.6-0.8": 0,
            "0.8-1.0": 0
        }
        
        for result in results:
            score = result.overall_score
            if score <= 0.2:
                buckets["0.0-0.2"] += 1
            elif score <= 0.4:
                buckets["0.2-0.4"] += 1
            elif score <= 0.6:
                buckets["0.4-0.6"] += 1
            elif score <= 0.8:
                buckets["0.6-0.8"] += 1
            else:
                buckets["0.8-1.0"] += 1
        
        return buckets
    
    @staticmethod
    def identify_improvement_areas(
        results: List[EvaluationResult],
        threshold: float = 0.7
    ) -> Dict[str, Any]:
        """Identify areas where the agent needs improvement"""
        low_performing = [r for r in results if r.overall_score < threshold]
        
        if not low_performing:
            return {"areas_needing_improvement": [], "low_performing_count": 0}
        
        correctness_issues = [r for r in low_performing if r.correctness_score < threshold]
        relevance_issues = [r for r in low_performing if r.relevance_score < threshold]
        completeness_issues = [r for r in low_performing if r.completeness_score < threshold]
        
        return {
            "areas_needing_improvement": {
                "correctness": len(correctness_issues) / len(results),
                "relevance": len(relevance_issues) / len(results),
                "completeness": len(completeness_issues) / len(results)
            },
            "low_performing_count": len(low_performing),
            "low_performing_percentage": len(low_performing) / len(results) * 100,
            "most_common_issue": max(
                [("correctness", len(correctness_issues)),
                 ("relevance", len(relevance_issues)),
                 ("completeness", len(completeness_issues))],
                key=lambda x: x[1]
            )[0]
        }