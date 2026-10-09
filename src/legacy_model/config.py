"""Runtime configuration of the Python model layer.

Only one setting exists for now: the location of the ecoinvent Master Data file used to resolve
seed and seedling exchanges (F6). The file is licensed material and is kept outside every git
repository; it is never copied into the repository.

Resolution order:
1. environment variable ``AGRITOOL_MASTER_DATA_PATH``;
2. ``agritool.cfg`` in the repository root (git-ignored), section ``[master_data]``, key ``path``.
"""
import configparser
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_FILE = REPO_ROOT / "agritool.cfg"
ENV_VAR = "AGRITOOL_MASTER_DATA_PATH"


def master_data_path():
    """Configured Master Data path (``Path``) or None when nothing is configured."""
    env = os.environ.get(ENV_VAR)
    if env:
        return Path(env)
    if CONFIG_FILE.is_file():
        parser = configparser.ConfigParser()
        parser.read(CONFIG_FILE, encoding="utf-8")
        value = parser.get("master_data", "path", fallback="")
        if value:
            return Path(value)
    return None


def require_master_data_path():
    """Configured Master Data path; raises a clear error when missing or not a file."""
    path = master_data_path()
    if path is None:
        raise RuntimeError(
            "ecoinvent Master Data path not configured: set %s or add [master_data] path=... "
            "to %s" % (ENV_VAR, CONFIG_FILE))
    if not path.is_file():
        raise FileNotFoundError("ecoinvent Master Data file not found: %s" % path)
    return path
