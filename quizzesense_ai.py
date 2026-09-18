import json
import queue
import threading
import time
import re
from collections import deque
from dataclasses import dataclass
from typing import Deque, List, Optional

import numpy as np
import sounddevice as sd
import tkinter as tk
from faster_whisper import WhisperModel
import requests
from tkinter import scrolledtext

from quizsense.question_detection import QuestionDetector


# =========================
# Configuration
# =========================
SAMPLE_RATE = 16000
CHANNELS = 1
BLOCK_DURATION_SEC = 0.5
BLOCK_SIZE = int(SAMPLE_RATE * BLOCK_DURATION_SEC)
ROLLING_CONTEXT_SEC = 24
SILENCE_RMS_THRESHOLD = 0.01
MIN_SPEECH_BLOCKS = 2
MIN_SILENCE_BLOCKS_TO_FLUSH = 2
TRANSCRIBE_MODEL_SIZE = "base"   # tiny / base / small / medium
DEVICE = "cpu"                   # "cuda" if GPU is available
COMPUTE_TYPE = "int8"            # int8 for CPU, float16 for GPU
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1:8b"
QUESTION_COOLDOWN_SEC = 5
MAX_HISTORY_ITEMS = 50
OLLAMA_TIMEOUT_SEC = 18
ANSWER_MAX_TOKENS = 160


# =========================
# Data Models
# =========================
@dataclass
class TranscriptChunk:
    timestamp: float
    text: str


@dataclass
class QAItem:
    timestamp: float
    question_en: str
    question_ko: str
    answer_en: str
    answer_ko: str


