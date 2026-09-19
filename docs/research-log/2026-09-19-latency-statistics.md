# 연구 기록 - 지연시간 통계 저장 개선

- 일자: 2026-09-19

## 목적

실제 장치 종단 실험에서 평균만으로는 드러나지 않는 응답 지연 편차를 확인할 수 있도록 세션 결과의 지연시간 요약 항목을 확장한다.

## 변경 내용

- 성공한 Q&A 항목만 대상으로 STT, 답변 생성, 전체 지연시간을 집계한다.
- 각 구간별 평균에 더해 중앙값과 95백분위수를 계산한다.
- 확장된 요약값을 기존 세션 JSON 결과에 함께 저장한다.
- 빈 세션과 실패 항목 제외 동작을 자동 테스트에 추가한다.

## 실행 조건

- Python 3.12.14
- 실제 마이크, faster-whisper 모델, Ollama 없이 코어 모듈을 검증했다.
- 질문 탐지 평가는 저장소의 `data/question_detection_eval.csv`를 사용했다.

## 결과

- `python -m pytest`: 12개 통과, 실패 0개
- `python -m ruff check quizsense tests`: 통과
- `python -m quizsense.evaluation data/question_detection_eval.csv --output artifacts/evaluation/question-detection-v1.json`: 정확도 1.0000, 정밀도 1.0000, 재현율 1.0000, F1 1.0000
- `python -m py_compile quizzesense_ai.py quizsense/*.py`: 통과
- `git diff --check`: 통과

## 문제점

- 이번 실행환경에는 실제 마이크와 로컬 Ollama 모델이 없어 종단 지연시간 실측값은 생성하지 않았다.
- 표본이 매우 적을 때 95백분위수는 세션 특성을 충분히 대표하지 못하므로 실제 평가는 여러 질문을 반복 측정해야 한다.

## 다음 작업

동일 PC에서 실제 마이크, faster-whisper, Ollama를 연결해 강의형 질문을 반복 재생하고, 생성된 세션 JSON의 평균·중앙값·95백분위수를 연구 결과로 기록한다.
