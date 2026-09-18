from quizsense.question_detection import QuestionDetector


def test_detects_english_and_korean_questions():
    detector = QuestionDetector(cooldown_sec=0)
    assert detector.classify("Why is the sky blue").is_question
    assert detector.classify("왜 하늘은 파란가요").is_question


def test_rejects_statements():
    detector = QuestionDetector(cooldown_sec=0)
    assert not detector.classify("The sky appears blue because of scattering.").is_question
    assert not detector.classify("오늘은 네트워크 계층을 공부합니다.").is_question


def test_extracts_last_question_from_context():
    detector = QuestionDetector(cooldown_sec=0)
    result = detector.classify("We discussed caching. Why does a cache miss occur?")
    assert result.extracted_question == "Why does a cache miss occur?"


def test_cooldown_and_duplicate_are_explainable():
    detector = QuestionDetector(cooldown_sec=5, duplicate_window_sec=30)
    assert detector.should_trigger("What is a process?", now=10).is_question
    blocked = detector.should_trigger("Why do we need threads?", now=12)
    assert not blocked.is_question and "cooldown" in blocked.reasons
    duplicate = detector.should_trigger("What is a process?", now=20)
    assert not duplicate.is_question and "duplicate" in duplicate.reasons
