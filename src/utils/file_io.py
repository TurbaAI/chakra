import gzip
import logging
from gzip import GzipFile
from pathlib import Path
from typing import IO

logger = logging.getLogger(__name__)


def open_file_read(file_path: str | Path, mode: str = "rb") -> GzipFile | IO:
    if isinstance(file_path, str):
        file_path = Path(file_path)

    if not file_path.exists():
        msg = f"{file_path} does not exist!"
        raise FileNotFoundError(msg)

    try:
        in_file = gzip.open(file_path.as_posix(), mode)
        in_file.seek(1)
        in_file.seek(0)
    except IOError:
        if file_path.as_posix().endswith(".gz"):
            logger.warning(
                "File path %s has `.gz` extension but does not seem to be zipped! Attempting to open regularly!",
                file_path.as_posix(),
            )
        in_file = file_path.open(mode)
    return in_file


def open_file_write(file_path: str | Path, mode: str = "wb") -> GzipFile | IO:
    if isinstance(file_path, str):
        file_path = Path(file_path)

    if not file_path.parent.exists():
        logger.warning("Directory %s does not exist. It will be created!", file_path.parent.as_posix())
        file_path.parent.mkdir(parents=True, exist_ok=True)

    if file_path.as_posix().endswith(".gz"):
        return gzip.open(file_path.as_posix(), mode)
    else:
        return file_path.open(mode)
