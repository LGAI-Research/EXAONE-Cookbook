"""
프로젝트 루트 conftest: 루트를 sys.path에 넣어 test/core/* 에서 core 모듈 임포트 가능하게 함.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
