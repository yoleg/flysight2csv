from pathlib import Path
from typing import Iterable, Iterator, Sequence


def iter_matching_files(files_or_directories: Iterable[Path], glob_patterns: Sequence[str]) -> Iterator[Path]:
    """Yield all files that match any of the glob patterns in any of the files or directories."""
    for path in files_or_directories:
        if path.is_dir():
            for glob_pattern in glob_patterns:
                yield from path.glob(glob_pattern)
        elif path.is_file() and any(path.match(glob_pattern) for glob_pattern in glob_patterns):
            yield path
