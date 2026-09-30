"""Person-down heuristic tests (#32)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from inference.person_down import detect_person_down


def test_lying_person_detected():
    # wide bbox — person horizontal
    assert detect_person_down((100, 200, 300, 250), threshold=1.4) is True


def test_standing_person_not_flagged():
    assert detect_person_down((100, 50, 160, 250), threshold=1.4) is False
