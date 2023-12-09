# Number 1-9, and A-Z
import enum
import subprocess
import sys

VERSION = "VERSIONADDEDBYGITHUB"
COPYRIGHT = "Copyright © YEARADDEDBYGITHUB Nate Harris. All rights reserved."

ASCII_ART = """
"""


def splash_logo() -> str:
    version = VERSION
    if "GITHUB" in version:
        try:
            last_commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
            version = f"git-{last_commit[:7]}"
        except subprocess.SubprocessError:
            version = "git-unknown-commit"
    return f"""
{ASCII_ART}
Version {version}, Python {sys.version}

{COPYRIGHT}
"""


class ScheduleType(enum.Enum):
    monthly = "monthly"
    weekly = "weekly"
    date_range = "date_range"
    always = "always"


def schedule_types() -> list[str]:
    """Return a list of Schedule Types

    Returns:
        List[ScheduleType]: List of Schedule Types
    """
    return [_enum.value for _enum in ScheduleType]
