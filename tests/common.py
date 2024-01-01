import io
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = Path(__file__).parent / "data"


def read_raw_text(source: Path | io.StringIO) -> str:
    if isinstance(source, io.StringIO):
        return source.getvalue()
    with open(source, newline="", encoding="utf-8") as file:
        return file.read()


def write_raw_text(source: Path | io.StringIO, text: str) -> None:
    if isinstance(source, io.StringIO):
        source.write(text)
    else:
        with open(source, "w", newline="", encoding="utf-8") as file:
            file.write(text)