# =========================
# UI
# =========================
class FloatingAnswerWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("QuizSense AI")
        self.root.attributes("-topmost", True)
        self.root.geometry("820x760+900+50")
        self.root.configure(bg="#111111")

        self.title_label = tk.Label(
            self.root,
            text="Walking Encyclopedia AI",
            fg="#ffffff",
            bg="#111111",
            font=("Arial", 14, "bold"),
            anchor="w"
        )
        self.title_label.pack(fill="x", padx=12, pady=(10, 4))

        self.status_label = tk.Label(
            self.root,
            text="대기 중...",
            fg="#bbbbbb",
            bg="#111111",
            font=("Arial", 10),
            anchor="w"
        )
        self.status_label.pack(fill="x", padx=12, pady=(0, 6))

        self.question_var = tk.StringVar(value="질문 감지 대기 중...")
        self.question_label = tk.Label(
            self.root,
            textvariable=self.question_var,
            fg="#ffd166",
            bg="#111111",
            justify="left",
            wraplength=770,
            font=("Arial", 12, "bold"),
            anchor="nw"
        )
        self.question_label.pack(fill="x", padx=12, pady=(0, 6))

        self.question_ko_var = tk.StringVar(value="질문 번역 대기 중...")
        self.question_ko_label = tk.Label(
            self.root,
            textvariable=self.question_ko_var,
            fg="#8ecae6",
            bg="#111111",
            justify="left",
            wraplength=770,
            font=("Arial", 11),
            anchor="nw"
        )
        self.question_ko_label.pack(fill="x", padx=12, pady=(0, 8))

        self.answer_en_var = tk.StringVar(value="질문이 감지되면 여기 영어 답변이 표시됩니다.")
        self.answer_en_label = tk.Label(
            self.root,
            textvariable=self.answer_en_var,
            fg="#00ff99",
            bg="#111111",
            justify="left",
            wraplength=770,
            font=("Arial", 13),
            anchor="nw"
        )
        self.answer_en_label.pack(fill="x", padx=12, pady=(0, 6))

        self.answer_ko_var = tk.StringVar(value="질문이 감지되면 여기 한국어 답변이 표시됩니다.")
        self.answer_ko_label = tk.Label(
            self.root,
            textvariable=self.answer_ko_var,
            fg="#caffbf",
            bg="#111111",
            justify="left",
            wraplength=770,
            font=("Arial", 12),
            anchor="nw"
        )
        self.answer_ko_label.pack(fill="x", padx=12, pady=(0, 12))

        self.history_title = tk.Label(
            self.root,
            text="Q&A History",
            fg="#ffffff",
            bg="#111111",
            font=("Arial", 11, "bold"),
            anchor="w"
        )
        self.history_title.pack(fill="x", padx=12, pady=(4, 4))

        self.history_text = scrolledtext.ScrolledText(
            self.root,
            height=18,
            bg="#0b0b0b",
            fg="#dddddd",
            insertbackground="#ffffff",
            wrap=tk.WORD,
            font=("Consolas", 10),
            relief="flat",
            borderwidth=1
        )
        self.history_text.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        self.history_text.insert(tk.END, "아직 질의응답 내역이 없습니다.\n")
        self.history_text.config(state=tk.DISABLED)

        self.control_frame = tk.Frame(self.root, bg="#111111")
        self.control_frame.pack(fill="x", padx=12, pady=(0, 8))
        self.start_button = tk.Button(
            self.control_frame,
            text="청취 시작",
            command=lambda: self.on_start_requested and self.on_start_requested(),
        )
        self.start_button.pack(side="left", padx=(0, 8))
        self.stop_button = tk.Button(
            self.control_frame,
            text="중지",
            state=tk.DISABLED,
            command=lambda: self.on_stop_requested and self.on_stop_requested(),
        )
        self.stop_button.pack(side="left")

        self.export_button = tk.Button(
            self.root,
            text="Q&A 내역 저장",
            command=self._show_export_message,
            bg="#1f1f1f",
            fg="#ffffff",
            activebackground="#333333",
            activeforeground="#ffffff",
            relief="flat"
        )
        self.export_button.pack(anchor="e", padx=12, pady=(0, 12))

        self.on_export_requested = None
        self.on_start_requested = None
        self.on_stop_requested = None

    def set_running(self, running: bool):
        def _update():
            self.start_button.config(state=tk.DISABLED if running else tk.NORMAL)
            self.stop_button.config(state=tk.NORMAL if running else tk.DISABLED)

        self.root.after(0, _update)

    def set_status(self, text: str):
        self.root.after(0, lambda: self.status_label.config(text=text))

    def set_question(self, text: str):
        self.root.after(0, lambda: self.question_var.set(text))

    def set_question_translation(self, text: str):
        self.root.after(0, lambda: self.question_ko_var.set(text))

    def set_answer_en(self, text: str):
        self.root.after(0, lambda: self.answer_en_var.set(text))

    def set_answer_ko(self, text: str):
        self.root.after(0, lambda: self.answer_ko_var.set(text))

    def add_history(self, question_en: str, question_ko: str, answer_en: str, answer_ko: str):
        entry = (
            f"Q (EN): {question_en}\n"
            f"Q (KO): {question_ko}\n"
            f"A (EN): {answer_en}\n"
            f"A (KO): {answer_ko}\n"
            f"{'-' * 72}\n"
        )

        def _append():
            self.history_text.config(state=tk.NORMAL)
            current = self.history_text.get("1.0", tk.END).strip()
            if current == "아직 질의응답 내역이 없습니다.":
                self.history_text.delete("1.0", tk.END)
            self.history_text.insert(tk.END, entry)
            self.history_text.see(tk.END)
            self.history_text.config(state=tk.DISABLED)

        self.root.after(0, _append)

    def _show_export_message(self):
        if callable(self.on_export_requested):
            self.on_export_requested()

    def run(self):
        self.root.mainloop()


# =========================
# Audio Capture + Simple VAD
# =========================
class AudioStreamManager:
    def __init__(self):
        self.audio_queue: queue.Queue[np.ndarray] = queue.Queue(maxsize=64)
        self.running = False
        self.stream = None

    def callback(self, indata, frames, time_info, status):
        if status:
            print("[audio status]", status)
        mono = np.squeeze(indata.copy())
        try:
            self.audio_queue.put_nowait(mono)
        except queue.Full:
            try:
                _ = self.audio_queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self.audio_queue.put_nowait(mono)
            except queue.Full:
                pass

    def start(self):
        self.running = True
        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="float32",
            blocksize=BLOCK_SIZE,
            callback=self.callback,
        )
        self.stream.start()

    def stop(self):
        self.running = False
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()


