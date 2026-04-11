"""Pytest configuration and shared fixtures."""

import pytest
import pandas as pd
from pathlib import Path


@pytest.fixture
def fixtures_dir() -> Path:
    """Return path to fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def pdfs_dir(fixtures_dir: Path) -> Path:
    """Return path to PDF fixtures directory."""
    return fixtures_dir / "pdfs"


@pytest.fixture
def expected_outputs_dir(fixtures_dir: Path) -> Path:
    """Return path to expected outputs directory."""
    return fixtures_dir / "expected_outputs"


@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    """Create a simple sample DataFrame for testing."""
    return pd.DataFrame(
        {
            "Name": ["Alice", "Bob", "Charlie"],
            "Age": [25, 30, 35],
            "City": ["New York", "London", "Tokyo"],
        }
    )


@pytest.fixture
def sample_thai_dataframe() -> pd.DataFrame:
    """Create a DataFrame with Thai content for testing."""
    return pd.DataFrame(
        {
            "ชื่อ": ["สมชาย", "สมหญิง", "วิชัย"],
            "นามสกุล": ["ใจดี", "รักษ์ไทย", "มั่นคง"],
            "อายุ": [25, 30, 35],
            "เงินเดือน": ["฿35,000", "฿45,000", "฿55,000"],
        }
    )


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Create a temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir
