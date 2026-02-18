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
            result = runner.run("/fake/path.exe", "test")
        
        assert result is False

    def test_returns_true_on_success(self):
        """Returns True when program runs and exits."""
        runner = ProgramRunner()
        
        with patch('os.path.exists', return_value=True):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                result = runner.run("/real/path.exe", "test")
        
        assert result is True

    def test_returns_false_on_error(self):
        """Returns False when program fails to run."""
        runner = ProgramRunner()
        
        with patch('os.path.exists', return_value=True):
            with patch('subprocess.run', side_effect=Exception("Failed")):
                result = runner.run("/real/path.exe", "test")
        
        assert result is False

    def test_runs_without_timeout(self):
        """Runs program without timeout (waits for manual close)."""
        runner = ProgramRunner()
        
        with patch('os.path.exists', return_value=True):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                runner.run("/real/path.exe", "test")
                
                # Verify no timeout parameter passed
                call_args = mock_run.call_args
                assert 'timeout' not in call_args.kwargs
