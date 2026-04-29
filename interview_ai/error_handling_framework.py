import json
import logging
import re
import threading
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Set


class CallState(Enum):
    INIT = auto()
    ASKING_QUESTION = auto()
    WAITING_RESPONSE = auto()
    PROCESSING = auto()
    RETRYING = auto()
    CLARIFYING = auto()
    SKIPPED = auto()
    ESCALATED = auto()
    COMPLETED = auto()
    FAILED = auto()


class EscalationRoute(Enum):
    CALLBACK_REQUEST = "CALLBACK_REQUEST"
    SMS_FOLLOWUP = "SMS_FOLLOWUP"
    HUMAN_RECRUITER = "HUMAN_RECRUITER"
    MULTILINGUAL_AGENT = "MULTILINGUAL_AGENT"
    SUPERVISOR_QUEUE = "SUPERVISOR_QUEUE"


@dataclass(frozen=True)
class SilenceEvent:
    event: str = "SILENCE_TIMEOUT"
    seconds: int = 0
    action: str = "NONE"


@dataclass(frozen=True)
class NLPResult:
    languages_detected: List[str]
    primary_language: str
    normalized_text: str
    confidence: float


@dataclass(frozen=True)
class DetectionResult:
    missing_answer: bool
    reason: Optional[str]
    severity: str


@dataclass(frozen=True)
class EscalationResult:
    route_to: str
    priority: str
    reason: str


@dataclass
class AnalyticsEvent:
    session_id: str
    candidate_id: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    question_id: Optional[str] = None
    state: str = "INIT"
    detected_error: Optional[str] = None
    retry_count: int = 0
    escalation_triggered: bool = False
    resolution_status: str = "PENDING"


class SilenceTimer:
    def __init__(self):
        self.thresholds = {
            3: "REPROMPT",
            7: "RETRY_QUESTION",
            12: "SKIP_FALLBACK"
        }

    def process_silence(self, seconds: int) -> SilenceEvent:
        action = "NONE"
        if seconds >= 12:
            action = "SKIP_FALLBACK"
        elif seconds >= 7:
            action = "RETRY_QUESTION"
        elif seconds >= 3:
            action = "REPROMPT"
            
        return SilenceEvent(seconds=seconds, action=action)


class MultilingualNLPProcessor:
    def __init__(self):
        self.language_patterns = {
            "Hindi": [r"\bhaan\b", r"\bnahi\b", r"\bhai\b", r"\bkar\b", r"\bexperience hai\b", r"\bbaat\b", r"\bkam\b", r"\bzyada\b", r"\bthik\b"],
            "Malayalam": [r"\bcheyyam\b", r"\bindu\b", r"\bnjan\b", r"\benikku\b", r"\bella\b", r"\bmadi\b", r"\bivide\b", r"\bundo\b"],
            "Tamil": [r"\bpanren\b", r"\birukku\b", r"\billa\b", r"\bnaan\b", r"\bvenum\b", r"\btheriyum\b", r"\beppo\b", r"\benga\b"],
            "Telugu": [r"\bchesta\b", r"\bundu\b", r"\bledu\b", r"\bnenu\b", r"\bkaavali\b", r"\btelusu\b", r"\beppudu\b", r"\bekkada\b"],
            "Kannada": [r"\bmadtini\b", r"\bide\b", r"\billa\b", r"\bnaanu\b", r"\bbeku\b", r"\bgothu\b"],
            "English": [r"\byes\b", r"\bno\b", r"\bi am\b", r"\bexperience\b", r"\bknow\b", r"\bworking\b", r"\bproject\b", r"\busing\b"]
        }

    def process(self, text: str) -> NLPResult:
        detected = []
        text_lower = text.lower()
        
        for lang, patterns in self.language_patterns.items():
            if any(re.search(p, text_lower) for p in patterns):
                detected.append(lang)
        
        if not detected:
            detected = ["English"]
            
        primary = detected[0]
        is_mixed = len(detected) > 1
        
        if "English" in detected and is_mixed:
            primary = "English"
            
        return NLPResult(
            languages_detected=detected,
            primary_language=primary,
            normalized_text=text.strip(),
            confidence=0.95 if not is_mixed else 0.85
        )


