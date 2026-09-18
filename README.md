# QuizSense AI

강의 음성을 실시간으로 전사하고 질문을 자동 탐지한 뒤, 로컬 LLM으로 영어·한국어 답변을 표시하는 데스크톱 학습 보조 시스템입니다.

## 현재 구현 범위

- 16 kHz 마이크 입력과 RMS 기반 음성 구간 분리
- `faster-whisper` 기반 영어 음성 전사 및 최근 24초 문맥 유지
- 한국어·영어 규칙 기반 질문 탐지와 탐지 근거 점수
- 쿨다운 및 유사 질문 중복 억제
- Ollama 구조화 응답을 이용한 질문 번역·이중 언어 답변
- Tkinter UI, 청취 시작/중지, Q&A 이력 표시·JSON 저장
- 질문 탐지 자동 테스트 및 CSV 평가 도구

## 구조

```text
quizsense-ai/
├── quizzesense_ai.py              # 데스크톱 앱과 장치 연동
├── quizsense/                     # 테스트 가능한 코어 모듈
│   ├── config.py                  # 환경 설정과 검증
│   ├── question_detection.py      # 한·영 질문 판별/추출/중복 억제
│   ├── llm.py                     # Ollama 구조화 응답 클라이언트
│   ├── history.py                 # 세션 결과·지연시간 저장
│   ├── models.py                  # 데이터 모델
│   └── evaluation.py              # 정량 평가 CLI
├── data/                          # 평가 데이터
├── artifacts/evaluation/          # 재현 가능한 평가 결과
├── tests/                         # 단위 테스트
└── docs/                          # 구조·연구 진행 기록
```

상세 내용은 [시스템 구조](docs/architecture.md)를 참고하세요.

## 설치 및 실행

Python 3.10 이상, 마이크, 실행 중인 Ollama가 필요합니다.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
ollama pull llama3.1:8b
python quizzesense_ai.py
```

실행 후 `청취 시작`을 눌러 마이크 입력을 시작하고 `중지`로 스트림을 닫습니다.

## 개발 검증

```bash
pip install -r requirements-dev.txt
python -m pytest
python -m ruff check quizsense tests
python -m quizsense.evaluation data/question_detection_eval.csv \
  --output artifacts/evaluation/question-detection-v1.json
```

2026-09-18 기준 자동 테스트 10개가 통과했습니다. 20개 질문과 20개 비질문으로 구성한 내부 평가 세트에서는 정확도·정밀도·재현율·F1이 모두 1.0이었습니다. 이 데이터는 기능 회귀 검증용 소규모 자체 데이터이므로 실제 강의 일반화 성능을 의미하지 않습니다.

## 현재 한계

- 실제 교실 소음·화자 거리·마이크 종류를 반영한 외부 데이터 평가는 아직 수행하지 않았습니다.
- 실행 코드의 STT 언어는 현재 영어로 고정되어 있습니다. 질문 판별 코어는 한·영을 지원하지만 한국어 음성 전체 흐름은 후속 검증이 필요합니다.
- 고정 RMS 임계값은 환경 변화에 민감할 수 있습니다.
- 실제 장치 환경의 STT 및 Ollama 종단 지연시간 측정이 남아 있습니다.
- 규칙 기반 탐지기는 간접 질문이나 문맥에 따라 오탐·미탐이 생길 수 있습니다.

## 연구 기록

- [2026-09-18 현재 상태 점검](docs/research-log/2026-09-18-current-status.md)
- [2026-09-18 구조 개선 및 1차 평가](docs/research-log/2026-09-18-refactor-and-evaluation.md)

## 라이선스

MIT License
