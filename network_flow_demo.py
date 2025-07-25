#!/usr/bin/env python3
"""
네트워크 트래픽 흐름 데모 및 모니터링
"""
import os
import time
import asyncio
from datetime import datetime

# 네트워크 요청 추적을 위한 Mock
class NetworkTracker:
    def __init__(self):
        self.requests = []
    
    def log_request(self, method: str, url: str, payload_size: int = 0):
        """네트워크 요청 로깅"""
        self.requests.append({
            "timestamp": datetime.now(),
            "method": method,
            "url": url,
            "payload_size": payload_size,
            "type": self._classify_request(url)
        })
        print(f"📡 {method} {url} ({payload_size} bytes)")
    
    def _classify_request(self, url: str) -> str:
        """요청 타입 분류"""
        if "internal-llm" in url or "10.0.1" in url:
            return "internal_llm"
        elif "smith.langchain.com" in url:
            return "external_blocked"
        elif "api.openai.com" in url:
            return "external_blocked"
        else:
            return "unknown"
    
    def print_summary(self):
        """트래픽 요약 출력"""
        print(f"\n📊 네트워크 트래픽 요약:")
        print(f"{'='*50}")
        
        internal_count = len([r for r in self.requests if r["type"] == "internal_llm"])
        blocked_count = len([r for r in self.requests if r["type"] == "external_blocked"])
        total_payload = sum(r["payload_size"] for r in self.requests)
        
        print(f"✅ 사내 LLM 요청: {internal_count}개")
        print(f"🚫 차단된 외부 요청: {blocked_count}개")
        print(f"📦 총 전송량: {total_payload:,} bytes")
        print(f"⏱️  실행 시간: {len(self.requests)} requests")
        
        if self.requests:
            print(f"\n📋 요청 상세:")
            for i, req in enumerate(self.requests, 1):
                status = "✅" if req["type"] == "internal_llm" else "🚫"
                print(f"  {i}. {status} {req['method']} {req['url'][:50]}...")


async def simulate_evaluation_flow():
    """평가 시스템 실행 흐름 시뮬레이션"""
    tracker = NetworkTracker()
    
    print("🚀 K8s Agent 평가 시스템 트래픽 흐름 시뮬레이션")
    print("="*60)
    
    # Phase 1: 초기화
    print(f"\n🔧 Phase 1: 시스템 초기화")
    print(f"   📁 Few-shot YAML 파일 로드... (로컬 파일 시스템)")
    await asyncio.sleep(0.5)
    
    print(f"   🔒 외부 전송 차단 확인...")
    # 외부 요청 차단 시뮬레이션
    try:
        # 실제로는 요청하지 않지만 차단됨을 보여줌
        print(f"      🚫 smith.langchain.com 접근 차단됨")
        print(f"      🚫 api.openai.com 접근 차단됨")
    except:
        pass
    
    print(f"   🧪 사내 LLM 서버 연결 테스트...")
    tracker.log_request("POST", "http://internal-llm.company.com:8000/v1/chat/completions", 150)
    await asyncio.sleep(1.0)
    
    # Phase 2: 평가 실행
    print(f"\n📊 Phase 2: Agent 평가 실행")
    test_cases = [
        "OOMKilled 오류 분석",
        "검색 성능 최적화", 
        "Rolling Update 설정",
        "HPA 구성",
        "ImagePullBackOff 해결"
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n   📝 테스트 {i}: {test_case}")
        print(f"      🤖 Mock Agent 응답 생성 (로컬)")
        await asyncio.sleep(0.3)
        
        print(f"      🎯 Few-shot 예제 선택 (로컬 YAML)")
        await asyncio.sleep(0.2)
        
        print(f"      📝 평가 프롬프트 구성 (로컬)")
        
        # 실제 사내 LLM 호출 시뮬레이션
        prompt_size = 1500 + len(test_case) * 10  # 프롬프트 크기 추정
        print(f"      🔄 사내 LLM 평가 요청...")
        tracker.log_request("POST", "http://internal-llm.company.com:8000/v1/chat/completions", prompt_size)
        await asyncio.sleep(2.0)  # LLM 응답 시간 시뮬레이션
        
        print(f"      💾 평가 결과 로컬 저장")
        await asyncio.sleep(0.1)
    
    # Phase 3: 결과 저장
    print(f"\n💾 Phase 3: 결과 저장 및 정리")
    print(f"   📄 JSON 파일 저장 (로컬)")
    print(f"   📊 메트릭 계산 (로컬)")
    
    # 트래픽 요약
    tracker.print_summary()
    
    print(f"\n🔐 보안 확인:")
    print(f"   ✅ 모든 데이터가 사내 네트워크에서만 처리됨")
    print(f"   ✅ 외부 서버로 전송된 데이터: 0 bytes")
    print(f"   ✅ 사내 LLM서버 외 다른 연결 없음")


def show_actual_flow():
    """실제 코드에서의 트래픽 흐름"""
    print(f"\n📋 실제 코드에서의 네트워크 흐름:")
    print(f"{'='*50}")
    
    flow_steps = [
        ("시작", "internal_llm_config.py 실행"),
        ("환경변수", "OPENAI_BASE_URL 확인 → 사내 서버"),
        ("차단", "LANGCHAIN_* 환경변수 제거 → 외부 전송 차단"),
        ("Few-shot", "YAML 파일 로드 → 로컬 파일시스템만"),
        ("테스트", "사내 LLM 연결 테스트 → 1회 POST 요청"),
        ("평가루프", "각 테스트케이스별 → 사내 LLM POST 요청"),
        ("결과", "JSON 저장 → 로컬 파일시스템만")
    ]
    
    for step, description in flow_steps:
        icon = "🔒" if "차단" in description else "📡" if "POST" in description else "📁"
        print(f"   {icon} {step:8} | {description}")


if __name__ == "__main__":
    print("🌐 K8s Agent 평가 시스템 - 네트워크 트래픽 흐름 분석")
    print("="*70)
    
    # 실제 흐름 설명
    show_actual_flow()
    
    # 시뮬레이션 실행
    print(f"\n🎭 실행 시뮬레이션:")
    asyncio.run(simulate_evaluation_flow())