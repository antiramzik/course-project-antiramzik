from pathlib import Path

from src.secure_upload import secure_save, sniff


def test_sniff_png_ok():
    data = b"\x89PNG\r\n\x1a\n" + b"1234"
    assert sniff(data) == "image/png"


def test_sniff_jpeg_ok():
    data = b"\xff\xd8hello-world\xff\xd9"
    assert sniff(data) == "image/jpeg"


def test_sniff_bad_returns_none():
    assert sniff(b"not_an_image") is None


def test_secure_save_rejects_big(tmp_path: Path):
    data = b"\x89PNG\r\n\x1a\n" + b"0" * 5_000_001
    try:
        secure_save(tmp_path, data)
        assert False, "expected ValueError('too_big')"
    except ValueError as exc:
        assert str(exc) == "too_big"


def test_secure_save_rejects_bad_type(tmp_path: Path):
    try:
        secure_save(tmp_path, b"just-bytes")
        assert False, "expected ValueError('bad_type')"
    except ValueError as exc:
        assert str(exc) == "bad_type"


def test_secure_save_ok_png(tmp_path: Path):
    data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
    path_str = secure_save(tmp_path, data)
    path = Path(path_str)

    assert path.exists()
    assert path.suffix == ".png"
    content = path.read_bytes()
    assert content.startswith(b"\x89PNG\r\n\x1a\n")
