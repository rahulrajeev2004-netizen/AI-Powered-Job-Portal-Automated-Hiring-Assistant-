import pytest
from utils.text_cleaner import clean_text, _normalize_heading

def test_heading_normalization():
    assert _normalize_heading("Work Experience:") == "EXPERIENCE"
    assert _normalize_heading("Professional Summary") == "SUMMARY"
    assert _normalize_heading("Technical Skills") == "SKILLS"
    assert _normalize_heading("Unknown Heading") == "Unknown Heading"
    assert _normalize_heading("Education") == "EDUCATION"
    
def test_clean_text_noise_removal():
    raw_text = "This is a random\ttext   with   spaces.\n\nAnd random \xa0 symbols! ©"
    cleaned = clean_text(raw_text)
    
    assert "text with spaces." in cleaned
    assert "symbols!" in cleaned
    assert "©" not in cleaned

def test_clean_text_normalizes_headings():
    raw_text = "Profile\nSoftware Engineer with 5 years experience.\n\nWork Experience:\nGoogle - 2020-2022"
    cleaned = clean_text(raw_text)
    
    lines = cleaned.split("\n")
    assert "SUMMARY" in lines
    assert "EXPERIENCE" in lines
    assert "Google - 2020-2022" in lines
    assert "Software Engineer with 5 years experience." in lines