class MissingAnswerDetector:
    def __init__(self):
        self.vague_keywords = {"hmm", "uh", "um", "maybe", "not sure", "don't know", "skip", "next", "pass"}
        self.evasive_patterns = [
            r"\bwhy do you ask\b",
            r"\bnot comfortable\b",
            r"\bask something else\b",
            r"\bcan't say\b",
            r"\bno comments\b",
            r"\bi don't want to answer\b",
            r"\bnext question please\b",
            r"\bprefer not to say\b"
        ]

    def detect(self, text: str) -> DetectionResult:
        text_lower = text.lower().strip()
        
        if not text_lower or len(text_lower.split()) < 1:
            return DetectionResult(True, "empty_response", "HIGH")
            
        if text_lower in self.vague_keywords:
            return DetectionResult(True, "vague_response", "MEDIUM")
            
        if any(re.search(p, text_lower) for p in self.evasive_patterns):
            return DetectionResult(True, "evasive_response", "HIGH")
            
        if len(text_lower.split()) == 1 and text_lower not in {"yes", "no", "sure"}:
            return DetectionResult(True, "one_word_unclear", "LOW")
            
        return DetectionResult(False, None, "NONE")


class BackgroundNoiseDetector:
    def __init__(self):
        self.noise_tokens = {"[noise]", "[background]", "[static]", "[inaudible]", "[cough]", "[click]"}
        self.noise_threshold = 0.5  # If more than 50% of tokens are noise

    def detect(self, text: str, confidence: float) -> Dict[str, Any]:
        text_lower = text.lower()
        tokens = text_lower.split()
        
        if not tokens:
            return {"is_noisy": confidence < 0.3, "reason": "empty_audio" if confidence < 0.3 else None}
            
        noise_count = sum(1 for t in tokens if t in self.noise_tokens)
        noise_ratio = noise_count / len(tokens)
        
        is_noisy = noise_ratio > self.noise_threshold or confidence < 0.35
        
        return {
            "is_noisy": is_noisy,
            "noise_ratio": noise_ratio,
            "confidence": confidence,
            "reason": "high_background_noise" if is_noisy else None
        }


class CallStateMachine:
    def __init__(self):
        self._current_state = CallState.INIT
        self._valid_transitions = {
            CallState.INIT: {CallState.ASKING_QUESTION, CallState.FAILED},
            CallState.ASKING_QUESTION: {CallState.WAITING_RESPONSE, CallState.FAILED},
            CallState.WAITING_RESPONSE: {CallState.PROCESSING, CallState.RETRYING, CallState.CLARIFYING, CallState.FAILED},
            CallState.PROCESSING: {CallState.ASKING_QUESTION, CallState.COMPLETED, CallState.SKIPPED, CallState.FAILED},
            CallState.RETRYING: {CallState.WAITING_RESPONSE, CallState.ESCALATED, CallState.FAILED},
            CallState.CLARIFYING: {CallState.WAITING_RESPONSE, CallState.FAILED},
            CallState.SKIPPED: {CallState.ASKING_QUESTION, CallState.COMPLETED, CallState.FAILED},
            CallState.ESCALATED: {CallState.FAILED, CallState.COMPLETED},
            CallState.COMPLETED: set(),
            CallState.FAILED: set()
        }

    @property
    def state(self) -> str:
        return self._current_state.name

    def transition_to(self, new_state: CallState) -> bool:
        if new_state in self._valid_transitions.get(self._current_state, set()):
            self._current_state = new_state
            return True
        return False


class EscalationRouter:
    def __init__(self):
        self.failure_threshold = 3

    def route(self, error_type: str, count: int, text: Optional[str] = None) -> EscalationResult:
        if text and any(word in text.lower() for word in ["abuse", "stupid", "idiot", "hate"]):
            return EscalationResult("HUMAN_RECRUITER", "CRITICAL", "Abusive language detected")

        if error_type == "POOR_AUDIO" and count >= self.failure_threshold:
            return EscalationResult("CALLBACK_REQUEST", "HIGH", "Repeated poor audio")
            
        if error_type == "SILENCE" and count >= self.failure_threshold:
            return EscalationResult("SMS_FOLLOWUP", "MEDIUM", "Repeated silence failures")
            
        if error_type == "UNSUPPORTED_LANGUAGE":
            return EscalationResult("MULTILINGUAL_AGENT", "HIGH", "Candidate requested different language")
            
        if error_type == "SYSTEM_CRASH":
            return EscalationResult("SUPERVISOR_QUEUE", "CRITICAL", "Internal system failure")
            
        if error_type == "BACKGROUND_NOISE" and count >= self.failure_threshold:
            return EscalationResult("CALLBACK_REQUEST", "HIGH", "Persistent background noise")
            
        return EscalationResult("NONE", "LOW", "No escalation needed")


class AnalyticsLogger:
    def __init__(self, log_file: str = "call_analytics.jsonl"):
        self.log_file = log_file
        self._lock = threading.Lock()

    def log(self, event: AnalyticsEvent):
        with self._lock:
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(asdict(event)) + "\n")
            except Exception as e:
                logging.error(f"Failed to write analytics log: {e}")


