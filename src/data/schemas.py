from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class QueryType(str, Enum):
    ERROR_ANALYSIS = "error_analysis"
    PERFORMANCE = "performance"
    CONFIGURATION = "configuration"
    SCALING = "scaling"
    TROUBLESHOOTING = "troubleshooting"


class K8sQuery(BaseModel):
    query_id: str = Field(..., description="Unique identifier for the query")
    user_query: str = Field(..., description="Original user query about K8s cluster")
    query_type: QueryType = Field(..., description="Type of K8s query")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context like cluster state, logs")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        use_enum_values = True


class AgentResponse(BaseModel):
    response_id: str = Field(..., description="Unique identifier for the response")
    query_id: str = Field(..., description="Reference to the original query")
    answer: str = Field(..., description="Agent's response to the query")
    reasoning: Optional[str] = Field(None, description="Agent's reasoning process")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Agent's confidence in the answer")
    sources: List[str] = Field(default_factory=list, description="Sources used for the answer")
    execution_time: float = Field(..., description="Time taken to generate response in seconds")
    
    
class GroundTruth(BaseModel):
    query_id: str = Field(..., description="Reference to the original query")
    expected_answer: str = Field(..., description="Expected correct answer")
    key_points: List[str] = Field(..., description="Key points that should be covered")
    acceptable_variations: List[str] = Field(default_factory=list, description="Acceptable answer variations")
    

class EvaluationResult(BaseModel):
    evaluation_id: str = Field(..., description="Unique identifier for the evaluation")
    query_id: str = Field(..., description="Reference to the original query")
    response_id: str = Field(..., description="Reference to the agent response")
    correctness_score: float = Field(..., ge=0.0, le=1.0, description="Correctness score")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    completeness_score: float = Field(..., ge=0.0, le=1.0, description="Completeness score")
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Overall evaluation score")
    feedback: Dict[str, Any] = Field(default_factory=dict, description="Detailed feedback")
    timestamp: datetime = Field(default_factory=datetime.now)


class TestCase(BaseModel):
    test_id: str = Field(..., description="Unique identifier for the test case")
    query: K8sQuery = Field(..., description="The test query")
    ground_truth: GroundTruth = Field(..., description="Expected correct answer and evaluation criteria")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    

class EvaluationDataset(BaseModel):
    dataset_id: str = Field(..., description="Unique identifier for the dataset")
    name: str = Field(..., description="Dataset name")
    description: str = Field(..., description="Dataset description")
    test_cases: List[TestCase] = Field(..., description="List of test cases")
    created_at: datetime = Field(default_factory=datetime.now)
    version: str = Field(default="1.0.0", description="Dataset version")