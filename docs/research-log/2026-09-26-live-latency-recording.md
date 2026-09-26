# 연구 기록 - 실시간 지연시간 기록 연결

- 일자: 2026-09-26

## 목적

기존에 구현한 지연시간 통계 모듈을 실제 데스크톱 실행 경로에 연결해, 향후 종단 실험의 측정값이 세션 결과로 저장되도록 한다.

## 변경 내용

- 실제 음성 전사 전후에서 STT 처리시간을 측정한다.
- 질문 감지 후 Ollama 응답 생성 전후에서 답변 처리시간을 측정한다.
- 질문 원문, 탐지 점수, STT·답변·전체 지연시간, 성공·실패 상태를 공통 `QAItem` 형식으로 기록한다.
- 저장 버튼을 누르면 `artifacts/sessions`에 요약 포함 JSON과 항목별 CSV를 함께 생성한다.
- Ollama 응답 실패 항목은 실패 건수에 포함하되 성공 지연시간 통계에서는 제외한다.

## 실행 조건

- Python 3.12.14
- 실제 마이크, faster-whisper 모델, Ollama가 없는 컨테이너에서 세션 기록·내보내기 로직을 검증했다.

## 결과

- `python -m pytest`: 19개 통과, 실패 0개
- `python -m ruff check quizsense tests`: 통과
- `python -m quizsense.evaluation data/question_detection_eval.csv --output artifacts/evaluation/question-detection-v1.json`: 정확도 1.0000, 정밀도 1.0000, 재현율 1.0000, F1 1.0000
- `python -m py_compile quizzesense_ai.py quizsense/*.py`: 통과
- 자동 테스트에서 STT 125.68ms, 답변 900.13ms 입력이 전체 1025.80ms로 계산되어 JSON·CSV에 저장됨을 확인했다. 이 값은 계산 검증용 입력이며 실제 장치 측정값이 아니다.

## 문제점

- 이번 환경에는 실제 장치와 Ollama가 없어 실제 종단 지연시간 수치는 측정하지 않았다.
- 현재 전체 지연시간은 STT와 답변 생성시간의 합이며, 음성 발화 구간 수집 대기시간은 포함하지 않는다.

## 다음 작업

발표용 PC에서 실제 강의형 질문을 반복 입력하고 저장된 세션 JSON의 평균·중앙값·95백분위수와 실패 사례를 연구 결과로 기록한다.
