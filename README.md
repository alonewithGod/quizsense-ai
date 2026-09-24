# QuizSense AI

강의 음성을 실시간으로 전사하고 질문을 자동 탐지한 뒤, 로컬 LLM으로 영어·한국어 답변을 표시하는 데스크톱 학습 보조 시스템입니다.

## 현재 구현 범위

- 16 kHz 마이크 입력과 RMS 기반 음성 구간 분리
- `faster-whisper` 기반 자동 언어 감지 음성 전사 및 최근 24초 문맥 유지
- 한국어·영어 규칙 기반 질문 탐지와 탐지 근거 점수
- 쿨다운 및 유사 질문 중복 억제
- Ollama 구조화 응답을 이용한 질문 번역·이중 언어 답변
- Tkinter UI, 청취 시작/중지, Q&A 이력 표시·JSON/CSV 저장
- 질문 탐지 자동 테스트 및 CSV 평가 도구
- 세션별 STT·답변·전체 지연시간의 평균·중앙값·95백분위수 저장
- 마이크·Whisper·Ollama 모델 준비 상태를 확인하는 실행 전 사전 점검

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
python -m quizsense.preflight
python quizzesense_ai.py
```

사전 점검의 모든 항목이 `PASS`인지 확인한 뒤 실행합니다. 자동 수집이 필요하면
`python -m quizsense.preflight --json`을 사용합니다. 실행 후 `청취 시작`을 눌러 마이크 입력을
시작하고 `중지`로 스트림을 닫습니다.

### 주요 실행 설정

앱과 사전 점검은 동일한 `QUIZSENSE_` 환경변수를 사용합니다. 기본값은 자동 언어 감지,
Whisper `base`, CPU `int8`, Ollama `llama3.1:8b`입니다.

```powershell
# PowerShell 예시: 한국어로 고정하고 Ollama 대기시간을 45초로 설정
$env:QUIZSENSE_LANGUAGE="ko"
$env:QUIZSENSE_OLLAMA_TIMEOUT="45"
python -m quizsense.preflight
python quizzesense_ai.py
```

언어는 `auto`, `en`, `ko` 중 하나를 사용할 수 있습니다. 이외에도 `QUIZSENSE_WHISPER_MODEL`,
`QUIZSENSE_DEVICE`, `QUIZSENSE_COMPUTE_TYPE`, `QUIZSENSE_OLLAMA_URL`,
`QUIZSENSE_OLLAMA_MODEL`, `QUIZSENSE_SILENCE_THRESHOLD`를 조정할 수 있습니다.

## 개발 검증

```bash
pip install -r requirements-dev.txt
python -m pytest
python -m ruff check quizsense tests
python -m quizsense.evaluation data/question_detection_eval.csv \
  --output artifacts/evaluation/question-detection-v1.json
```

검증 시점별 실행 결과는 [연구 기록](docs/research-log/)에 남깁니다. 20개 질문과 20개 비질문으로 구성한 내부 평가 세트에서는 정확도·정밀도·재현율·F1이 모두 1.0이었습니다. 이 데이터는 기능 회귀 검증용 소규모 자체 데이터이므로 실제 강의 일반화 성능을 의미하지 않습니다.

## 현재 한계

- 실제 교실 소음·화자 거리·마이크 종류를 반영한 외부 데이터 평가는 아직 수행하지 않았습니다.
- STT 자동 언어 감지와 한국어 고정 설정은 연결했지만 한국어 음성 전체 흐름은 실제 장치에서 후속 검증이 필요합니다.
- 고정 RMS 임계값은 환경 변화에 민감할 수 있습니다.
- 실제 장치 환경의 STT 및 Ollama 종단 지연시간 측정이 남아 있습니다.
- 규칙 기반 탐지기는 간접 질문이나 문맥에 따라 오탐·미탐이 생길 수 있습니다.

## 연구 기록

- [2026-09-18 현재 상태 점검](docs/research-log/2026-09-18-current-status.md)
- [2026-09-18 구조 개선 및 1차 평가](docs/research-log/2026-09-18-refactor-and-evaluation.md)
- [2026-09-19 지연시간 통계 저장 개선](docs/research-log/2026-09-19-latency-statistics.md)
- [2026-09-22 실행환경 사전 점검 추가](docs/research-log/2026-09-22-runtime-preflight.md)
- [2026-09-24 실행 설정 통합](docs/research-log/2026-09-24-runtime-config-integration.md)

## 라이선스

MIT License
