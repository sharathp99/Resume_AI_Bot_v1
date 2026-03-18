from __future__ import annotations

from pathlib import Path

import fitz
from docx import Document

DATA = {
    "data_engineer": [
        (
            "alex_johnson.pdf",
            "Alex Johnson\nSenior Data Engineer\nSeattle, WA\nalex.johnson@example.com\n(206) 555-0101\nhttps://linkedin.com/in/alexjohnson\n8 years of experience building Python, SQL, Spark, Airflow, AWS, and dbt pipelines for fintech analytics.\nEducation: BS Computer Science.\nSummary: Built batch and streaming ETL platforms in Snowflake and AWS.",
        ),
        (
            "jamie_lee.docx",
            "Jamie Lee\nData Engineer\nAustin, TX\njamie.lee@example.com\n(512) 555-0132\nhttps://github.com/jamielee\n5 years of experience with Python, SQL, Airflow, dbt, and Tableau in healthcare analytics.\nEducation: MS Information Systems.\nSummary: Owned ELT pipelines and BI data marts.",
        ),
    ]
}


def write_pdf(path: Path, text: str) -> None:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()


def write_docx(path: Path, text: str) -> None:
    document = Document()
    for line in text.split("\n"):
        document.add_paragraph(line)
    document.save(path)


if __name__ == "__main__":
    root = Path("data/resumes")
    for role, docs in DATA.items():
        folder = root / role
        folder.mkdir(parents=True, exist_ok=True)
        for filename, text in docs:
            destination = folder / filename
            if destination.suffix == ".pdf":
                write_pdf(destination, text)
            else:
                write_docx(destination, text)
    print("Sample resume data generated under data/resumes")
