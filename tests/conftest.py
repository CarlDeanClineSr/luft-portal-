import sys
from pathlib import Path
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def data_path(tmp_path):
    """Provide a temporary χ dataset for directive tests."""
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2025-01-01", periods=10, freq="1h"),
            "chi_amplitude": [0.11, 0.13, 0.14, 0.09, 0.08, 0.12, 0.1, 0.11, 0.13, 0.1],
        }
    )
    path = tmp_path / "chi_test.csv"
    df.to_csv(path, index=False)
    return path
