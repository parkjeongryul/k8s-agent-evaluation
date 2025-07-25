"""
API 기반 K8s Agent - 실제 배포된 Agent API 호출
"""
import os
import asyncio
import aiohttp
import json
from typing import Dict, Any, Optional
from uuid import uuid4
from datetime import datetime
from ..data.schemas import K8sQuery, AgentResponse


class APIK8sAgent:
    """실제 K8s Agent API를 호출하는 클라이언트"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # API 설정 (환경변수 우선)
        self.api_base_url = os.getenv('K8S_AGENT_API_URL', 
                                      config.get('api_base_url', 'http://localhost:8080'))
        self.api_key = os.getenv('K8S_AGENT_API_KEY', 
                                  config.get('api_key'))
        self.timeout = int(os.getenv('K8S_AGENT_TIMEOUT', 
                                      config.get('timeout', 30)))
        
        # API 엔드포인트
        self.endpoint = f"{self.api_base_url.rstrip('/')}/api/v1/query"
        
        # 헤더 설정
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        if self.api_key:
            self.headers['Authorization'] = f'Bearer {self.api_key}'
        
        print(f"🌐 K8s Agent API 설정:")
        print(f"   URL: {self.api_base_url}")
        print(f"   Endpoint: {self.endpoint}")
        print(f"   인증: {'✅' if self.api_key else '❌'}")
        print(f"   타임아웃: {self.timeout}초")
    
    async def process_query(self, query: K8sQuery) -> AgentResponse:
        """API를 통해 K8s 문의 처리"""
        
        # API 요청 페이로드 구성
        payload = self._build_request_payload(query)
        
        # API 호출
        start_time = asyncio.get_event_loop().time()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.endpoint,
                    json=payload,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    execution_time = asyncio.get_event_loop().time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_api_response(data, query, execution_time)
                    else:
                        error_text = await response.text()
                        return self._create_error_response(
                            query, 
                            f"API 에러 ({response.status}): {error_text}",
                            execution_time
                        )
                        
        except asyncio.TimeoutError:
            execution_time = self.timeout
            return self._create_error_response(
                query,
                f"API 타임아웃 ({self.timeout}초 초과)",
                execution_time
            )
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            return self._create_error_response(
                query,
                f"API 호출 실패: {str(e)}",
                execution_time
            )
    
    def _build_request_payload(self, query: K8sQuery) -> Dict[str, Any]:
        """API 요청 페이로드 생성"""
        return {
            "query_id": query.query_id,
            "query": query.user_query,
            "query_type": query.query_type if isinstance(query.query_type, str) else query.query_type.value,
            "context": query.context,
            "timestamp": query.timestamp.isoformat() if hasattr(query, 'timestamp') else datetime.now().isoformat()
        }
    
    def _parse_api_response(
        self, 
        data: Dict[str, Any], 
        query: K8sQuery,
        execution_time: float
    ) -> AgentResponse:
        """API 응답을 AgentResponse로 변환"""
        
        # API 응답 형식이 다를 수 있으므로 유연하게 파싱
        return AgentResponse(
            response_id=data.get('response_id', str(uuid4())),
            query_id=query.query_id,
            answer=data.get('answer', data.get('response', '')),
            reasoning=data.get('reasoning', 'API를 통한 실시간 분석'),
            confidence_score=float(data.get('confidence_score', data.get('confidence', 0.8))),
            sources=data.get('sources', ['K8s Agent API']),
            execution_time=execution_time
        )
    
    def _create_error_response(
        self, 
        query: K8sQuery, 
        error_message: str,
        execution_time: float
    ) -> AgentResponse:
        """에러 응답 생성"""
        return AgentResponse(
            response_id=str(uuid4()),
            query_id=query.query_id,
            answer=f"죄송합니다. 요청을 처리할 수 없습니다: {error_message}",
            reasoning="API 호출 중 오류 발생",
            confidence_score=0.0,
            sources=["Error Response"],
            execution_time=execution_time
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """API 헬스체크"""
        health_endpoint = f"{self.api_base_url.rstrip('/')}/health"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    health_endpoint,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "status": "healthy",
                            "api_version": data.get('version', 'unknown'),
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "error": f"Status code: {response.status}",
                            "timestamp": datetime.now().isoformat()
                        }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# 다양한 API 형식 지원을 위한 어댑터
class CustomAPIK8sAgent(APIK8sAgent):
    """커스텀 API 형식을 지원하는 Agent"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        
        # 커스텀 설정
        self.custom_endpoint = config.get('custom_endpoint', '/query')
        self.request_format = config.get('request_format', 'standard')
        self.response_format = config.get('response_format', 'standard')
    
    def _build_request_payload(self, query: K8sQuery) -> Dict[str, Any]:
        """커스텀 요청 형식 지원"""
        
        if self.request_format == 'simple':
            # 단순 형식
            return {
                "question": query.user_query,
                "type": query.query_type if isinstance(query.query_type, str) else query.query_type.value
            }
        elif self.request_format == 'detailed':
            # 상세 형식
            return {
                "request": {
                    "id": query.query_id,
                    "content": query.user_query,
                    "metadata": {
                        "type": query.query_type if isinstance(query.query_type, str) else query.query_type.value,
                        "context": query.context
                    }
                }
            }
        else:
            # 기본 형식
            return super()._build_request_payload(query)
    
    def _parse_api_response(
        self, 
        data: Dict[str, Any], 
        query: K8sQuery,
        execution_time: float
    ) -> AgentResponse:
        """커스텀 응답 형식 파싱"""
        
        if self.response_format == 'simple':
            # 단순 응답
            return AgentResponse(
                response_id=str(uuid4()),
                query_id=query.query_id,
                answer=data.get('text', ''),
                reasoning="API response",
                confidence_score=0.8,
                sources=["API"],
                execution_time=execution_time
            )
        elif self.response_format == 'nested':
            # 중첩된 응답
            response_data = data.get('data', {})
            return AgentResponse(
                response_id=response_data.get('id', str(uuid4())),
                query_id=query.query_id,
                answer=response_data.get('content', ''),
                reasoning=response_data.get('explanation', ''),
                confidence_score=float(response_data.get('score', 0.8)),
                sources=response_data.get('references', []),
                execution_time=execution_time
            )
        else:
            # 기본 파싱
            return super()._parse_api_response(data, query, execution_time)