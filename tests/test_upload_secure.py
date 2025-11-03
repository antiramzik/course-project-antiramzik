from pathlib import Path

from app.utils.upload_secure import MAX_BYTES, secure_save, sniff_image_type


def test_sniff_image_type_ok_png():
    data = b"\x89PNG\r\n\x1a\n" + b"12345"
    assert sniff_image_type(data) == "image/png"


def test_sniff_image_type_ok_jpeg():
    data = b"\xff\xd8" + b"abc" + b"\xff\xd9"
    assert sniff_image_type(data) == "image/jpeg"


def test_secure_save_too_big(tmp_path: Path):
    data = b"\x89PNG\r\n\x1a\n" + b"0" * (MAX_BYTES + 1)
    try:
        secure_save(tmp_path, data)
        assert False, "Expected ValueError('too_big')"
    except ValueError as e:
        assert str(e) == "too_big"


def test_secure_save_bad_type(tmp_path: Path):
    try:
        secure_save(tmp_path, b"not_an_image")
        assert False, "Expected ValueError('bad_type')"
    except ValueError as e:
        assert str(e) == "bad_type"


def test_secure_save_ok_png(tmp_path: Path):
    data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
    path = secure_save(tmp_path, data)
    p = Path(path)
    assert p.exists()
    assert p.suffix == ".png"
    assert p.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
