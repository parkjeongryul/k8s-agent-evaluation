# K8s Agent Evaluation System (사내 전용)

🏢 **사내 LLM 서버 전용** K8s 검색 클러스터 문의 처리 Agent 평가 시스템

## 🔒 보안 특징

- ✅ **완전 내부 처리**: 모든 데이터가 사내에서만 처리
- ✅ **외부 전송 차단**: LangSmith 등 외부 서비스 완전 제거
- ✅ **사내 LLM 서버**: OpenAI 호환 API 지원
- ✅ **로컬 Few-shot**: YAML 파일 기반 전문가 예제

## 주요 기능

- **2가지 평가 방식**: 파일 기반 Few-shot, 순수 LLM 기반
- **다차원 평가**: 정확성, 관련성, 완전성 점수
- **쿼리 타입별 분석**: 오류 분석, 성능, 구성, 스케일링 등
- **로컬 저장**: 모든 결과가 JSON 파일로 저장

## 설치

```bash
pip install -r requirements.txt

# 사내 전용 설정 템플릿 생성
python3 internal_llm_config.py --create-template
cp .env.internal .env
```

## 설정

`.env` 파일에 사내 LLM 서버 정보 입력:

```bash
# 사내 LLM 서버 설정
OPENAI_API_KEY=your_internal_api_key
OPENAI_BASE_URL=http://internal-llm.company.com:8000/v1
OPENAI_MODEL=your-internal-model-name
```

## 사용법

```bash
# 사내 LLM 서버로 평가 실행
python3 internal_llm_config.py
```

### 프로그래밍 방식

```python
from src.main import K8sAgentEvaluationSystem
from src.agent.mock_agent import MockK8sAgent

# 평가 시스템 초기화
config = {
    "file_based_config": {
        "model": "your-internal-model",
        "few_shot_dir": "examples/few_shot_examples"
    }
}
eval_system = K8sAgentEvaluationSystem(config)

# Agent 평가
agent = MockK8sAgent(quality_level="high")
results = await eval_system.evaluate_agent(
    agent, 
    evaluator_type="file_based"  # 또는 "llm"
)

# 결과 출력
eval_system.print_summary(results)
```

## 프로젝트 구조

```
k8s-agent-evaluation/
├── src/
│   ├── data/           # 데이터 스키마 및 테스트 데이터셋
│   ├── evaluator/      # 평가 모듈 (파일 기반, LLM 기반)
│   ├── agent/          # Mock Agent 구현
│   ├── metrics/        # 메트릭 계산
│   └── main.py         # 메인 실행 파일
├── examples/
│   └── few_shot_examples/  # 전문가 예제 YAML 파일들
├── internal_llm_config.py  # 사내 전용 실행 스크립트
└── requirements.txt    # 최소 의존성
```

## Few-shot 예제 관리

전문가 예제를 YAML 파일로 관리:

```yaml
# examples/few_shot_examples/error_analysis_examples.yaml
category: error_analysis
examples:
  - id: "ea_001"
    query:
      user_query: "Pod가 CrashLoopBackOff 상태입니다."
    expert_response: |
      전문가가 작성한 상세한 해결 방법...
    key_points:
      - "원인 분석"
      - "해결 단계"
```

## 보안 확인사항

- 🔒 **LangSmith 완전 제거**: 외부 추적 서비스 없음
- 🔒 **로컬 Few-shot**: YAML 파일에서만 예제 로드
- 🔒 **사내 LLM만 사용**: 외부 OpenAI API 사용 안함
- 🔒 **결과 저장**: 로컬 JSON 파일에만 저장

## 지원하는 사내 LLM 서버

OpenAI 호환 API를 제공하는 모든 서버:
- vLLM
- Text Generation Inference (TGI)
- FastChat
- Ollama
- 사내 커스텀 LLM 서버