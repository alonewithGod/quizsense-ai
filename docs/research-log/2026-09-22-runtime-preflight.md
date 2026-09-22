# 연구 기록 - 실행환경 사전 점검 추가

- 일자: 2026-09-22

## 목적

실제 마이크·faster-whisper·Ollama 종단 실험 전에 필수 실행환경을 진단해, 실행 실패 원인을 구체적으로 확인하고 발표 현장의 설정 오류를 줄인다.

## 변경 내용

- `python -m quizsense.preflight` 명령을 추가했다.
- `sounddevice`와 `faster_whisper` 설치 여부, 기본 입력 장치, Ollama 연결 및 `llama3.1:8b` 모델 설치 여부를 점검한다.
- 사람이 읽는 출력과 자동 저장용 JSON 출력을 지원한다.
- 설정값이 잘못됐거나 필수 조건이 충족되지 않으면 종료 코드 1을 반환한다.

## 실행 조건

- Python 3.12.14
- 컨테이너 환경에서 자동 테스트와 정적 검사를 수행했다.
- 현재 실행환경에는 실제 입력 장치와 실행 중인 로컬 Ollama 서버가 제공되지 않았다.

## 결과

- `python -m pytest`: 15개 통과, 실패 0개
- `python -m ruff check quizsense tests`: 통과
- `python -m quizsense.evaluation data/question_detection_eval.csv --output artifacts/evaluation/question-detection-v1.json`: 정확도 1.0000, 정밀도 1.0000, 재현율 1.0000, F1 1.0000
- `python -m py_compile quizzesense_ai.py quizsense/*.py`: 통과
- 현재 환경의 사전 점검: `sounddevice`, `faster_whisper`, 입력 장치, Ollama 연결이 모두 준비되지 않은 것으로 확인됐으며 종료 코드 1을 반환했다.

## 문제점

- 사전 점검은 장치와 모델의 준비 여부만 확인하며 실제 음성 전사·질문 탐지·답변 생성 성공까지 보장하지 않는다.
- 실제 마이크와 Ollama가 있는 동일 PC에서 종단 실행 결과와 지연시간을 별도로 측정해야 한다.

## 다음 작업

발표에 사용할 PC에서 `python -m quizsense.preflight --json`을 실행해 모든 항목이 통과하는지 확인한 뒤, 강의형 질문 음성으로 종단 실행과 지연시간 측정을 수행한다.
