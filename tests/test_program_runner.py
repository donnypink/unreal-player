"""Tests for ProgramRunner class."""
import pytest
from unittest.mock import patch, MagicMock
import subprocess
from program_runner import ProgramRunner


class TestProgramRunner:
    """Tests for program execution."""

    def test_returns_false_for_missing_exe(self):
        """Returns False when executable doesn't exist."""
        runner = ProgramRunner()
        
        with patch('os.path.exists', return_value=False):
            result = runner.run("/fake/path.exe", "test", 30)
        
        assert result is False

    def test_returns_true_on_success(self):
        """Returns True when program runs successfully."""
        runner = ProgramRunner()
        
        with patch('os.path.exists', return_value=True):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                result = runner.run("/real/path.exe", "test", 30)
        
        assert result is True

    def test_returns_true_on_timeout(self):
        """Returns True when program times out (expected behavior)."""
        runner = ProgramRunner()
        
        with patch('os.path.exists', return_value=True):
            with patch('subprocess.run', side_effect=subprocess.TimeoutExpired("cmd", 30)):
                result = runner.run("/real/path.exe", "test", 30)
        
        assert result is True

    def test_returns_false_on_error(self):
        """Returns False when program fails to run."""
        runner = ProgramRunner()
        
        with patch('os.path.exists', return_value=True):
            with patch('subprocess.run', side_effect=Exception("Failed")):
                result = runner.run("/real/path.exe", "test", 30)
        
        assert result is False
