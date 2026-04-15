from pathlib import Path
import pytest
from career_ai.core.extractor import extract


def test_extract_txt(tmp_path):
    f = tmp_path / "cv.txt"
    f.write_text("Software Engineer with 5 years experience.")
    assert "Software Engineer" in extract(f)


def test_extract_md(tmp_path):
    f = tmp_path / "cv.md"
    f.write_text("# John Doe\n\n## Experience\n- Engineer at Acme")
    assert "Acme" in extract(f)


def test_unsupported_format(tmp_path):
    f = tmp_path / "cv.xyz"
    f.write_text("data")
    with pytest.raises(ValueError, match="Unsupported file format"):
        extract(f)