class ErrorHandlingFramework:
    """
    Consolidated Master Robustness Engine and Error Handling Framework.
    Orchestrates silence timing, multilingual NLP, missing answer detection,
    call state management, escalation routing, and analytics logging.
    """
    def __init__(self, session_id: str, candidate_id: str):
        self.session_id = session_id
        self.candidate_id = candidate_id
        self.silence_timer = SilenceTimer()
        self.nlp_processor = MultilingualNLPProcessor()
        self.answer_detector = MissingAnswerDetector()
        self.state_machine = CallStateMachine()
        self.router = EscalationRouter()
        self.logger = AnalyticsLogger()
        self.noise_detector = BackgroundNoiseDetector()
        
        self.retry_counts: Dict[str, int] = {}
        self.current_question_id: Optional[str] = None

    def handle_silence(self, seconds: int) -> Dict[str, Any]:
        event = self.silence_timer.process_silence(seconds)
        self.retry_counts["SILENCE"] = self.retry_counts.get("SILENCE", 0) + 1
        
        if event.action == "SKIP_FALLBACK":
            self.state_machine.transition_to(CallState.SKIPPED)
        elif event.action == "RETRY_QUESTION":
            self.state_machine.transition_to(CallState.RETRYING)
            
        log_entry = AnalyticsEvent(
            session_id=self.session_id,
            candidate_id=self.candidate_id,
            question_id=self.current_question_id,
            state=self.state_machine.state,
            detected_error="SILENCE",
            retry_count=self.retry_counts["SILENCE"]
        )
        
        escalation = self.router.route("SILENCE", self.retry_counts["SILENCE"])
        if escalation.route_to != "NONE":
            self.state_machine.transition_to(CallState.ESCALATED)
            log_entry.escalation_triggered = True
            
        self.logger.log(log_entry)
        
        return {
            "silence_event": asdict(event),
            "escalation": asdict(escalation) if escalation.route_to != "NONE" else None,
            "next_state": self.state_machine.state
        }

    def process_response(self, text: str, question_id: str, confidence: float = 1.0) -> Dict[str, Any]:
        self.current_question_id = question_id
        self.state_machine.transition_to(CallState.PROCESSING)
        
        # 1. Noise Detection
        noise_res = self.noise_detector.detect(text, confidence)
        
        # 2. NLP and Answer Detection
        nlp_res = self.nlp_processor.process(text)
        detection = self.answer_detector.detect(text)
        
        # 3. Decision Logic
        action = "CONTINUE"
        reason = None
        
        if noise_res["is_noisy"]:
            self.retry_counts["BACKGROUND_NOISE"] = self.retry_counts.get("BACKGROUND_NOISE", 0) + 1
            self.state_machine.transition_to(CallState.RETRYING)
            action = "REPROMPT"
            reason = "background_noise"
        elif confidence < 0.45:
            self.retry_counts["POOR_AUDIO"] = self.retry_counts.get("POOR_AUDIO", 0) + 1
            self.state_machine.transition_to(CallState.RETRYING)
            action = "REPROMPT"
            reason = "poor_audio_quality"
        elif detection.missing_answer:
            self.retry_counts["MISSING_ANSWER"] = self.retry_counts.get("MISSING_ANSWER", 0) + 1
            self.state_machine.transition_to(CallState.CLARIFYING)
            action = "REPROMPT"
            reason = detection.reason
            
        # Check for Escalation
        error_type = reason.upper() if reason else "NONE"
        escalation = self.router.route(error_type, self.retry_counts.get(error_type, 0), text)
        
        if escalation.route_to != "NONE":
            self.state_machine.transition_to(CallState.ESCALATED)
            action = "ESCALATE"
            
        # 4. Logging
        log_entry = AnalyticsEvent(
            session_id=self.session_id,
            candidate_id=self.candidate_id,
            question_id=question_id,
            state=self.state_machine.state,
            detected_error=reason,
            retry_count=self.retry_counts.get(error_type, 0),
            escalation_triggered=(action == "ESCALATE")
        )
        self.logger.log(log_entry)
        
        return {
            "nlp": asdict(nlp_res),
            "detection": asdict(detection),
            "noise": noise_res,
            "action": action,
            "reason": reason,
            "escalation": asdict(escalation) if action == "ESCALATE" else None,
            "next_state": self.state_machine.state
        }

    def trigger_escalation(self, error_type: str, reason: str):
        escalation = self.router.route(error_type, self.retry_counts.get(error_type, 0))
        self.state_machine.transition_to(CallState.ESCALATED)
        
        self.logger.log(AnalyticsEvent(
            session_id=self.session_id,
            candidate_id=self.candidate_id,
            state=self.state_machine.state,
            detected_error=error_type,
            escalation_triggered=True,
            resolution_status="ESCALATED"
        ))
        return asdict(escalation)
