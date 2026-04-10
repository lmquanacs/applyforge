from codelens.core.discovery import discover
import os, tempfile


def test_detect_spring_boot():
    with tempfile.TemporaryDirectory() as tmp:
        open(os.path.join(tmp, "pom.xml"), "w").close()
        result = discover(tmp)
        assert result["hint"] == "spring-boot"


def test_detect_generic():
    with tempfile.TemporaryDirectory() as tmp:
        result = discover(tmp)
        assert result["hint"] == "generic"
