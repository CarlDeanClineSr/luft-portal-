from pathlib import Path
import sys

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from downstream_input_guard import (
    CANONICAL_PROTOCOL,
    LegacyInputError,
    require_canonical_chi,
)


def test_guard_accepts_unclipped_canonical_values():
    frame = pd.DataFrame({"chi_B24M": [0.1, 1.0, 2.0]})
    values = require_canonical_chi(frame, protocol_id=CANONICAL_PROTOCOL)
    assert values.max() == 2.0


def test_guard_rejects_legacy_only_input():
    frame = pd.DataFrame({"chi_amplitude": [0.15, 0.15]})
    with pytest.raises(LegacyInputError, match="legacy-like columns"):
        require_canonical_chi(frame)


def test_guard_rejects_generic_chi_name():
    frame = pd.DataFrame({"chi": [0.1]})
    with pytest.raises(LegacyInputError, match="generic column"):
        require_canonical_chi(frame, column="chi")
