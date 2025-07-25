# K8s Agent Evaluation System

LangSmith를 활용한 K8s 검색 클러스터 문의 처리 Agent 평가 시스템

## 주요 기능

- **다양한 평가 방식**: LLM 기반 평가 및 LangSmith 통합 평가
- **Few-shot 학습**: 고성능 응답을 LangSmith 데이터셋에 자동 추가
- **포괄적인 메트릭**: 정확성, 관련성, 완전성 평가
- **쿼리 타입별 분석**: 오류 분석, 성능, 구성, 스케일링 등
- **개선 영역 식별**: 자동으로 취약점 파악

## 설치

```bash
pip install -r requirements.txt
cp .env.example .env
# .env 파일에 API 키 설정
```

## 사용법

```python
from src.main import K8sAgentEvaluationSystem
from src.agent.mock_agent import MockK8sAgent

# 평가 시스템 초기화
eval_system = K8sAgentEvaluationSystem()

# Agent 평가
agent = MockK8sAgent(quality_level="high")
results = await eval_system.evaluate_agent(agent, use_langsmith=True)

# 결과 출력
eval_system.print_summary(results)
```

## 프로젝트 구조

```
k8s-agent-evaluation/
├── src/
│   ├── data/           # 데이터 스키마 및 테스트 데이터셋
│   ├── evaluator/      # 평가 모듈 (LLM, LangSmith)
│   ├── agent/          # Mock Agent 구현
│   ├── metrics/        # 메트릭 계산
│   └── main.py         # 메인 실행 파일
├── tests/              # 테스트 코드
└── requirements.txt    # 의존성
```

## LangSmith Few-shot 추가

평가 점수가 0.8 이상인 우수 응답은 자동으로 LangSmith 데이터셋에 추가되어 향후 평가에 활용됩니다.