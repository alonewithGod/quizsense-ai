# QuizSense AI 발표용 실행 절차

이 문서는 Windows 11 발표용 PC에서 실제 마이크, faster-whisper, Ollama를 사용해 시연하고
검증 자료를 보존하기 위한 절차다. 실제 장치 결과가 없는 상태에서 성공을 가정하지 않는다.

## 1. 발표 전 최초 준비

PowerShell에서 저장소 루트로 이동한 뒤 아래 명령을 한 번 실행한다.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
ollama pull llama3.1:8b
```

PowerShell이 스크립트 실행을 막으면 현재 창에서만 다음 명령을 실행한 뒤 다시 활성화한다.

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## 2. 발표 당일 사전 점검

1. Windows 설정에서 사용할 마이크를 기본 입력 장치로 선택한다.
2. Ollama를 실행한다.
3. 저장소 루트에서 아래 명령을 실행한다.

```powershell
.\.venv\Scripts\Activate.ps1
$env:QUIZSENSE_LANGUAGE="ko"
python -m quizsense.preflight --output artifacts/preflight/demo-pc.json
```

화면의 네 항목이 모두 `PASS`이고 `demo-pc.json`의 `ready`가 `true`인지 확인한다.

- `module:sounddevice`
- `module:faster_whisper`
- `input_device`
- `ollama_model`

하나라도 실패하면 앱을 먼저 실행하지 말고 아래 복구표를 따른다.

## 3. 3분 시연 순서

```powershell
python quizzesense_ai.py
```

1. 앱에서 `청취 시작`을 누르고 상태가 `실시간 청취 중`으로 바뀌는지 확인한다.
2. 평서문을 먼저 말한다: `오늘은 운영체제의 가상 메모리를 설명하겠습니다.`
3. 질문을 말한다: `페이지 폴트가 발생하면 어떤 순서로 처리될까요?`
4. 화면에 원문 질문, 한국어 질문, 영어 답변, 한국어 답변이 표시될 때까지 기다린다.
5. 두 번째 질문을 말한다: `TLB가 필요한 이유를 누가 설명해볼까요?`
6. `중지`를 누른 뒤 `Q&A 내역 저장`을 눌러 JSON과 CSV를 생성한다.

답변 내용이나 지연시간을 미리 약속하지 않는다. 질문 탐지 여부, 답변 생성 여부, 실제 저장 파일만
현장에서 확인한다.

## 4. 반드시 남길 증빙

발표 직후 다음 자료를 같은 실험 회차의 증빙으로 보관한다.

- `artifacts/preflight/demo-pc.json`: 장치·모델·설정 준비 상태
- `artifacts/sessions/session_*.json`: 성공·실패 수와 지연시간 통계
- `artifacts/sessions/session_*.csv`: 질문별 전사문·답변·지연시간
- 스크린샷 1: 사전 점검 네 항목이 모두 `PASS`인 PowerShell 화면
- 스크린샷 2: 질문과 이중 언어 답변이 표시된 앱 화면
- 스크린샷 3: 저장 완료 경로가 표시된 앱 상태 영역

스크린샷에는 전체 바탕화면 대신 앱과 필요한 PowerShell 영역만 포함한다. 실제 화면에서 촬영하고,
문서에 넣기 위해 결과를 재작성하거나 합성하지 않는다.

## 5. 실패 시 복구표

| 증상 | 확인 및 복구 |
|---|---|
| `sounddevice is not installed` | 가상환경 활성화 후 `python -m pip install -r requirements.txt` 실행 |
| 입력 장치 실패 | Windows 마이크 권한과 기본 입력 장치를 확인하고 다른 앱의 독점 사용을 종료 |
| Ollama 연결 실패 | Ollama 실행 여부를 확인한 뒤 `ollama list` 실행 |
| 모델 누락 | `ollama pull llama3.1:8b` 실행 후 사전 점검 재실행 |
| 질문을 감지하지 못함 | 마이크 가까이에서 한 문장씩 말하고 문장 끝을 질문형으로 명확히 발음 |
| 답변 생성 실패 | Ollama 창과 모델 설치 상태를 확인한 뒤 같은 질문을 한 번만 재시도 |
| 세션 저장 실패 | 저장 경로 권한과 디스크 공간을 확인하고 앱을 종료하기 전에 다시 저장 |

## 6. 제출 기록에 옮길 값

실제 세션 JSON에서 다음 값만 연구일지와 발표 자료에 옮긴다.

- `total_items`, `successful_items`, `failed_items`
- STT 지연시간 평균·중앙값·95백분위수
- 답변 지연시간 평균·중앙값·95백분위수
- 전체 지연시간 평균·중앙값·95백분위수

실행하지 않은 조건의 값, 테스트용 숫자, 예상값은 실측 결과로 기록하지 않는다.
