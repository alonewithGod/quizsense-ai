# 연구 기록 - 실행 설정 통합

- 일자: 2026-09-24

## 목적

사전 점검과 실제 데스크톱 앱이 동일한 실행 설정을 사용하도록 통합해, 점검 결과와 실제 동작이 달라지는 문제를 제거한다.

## 변경 내용

- `quizzesense_ai.py`의 고정 실행 상수를 `AppConfig` 값으로 교체했다.
- 마이크 샘플레이트·채널, 음성 구간 기준, Whisper 모델·언어·장치, Ollama 주소·모델·대기시간, 질문 중복 억제와 이력 크기를 환경변수로 설정할 수 있게 했다.
- `auto` 언어 설정을 faster-whisper의 자동 감지 값인 `None`으로 변환한다.
- README에 Windows PowerShell 설정 예시를 추가했다.

## 실행 조건

- Python 3.12.14
- 실제 마이크, faster-whisper 모델, Ollama가 없는 컨테이너에서 설정 로직과 정적 연결을 검증했다.

## 결과

- `python -m pytest`: 17개 통과, 실패 0개
- `python -m ruff check quizsense tests`: 통과
- `python -m quizsense.evaluation data/question_detection_eval.csv --output artifacts/evaluation/question-detection-v1.json`: 정확도 1.0000, 정밀도 1.0000, 재현율 1.0000, F1 1.0000
- `python -m py_compile quizzesense_ai.py quizsense/*.py`: 통과
- 환경변수 단위 테스트에서 언어 `ko`, 샘플레이트 48,000 Hz, Ollama 제한시간 12.5초, 이력 25개가 설정 객체에 반영됨을 확인했다.

## 문제점

- 설정 전달과 자동 언어 감지 값 변환은 검증했지만 실제 한국어 음성 전사 정확도는 측정하지 않았다.
- GPU 설정 조합과 마이크별 샘플레이트 지원 여부는 실제 발표 PC에서 확인해야 한다.

## 다음 작업

발표용 PC에서 사전 점검을 통과시킨 뒤 `auto`, `en`, `ko` 설정별 강의형 음성 전사를 실행하고 종단 지연시간과 오류 사례를 저장한다.
