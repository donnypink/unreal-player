"""Tests for ProgramRunner class."""
import pytest
from unittest.mock import patch, MagicMock, Mock
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
        
        # Mock Popen to return a process that completes successfully
        mock_process = MagicMock()
        mock_process.wait.return_value = 0
        
        with patch('os.path.exists', return_value=True):
            with patch('subprocess.Popen', return_value=mock_process) as mock_popen:
                result = runner.run("/real/path.exe", "test")
        
        assert result is True
        mock_popen.assert_called_once()

    def test_returns_false_on_error(self):
        """Returns False when program fails to run."""
        runner = ProgramRunner()
        
        with patch('os.path.exists', return_value=True):
            with patch('subprocess.Popen', side_effect=Exception("Failed")):
                result = runner.run("/real/path.exe", "test")
        
        assert result is False

    def test_runs_without_timeout(self):
        """Runs program without timeout (waits for manual close)."""
        runner = ProgramRunner()
        
        mock_process = MagicMock()
        mock_process.wait.return_value = 0
        
        with patch('os.path.exists', return_value=True):
            with patch('subprocess.Popen', return_value=mock_process) as mock_popen:
                runner.run("/real/path.exe", "test")
                
                # Verify Popen was called
                mock_popen.assert_called_once()
                # Verify wait was called (not terminate/kill)
                mock_process.wait.assert_called_once()

    def test_terminate_gracefully(self):
        """Test graceful termination."""
        runner = ProgramRunner()
        
        mock_process = MagicMock()
        mock_process.pid = 1234
        mock_process.wait.return_value = 0  # Process exits gracefully
        
        runner.current_process = mock_process
        
        with patch('os.kill') as mock_kill:
            result = runner.terminate()
        
        assert result is True
        # On Windows, os.kill is called with CTRL_BREAK_EVENT
        mock_kill.assert_called_once()
        # Process should be cleared
        assert runner.current_process is None

    def test_terminate_force_kill_on_timeout(self):
        """Test force kill when graceful termination times out."""
        runner = ProgramRunner()
        
        mock_process = MagicMock()
        mock_process.pid = 1234
        # First wait times out, second wait after kill succeeds
        mock_process.wait.side_effect = [subprocess.TimeoutExpired(None, 5), 0]
        
        runner.current_process = mock_process
        
        with patch('os.kill') as mock_kill:
            result = runner.terminate()
        
        assert result is True
        # os.kill called for CTRL_BREAK_EVENT
        mock_kill.assert_called_once()
        # kill() called after timeout
        mock_process.kill.assert_called_once()
        assert runner.current_process is None

    def test_terminate_no_process(self):
        """Test terminate when no process running."""
        runner = ProgramRunner()
        
        result = runner.terminate()
        
        assert result is True
