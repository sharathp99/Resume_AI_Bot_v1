from __future__ import annotations

from app.schemas.candidate import CandidateStructuredExtraction
from app.services.extraction.resume_extractor import ResumeExtractor
from app.utils.deterministic_extraction import extract_contacts


RESUME_TEXT = """Alex Johnson
Senior Data Engineer
Seattle, WA
alex.johnson@example.com
(206) 555-0101
https://linkedin.com/in/alexjohnson
8 years of experience building Python, SQL, Spark, and AWS platforms.
"""



def test_deterministic_contact_extraction() -> None:
    contacts = extract_contacts(RESUME_TEXT)
    assert contacts["email"] == "alex.johnson@example.com"
    assert contacts["phone"] == "(206) 555-0101"
    assert "linkedin.com" in contacts["linkedin_url"]



def test_resume_extractor_heuristics() -> None:
    extractor = ResumeExtractor()
    extraction = extractor.extract(RESUME_TEXT)

    assert isinstance(extraction, CandidateStructuredExtraction)
    assert extraction.full_name == "Alex Johnson"
    assert "Python" in extraction.skills
    assert extraction.years_experience == 8
