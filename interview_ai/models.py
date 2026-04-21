from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ApplicationMetadata:
    candidate_id: str
    job_id: str
    session_id: str
    timestamp: str

@dataclass
class InteractionSummary:
    total_questions_answered: int
    total_duration_seconds: float
    average_stt_confidence: float

@dataclass
class TranscriptItem:
    question_id: str
    timestamp: str
    raw_transcript: str
    normalized_text: str
    stt_confidence: Optional[float]
    duration_seconds: Optional[float] = None
    intent: Optional[str] = None
    noise_level: Optional[str] = None

@dataclass
class VoiceScreeningPayload:
    application: ApplicationMetadata
    interaction_summary: InteractionSummary
    transcript: List[TranscriptItem]