class SpeechSegmenter:
    def __init__(self):
        self.current_blocks: List[np.ndarray] = []
        self.speech_block_count = 0
        self.silence_block_count = 0

    @staticmethod
    def rms(audio_block: np.ndarray) -> float:
        return float(np.sqrt(np.mean(np.square(audio_block))))

    def process_block(self, block: np.ndarray) -> Optional[np.ndarray]:
        energy = self.rms(block)
        is_speech = energy >= SILENCE_RMS_THRESHOLD

        if is_speech:
            self.current_blocks.append(block)
            self.speech_block_count += 1
            self.silence_block_count = 0
            return None

        if self.current_blocks:
            self.current_blocks.append(block)
            self.silence_block_count += 1

            enough_speech = self.speech_block_count >= MIN_SPEECH_BLOCKS
            enough_silence = self.silence_block_count >= MIN_SILENCE_BLOCKS_TO_FLUSH

            if enough_speech and enough_silence:
                segment = np.concatenate(self.current_blocks)
                self.current_blocks = []
                self.speech_block_count = 0
                self.silence_block_count = 0
                return segment

            if not enough_speech and self.silence_block_count >= MIN_SILENCE_BLOCKS_TO_FLUSH:
                self.current_blocks = []
                self.speech_block_count = 0
                self.silence_block_count = 0

        return None


# =========================
# STT
# =========================
class RealTimeTranscriber:
    def __init__(self):
        self.model = WhisperModel(TRANSCRIBE_MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)

    def transcribe(self, audio: np.ndarray) -> str:
        audio = audio.astype(np.float32)
        segments, _ = self.model.transcribe(
            audio,
            language="en",
            vad_filter=False,
            beam_size=1,
            best_of=1,
            temperature=0.0,
            condition_on_previous_text=False,
        )
        text_parts = []
        for seg in segments:
            if seg.text:
                text_parts.append(seg.text.strip())
        return " ".join(text_parts).strip()


# =========================
# Transcript Buffer
# =========================
class RollingTranscriptBuffer:
    def __init__(self, max_seconds: int = ROLLING_CONTEXT_SEC):
        self.max_seconds = max_seconds
        self.buffer: Deque[TranscriptChunk] = deque()

    def add_text(self, text: str):
        now = time.time()
        self.buffer.append(TranscriptChunk(timestamp=now, text=text))
        self.evict_old(now)

    def evict_old(self, now: float):
        while self.buffer and now - self.buffer[0].timestamp > self.max_seconds:
            self.buffer.popleft()

    def get_context(self, max_chars: int = 500) -> str:
        now = time.time()
        self.evict_old(now)
        context = " ".join(chunk.text for chunk in self.buffer).strip()
        return context[-max_chars:]


# =========================
# Fast Question Processing
# =========================
class FastQuestionProcessor:
    QUESTION_STARTERS = {
        "what", "why", "how", "when", "where", "who", "which", "whose", "whom",
        "can", "could", "would", "should", "is", "are", "am", "do", "does", "did",
        "will", "may", "has", "have", "had"
    }
    PROMPT_HINTS = (
        "question for you", "quiz", "can anyone tell me", "tell me", "explain why",
        "what do you think", "who can", "why do you think", "how would you"
    )

    def __init__(self):
        self.last_trigger_time = 0.0

    def _normalize(self, text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    def is_question(self, text: str) -> bool:
        normalized = self._normalize(text)
        lowered = normalized.lower()
        if not lowered:
            return False
        if "?" in lowered:
            return True
        if any(hint in lowered for hint in self.PROMPT_HINTS):
            return True
        first_word = re.sub(r"^[^A-Za-z]+", "", lowered).split(" ", 1)[0]
        return first_word in self.QUESTION_STARTERS and len(lowered.split()) >= 3

    def should_trigger(self, text: str) -> bool:
        now = time.time()
        if not self.is_question(text):
            return False
        if now - self.last_trigger_time < QUESTION_COOLDOWN_SEC:
            return False
        self.last_trigger_time = now
        return True

    def extract_question(self, text: str) -> str:
        normalized = self._normalize(text)
        if not normalized:
            return ""

        parts = re.split(r"(?<=[?.!])\s+", normalized)
        candidates = [part.strip() for part in parts if part.strip()]

        for candidate in reversed(candidates):
            if "?" in candidate:
                return self._cleanup_question(candidate)

        for candidate in reversed(candidates):
            lowered = candidate.lower()
            first_word = re.sub(r"^[^A-Za-z]+", "", lowered).split(" ", 1)[0]
            if first_word in self.QUESTION_STARTERS or any(hint in lowered for hint in self.PROMPT_HINTS):
                return self._cleanup_question(candidate)

        return self._cleanup_question(normalized)

    def _cleanup_question(self, text: str) -> str:
        cleaned = self._normalize(text)
        cleaned = re.sub(r"^(so|now|okay|ok|well|then|and|but)\s+", "", cleaned, flags=re.IGNORECASE)
        if not cleaned.endswith("?"):
            cleaned += "?"
        return cleaned


# =========================
# Ollama Utility
# =========================
class OllamaClient:
    def __init__(self, model_name: str = OLLAMA_MODEL):
        self.model_name = model_name
        self.session = requests.Session()

    def generate(self, prompt: str, temperature: float = 0.2, num_predict: int = ANSWER_MAX_TOKENS) -> str:
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": num_predict,
            }
        }
        response = self.session.post(OLLAMA_URL, json=payload, timeout=OLLAMA_TIMEOUT_SEC)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()


