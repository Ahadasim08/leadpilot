import csv
import pytest
from docx import Document
from app.services.parsing import parse_document


def test_parse_csv(tmp_path):
    p = tmp_path / "d.csv"
    with open(p, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["a", "b"])
        w.writerow(["1", "2"])
    out = parse_document(str(p), "csv")
    assert len(out) == 1
    assert "a" in out[0]["text"] and "1" in out[0]["text"]


def test_parse_docx(tmp_path):
    p = tmp_path / "d.docx"
    doc = Document()
    doc.add_paragraph("hello world")
    doc.save(str(p))
    out = parse_document(str(p), "docx")
    assert "hello world" in out[0]["text"]


def test_unsupported():
    with pytest.raises(ValueError):
        parse_document("x.txt", "txt")
