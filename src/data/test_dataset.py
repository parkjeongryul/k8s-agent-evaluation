from typing import List
from uuid import uuid4
from datetime import datetime
from .schemas import (
    K8sQuery, QueryType, TestCase, GroundTruth, 
    EvaluationDataset
)


def create_test_dataset() -> EvaluationDataset:
    """Create a comprehensive test dataset for K8s agent evaluation"""
    
    test_cases = [
        TestCase(
            test_id=str(uuid4()),
            query=K8sQuery(
                query_id="tc_001",
                user_query="My pod is in CrashLoopBackOff state. The logs show 'OOMKilled'. How do I fix this?",
                query_type=QueryType.ERROR_ANALYSIS,
                context={
                    "error": "OOMKilled",
                    "pod_state": "CrashLoopBackOff",
                    "namespace": "production",
                    "container_memory_limit": "512Mi"
                }
            ),
            ground_truth=GroundTruth(
                query_id="tc_001",
                expected_answer="The OOMKilled error indicates your pod is exceeding its memory limit. To fix this: 1) Check current memory usage with 'kubectl top pod <pod-name>' 2) Increase memory limits in your deployment spec 3) Analyze application for memory leaks 4) Consider implementing memory-efficient practices",
                key_points=[
                    "Identify OOMKilled as out of memory error",
                    "Check current resource usage",
                    "Increase memory limits",
                    "Investigate memory leaks",
                    "Monitor after changes"
                ],
                acceptable_variations=[
                    "Increase resources.limits.memory in deployment",
                    "Use kubectl describe pod to check limits"
                ]
            ),
            metadata={"difficulty": "medium", "category": "resource_management"}
        ),
        
        TestCase(
            test_id=str(uuid4()),
            query=K8sQuery(
                query_id="tc_002",
                user_query="How can I optimize my K8s cluster for better search performance? Current response time is 500ms.",
                query_type=QueryType.PERFORMANCE,
                context={
                    "current_response_time": "500ms",
                    "cluster_type": "search",
                    "node_count": 5,
                    "index_size": "100GB"
                }
            ),
            ground_truth=GroundTruth(
                query_id="tc_002",
                expected_answer="To optimize search performance: 1) Enable node affinity for search pods 2) Use SSD-backed persistent volumes 3) Implement horizontal pod autoscaling 4) Configure appropriate JVM heap sizes 5) Use dedicated node pools for search workloads",
                key_points=[
                    "Node affinity configuration",
                    "Storage optimization with SSDs",
                    "Horizontal scaling setup",
                    "Memory tuning for search engines",
                    "Resource isolation strategies"
                ],
                acceptable_variations=[
                    "Configure HPA based on CPU/memory metrics",
                    "Use taints and tolerations for dedicated nodes"
                ]
            ),
            metadata={"difficulty": "high", "category": "performance_tuning"}
        ),
        
        TestCase(
            test_id=str(uuid4()),
            query=K8sQuery(
                query_id="tc_003",
                user_query="How do I configure a deployment with rolling updates and zero downtime?",
                query_type=QueryType.CONFIGURATION,
                context={
                    "application_type": "web_service",
                    "current_replicas": 3,
                    "update_frequency": "weekly"
                }
            ),
            ground_truth=GroundTruth(
                query_id="tc_003",
                expected_answer="Configure rolling updates with: 1) Set strategy.type: RollingUpdate 2) Configure maxSurge: 1 and maxUnavailable: 0 3) Add readiness probes 4) Set appropriate terminationGracePeriodSeconds 5) Use PodDisruptionBudget for additional safety",
                key_points=[
                    "RollingUpdate strategy configuration",
                    "maxSurge and maxUnavailable settings",
                    "Readiness probe implementation",
                    "Graceful shutdown handling",
                    "PodDisruptionBudget usage"
                ],
                acceptable_variations=[
                    "Configure preStop hooks for graceful shutdown",
                    "Use blue-green deployment strategy"
                ]
            ),
            metadata={"difficulty": "medium", "category": "deployment_strategy"}
        ),
        
        TestCase(
            test_id=str(uuid4()),
            query=K8sQuery(
                query_id="tc_004",
                user_query="My cluster is running out of resources during peak hours. How should I implement autoscaling?",
                query_type=QueryType.SCALING,
                context={
                    "peak_hours": "9AM-5PM",
                    "resource_usage_peak": "85%",
                    "resource_usage_off_peak": "30%",
                    "current_nodes": 10
                }
            ),
            ground_truth=GroundTruth(
                query_id="tc_004",
                expected_answer="Implement multi-level autoscaling: 1) Configure HPA for pods based on CPU/memory metrics 2) Set up Cluster Autoscaler for node scaling 3) Use VPA for right-sizing containers 4) Implement scheduled scaling for predictable patterns 5) Set resource requests/limits appropriately",
                key_points=[
                    "Horizontal Pod Autoscaler setup",
                    "Cluster Autoscaler configuration",
                    "Vertical Pod Autoscaler consideration",
                    "Scheduled scaling for peak hours",
                    "Resource requests and limits optimization"
                ],
                acceptable_variations=[
                    "Use KEDA for advanced autoscaling",
                    "Implement custom metrics for scaling decisions"
                ]
            ),
            metadata={"difficulty": "high", "category": "autoscaling"}
        ),
        
        TestCase(
            test_id=str(uuid4()),
            query=K8sQuery(
                query_id="tc_005",
                user_query="Getting 'ImagePullBackOff' error. The image exists in our private registry.",
                query_type=QueryType.TROUBLESHOOTING,
                context={
                    "error": "ImagePullBackOff",
                    "registry": "private.registry.com",
                    "namespace": "development"
                }
            ),
            ground_truth=GroundTruth(
                query_id="tc_005",
                expected_answer="Fix ImagePullBackOff for private registry: 1) Create docker-registry secret with credentials 2) Add imagePullSecrets to pod spec 3) Verify registry URL and image tag 4) Check network connectivity to registry 5) Ensure service account has proper permissions",
                key_points=[
                    "Docker registry secret creation",
                    "imagePullSecrets configuration",
                    "Registry URL verification",
                    "Network connectivity check",
                    "RBAC and permissions validation"
                ],
                acceptable_variations=[
                    "kubectl create secret docker-registry",
                    "Check firewall rules for registry access"
                ]
            ),
            metadata={"difficulty": "medium", "category": "image_management"}
        )
    ]
    
    return EvaluationDataset(
        dataset_id=str(uuid4()),
        name="K8s Agent Evaluation Dataset v1",
        description="Comprehensive test cases for evaluating K8s troubleshooting agents",
        test_cases=test_cases,
        version="1.0.0"
    )