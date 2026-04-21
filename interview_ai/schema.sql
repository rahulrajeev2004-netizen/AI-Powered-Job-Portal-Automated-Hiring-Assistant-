-- Minimal ATS Voice Transcript Extraction Schema (Day-23)

CREATE TABLE sessions (
    session_id UUID PRIMARY KEY,
    candidate_id UUID NOT NULL,
    job_id VARCHAR(50) NOT NULL,
    total_questions INT NOT NULL,
    total_duration_seconds FLOAT NOT NULL,
    average_stt_confidence FLOAT NOT NULL,
    -- Minimal Profile Extraction
    current_location VARCHAR(255),
    salary_current VARCHAR(50),
    salary_expected VARCHAR(50),
    notice_period_days VARCHAR(50),
    willing_to_relocate VARCHAR(10)
);

CREATE TABLE transcripts (
    transcript_id UUID PRIMARY KEY,
    session_id UUID REFERENCES sessions(session_id) ON DELETE CASCADE,
    question_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    raw_transcript TEXT NOT NULL,
    normalized_text TEXT NOT NULL,
    stt_confidence FLOAT,
    duration_seconds FLOAT,
    intent VARCHAR(50),
    noise_level VARCHAR(20)
);
