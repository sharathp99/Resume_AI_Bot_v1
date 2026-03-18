from __future__ import annotations

from app.services.jd.jd_parser import JobDescriptionParser



def test_jd_parser_extracts_skills_and_years() -> None:
    parser = JobDescriptionParser()
    jd = parser.parse(
        "Senior Data Engineer\nMust have Python, SQL, Airflow, and AWS. Preferred dbt. 5+ years of experience."
    )

    assert jd.role_title == "Senior Data Engineer"
    assert "Python" in jd.must_have_skills
    assert jd.years_required == 5
