import asyncio
import random
from typing import Dict, Any, List
from uuid import uuid4
from ..data.schemas import K8sQuery, AgentResponse


class MockK8sAgent:
    """Mock K8s agent for testing the evaluation system"""
    
    def __init__(self, quality_level: str = "medium"):
        """
        quality_level: "low", "medium", "high" - determines response quality
        """
        self.quality_level = quality_level
        self.response_templates = self._load_templates()
        
    def _load_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load response templates based on query types"""
        return {
            "error_analysis": {
                "high": {
                    "template": "Based on the error '{error}', this appears to be {diagnosis}. "
                               "The root cause is likely {root_cause}. "
                               "To resolve this: 1) {step1} 2) {step2} 3) {step3}. "
                               "Additionally, check {additional_check} to prevent recurrence.",
                    "confidence": 0.95
                },
                "medium": {
                    "template": "The error '{error}' suggests {diagnosis}. "
                               "Try these steps: 1) {step1} 2) {step2}.",
                    "confidence": 0.75
                },
                "low": {
                    "template": "Error '{error}' occurred. Try restarting the pod.",
                    "confidence": 0.4
                }
            },
            "performance": {
                "high": {
                    "template": "Performance analysis shows {metric} is {status}. "
                               "This indicates {diagnosis}. Recommendations: "
                               "1) {optimization1} 2) {optimization2} "
                               "Expected improvement: {improvement}%",
                    "confidence": 0.9
                },
                "medium": {
                    "template": "The {metric} seems {status}. "
                               "Consider {optimization1} to improve performance.",
                    "confidence": 0.7
                },
                "low": {
                    "template": "Performance might be slow. Try scaling up.",
                    "confidence": 0.3
                }
            },
            "configuration": {
                "high": {
                    "template": "For {config_item}, the recommended configuration is: "
                               "{config_yaml}. This ensures {benefit1} and {benefit2}. "
                               "Important: {warning}",
                    "confidence": 0.92
                },
                "medium": {
                    "template": "Update {config_item} with: {config_yaml}",
                    "confidence": 0.8
                },
                "low": {
                    "template": "Check your configuration files.",
                    "confidence": 0.35
                }
            }
        }
    
    async def process_query(self, query: K8sQuery) -> AgentResponse:
        """Process a K8s query and return a response"""
        await asyncio.sleep(random.uniform(0.5, 2.0))
        
        query_type = query.query_type if isinstance(query.query_type, str) else query.query_type.value
        templates = self.response_templates.get(
            query_type, 
            self.response_templates["error_analysis"]
        )
        
        template_data = templates[self.quality_level]
        
        answer = self._generate_response(
            template_data["template"],
            query.user_query,
            query.context
        )
        
        sources = self._generate_sources(query_type, self.quality_level)
        
        return AgentResponse(
            response_id=str(uuid4()),
            query_id=query.query_id,
            answer=answer,
            reasoning=f"Analyzed {query_type} using {self.quality_level} quality approach",
            confidence_score=template_data["confidence"] + random.uniform(-0.1, 0.1),
            sources=sources,
            execution_time=random.uniform(0.5, 2.0)
        )
    
    def _generate_response(
        self, 
        template: str, 
        user_query: str, 
        context: Dict[str, Any]
    ) -> str:
        """Generate response based on template"""
        placeholders = {
            "error": context.get("error", "Unknown error"),
            "diagnosis": "a resource constraint issue",
            "root_cause": "insufficient memory allocation",
            "step1": "Check resource limits with 'kubectl describe pod'",
            "step2": "Increase memory limits in deployment spec",
            "step3": "Monitor pod metrics after changes",
            "additional_check": "horizontal pod autoscaler settings",
            "metric": context.get("metric", "CPU usage"),
            "status": "above threshold",
            "optimization1": "Enable HPA with target CPU 70%",
            "optimization2": "Implement pod disruption budget",
            "improvement": "25-30",
            "config_item": context.get("config_item", "deployment"),
            "config_yaml": "resources: { limits: { memory: '2Gi', cpu: '1000m' } }",
            "benefit1": "stable performance",
            "benefit2": "efficient resource utilization",
            "warning": "Monitor after applying changes"
        }
        
        try:
            return template.format(**placeholders)
        except:
            return template
    
    def _generate_sources(self, query_type: str, quality_level: str) -> List[str]:
        """Generate relevant sources"""
        base_sources = [
            "Kubernetes Official Documentation",
            "Internal Runbook #K8S-001"
        ]
        
        if quality_level == "high":
            base_sources.extend([
                f"Cluster Metrics Dashboard",
                f"Previous incident analysis for {query_type}",
                "Best Practices Guide v2.1"
            ])
        elif quality_level == "medium":
            base_sources.append("Stack Overflow - Similar Issues")
            
        return base_sources