# =========================
# Answer Generation (single LLM call)
# =========================
class BilingualAnswerGenerator:
    def __init__(self, ollama_client: OllamaClient):
        self.ollama_client = ollama_client

    def generate_package(self, context: str, question_en: str) -> dict:
        prompt = f"""
You are a fast real-time lecture assistant.

Given the lecture context and one extracted English question, return ONLY a JSON object with exactly these keys:
- question_ko
- answer_en
- answer_ko

Rules:
- answer_en: 1-2 short English sentences.
- answer_ko: natural Korean translation/summary of the English answer.
- question_ko: natural Korean translation of the question.
- Be concise and helpful.
- If context is weak, give the best short general answer.
- Do not include markdown fences.

Lecture context:
{context}

Question in English:
{question_en}
""".strip()

        try:
            raw = self.ollama_client.generate(prompt, temperature=0.2, num_predict=ANSWER_MAX_TOKENS)
            data = self._parse_json(raw)
            question_ko = self._clean_text(data.get("question_ko", "")) or "질문 번역 생성 실패"
            answer_en = self._postprocess_answer(self._clean_text(data.get("answer_en", "")))
            answer_ko = self._postprocess_answer(self._clean_text(data.get("answer_ko", "")))

            if not answer_en:
                answer_en = "I am not fully sure from the context, but here is the best short answer I can give."
            if not answer_ko:
                answer_ko = "문맥이 충분하지 않지만, 가능한 범위에서 짧게 답변했어요."

            return {
                "question_ko": question_ko,
                "answer_en": answer_en,
                "answer_ko": answer_ko,
            }
        except Exception as e:
            return {
                "question_ko": "질문 번역 실패",
                "answer_en": f"[Answer generation failed: {e}]",
                "answer_ko": f"[답변 생성 실패: {e}]",
            }

    def _parse_json(self, text: str) -> dict:
        cleaned = text.strip()
        cleaned = re.sub(r"^```json\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"^```\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
            if match:
                return json.loads(match.group(0))
            raise

    @staticmethod
    def _clean_text(text: str) -> str:
        return re.sub(r"\s+", " ", str(text)).strip()

    @staticmethod
    def _postprocess_answer(text: str) -> str:
        text = re.sub(r"\s+", " ", text).strip()
        sentences = re.split(r"(?<=[.!?])\s+", text)
        if len(sentences) > 2:
            text = " ".join(sentences[:2]).strip()
        return text


# =========================
# Q&A History
# =========================
class QAHistoryManager:
    def __init__(self):
        self.items: Deque[QAItem] = deque(maxlen=MAX_HISTORY_ITEMS)

    def add_item(self, question_en: str, question_ko: str, answer_en: str, answer_ko: str):
        self.items.append(QAItem(
            timestamp=time.time(),
            question_en=question_en,
            question_ko=question_ko,
            answer_en=answer_en,
            answer_ko=answer_ko,
        ))

    def export_json(self, output_path: str) -> str:
        payload = []
        for item in self.items:
            payload.append({
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(item.timestamp)),
                "question_en": item.question_en,
                "question_ko": item.question_ko,
                "answer_en": item.answer_en,
                "answer_ko": item.answer_ko,
            })
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return output_path


# =========================
# Main Orchestrator
# =========================
class WalkingEncyclopediaAI:
    def __init__(self, ui: FloatingAnswerWindow):
        self.ui = ui
        self.audio_manager = AudioStreamManager()
        self.segmenter = SpeechSegmenter()
        self.transcriber = RealTimeTranscriber()
        self.buffer = RollingTranscriptBuffer()
        self.question_processor = QuestionDetector(
            cooldown_sec=QUESTION_COOLDOWN_SEC,
            duplicate_window_sec=30,
        )
        self.ollama_client = OllamaClient()
        self.answer_generator = BilingualAnswerGenerator(self.ollama_client)
        self.history_manager = QAHistoryManager()
        self.worker_thread = threading.Thread(target=self._run_loop, daemon=True)
        self.running = False
        self.ui.on_export_requested = self.export_history
        self.ui.on_start_requested = self.start
        self.ui.on_stop_requested = self.stop

    def start(self):
        if self.running:
            return
        self.ui.set_status("마이크 연결 중...")
        self.audio_manager.start()
        self.running = True
        self.ui.set_running(True)
        if self.worker_thread.ident is not None:
            self.worker_thread = threading.Thread(target=self._run_loop, daemon=True)
        self.worker_thread.start()
        self.ui.set_status("실시간 청취 중")

    def stop(self):
        self.running = False
        self.audio_manager.stop()
        self.ui.set_running(False)
        self.ui.set_status("중지됨")

    def export_history(self):
        try:
            filename = f"qa_history_{time.strftime('%Y%m%d_%H%M%S')}.json"
            path = self.history_manager.export_json(filename)
            self.ui.set_status(f"Q&A 내역 저장 완료: {path}")
        except Exception as e:
            self.ui.set_status(f"Q&A 내역 저장 실패: {e}")

    def _run_loop(self):
        while self.running:
            try:
                block = self.audio_manager.audio_queue.get(timeout=1)
            except queue.Empty:
                continue

            segment = self.segmenter.process_block(block)
            if segment is None:
                continue

            self.ui.set_status("음성 인식 중...")
            text = self.transcriber.transcribe(segment)

            if not text:
                self.ui.set_status("실시간 청취 중")
                continue

            print(f"[transcript] {text}")
            self.buffer.add_text(text)

            decision = self.question_processor.should_trigger(text)
            if decision.is_question:
                extracted_question = decision.extracted_question
                if not extracted_question:
                    self.ui.set_status("실시간 청취 중")
                    continue

                self.ui.set_question(f"Q: {extracted_question}")
                self.ui.set_question_translation("Q (KO): 번역 생성 중...")
                self.ui.set_answer_en("A (EN): 답변 생성 중...")
                self.ui.set_answer_ko("A (KO): 답변 생성 중...")
                self.ui.set_status("질문 감지됨 → 영어/한국어 답변 생성 중...")

                package = self.answer_generator.generate_package(
                    self.buffer.get_context(),
                    extracted_question,
                )
                question_ko = package["question_ko"]
                answer_en = package["answer_en"]
                answer_ko = package["answer_ko"]

                self.ui.set_question_translation(f"Q (KO): {question_ko}")
                self.ui.set_answer_en(f"A (EN): {answer_en}")
                self.ui.set_answer_ko(f"A (KO): {answer_ko}")
                self.ui.add_history(extracted_question, question_ko, answer_en, answer_ko)
                self.history_manager.add_item(extracted_question, question_ko, answer_en, answer_ko)

            self.ui.set_status("실시간 청취 중")


# =========================
# Entrypoint
# =========================
def main():
    ui = FloatingAnswerWindow()
    app = WalkingEncyclopediaAI(ui)

    def start_app():
        try:
            app.start()
        except Exception as e:
            ui.set_answer_en(f"A (EN): 시작 실패: {e}")
            ui.set_answer_ko(f"A (KO): 시작 실패: {e}")
            ui.set_status("오류")

    def on_close():
        app.stop()
        ui.root.destroy()

    ui.root.protocol("WM_DELETE_WINDOW", on_close)
    ui.run()


if __name__ == "__main__":
    main()
