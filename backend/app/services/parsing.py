import pandas as pd
from pypdf import PdfReader
from docx import Document


def parse_document(path: str, file_type: str) -> list[dict]:
    ft = file_type.lower()
    if ft == "pdf":
        reader = PdfReader(path)
        out = []
        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                out.append({"text": text, "page_number": i, "section": None})
        return out
    if ft == "docx":
        doc = Document(path)
        text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        return [{"text": text, "page_number": None, "section": None}]
    if ft == "csv":
        df = pd.read_csv(path)
        return [{"text": df.to_csv(index=False), "page_number": None, "section": None}]
    raise ValueError(f"Unsupported file type: {file_type}")
