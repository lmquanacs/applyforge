from codelens.core.chunking import collect_chunks, _is_secret


def test_secret_file_excluded():
    assert _is_secret(".env") is True
    assert _is_secret("MyService.java") is False


def test_collect_chunks_empty_dir(tmp_path):
    chunks = collect_chunks(str(tmp_path), "generic", [])
    assert chunks == []
