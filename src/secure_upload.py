import uuid
from pathlib import Path

MAX_BYTES = 5_000_000
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_SOI = b"\xff\xd8"
JPEG_EOI = b"\xff\xd9"


def sniff(data: bytes):
    """
    Определяет тип изображения по magic bytes:
    - PNG по сигнатуре PNG_MAGIC
    - JPEG по паре SOI/EOI
    Возвращает MIME-тип или None.
    """
    if data.startswith(PNG_MAGIC):
        return "image/png"
    if data.startswith(JPEG_SOI) and data.endswith(JPEG_EOI):
        return "image/jpeg"
    return None


def secure_save(base_dir: Path, data: bytes) -> str:
    """
    Безопасно сохраняет PNG/JPEG:
    - проверяет максимальный размер (MAX_BYTES);
    - проверяет magic bytes (только PNG/JPEG);
    - нормализует путь и не выходит за пределы base_dir;
    - запрещает симлинки в родительских директориях;
    - сохраняет файл под UUID-именем с нужным расширением.

    Ошибки:
    - ValueError("too_big")       — размер больше MAX_BYTES;
    - ValueError("bad_type")      — не PNG/JPEG;
    - ValueError("path_traversal") — выход за пределы base_dir;
    - ValueError("symlink_parent") — симлинк в одном из родителей пути.
    """
    if len(data) > MAX_BYTES:
        raise ValueError("too_big")

    content_type = sniff(data)
    if content_type is None:
        raise ValueError("bad_type")

    root = Path(base_dir).resolve(strict=True)

    ext = ".png" if content_type == "image/png" else ".jpg"
    name = f"{uuid.uuid4()}{ext}"
    path = (root / name).resolve()

    if not str(path).startswith(str(root)):
        raise ValueError("path_traversal")

    if any(parent.is_symlink() for parent in path.parents):
        raise ValueError("symlink_parent")

    path.write_bytes(data)
    return str(path)
