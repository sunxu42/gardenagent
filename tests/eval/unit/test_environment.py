from unittest.mock import patch

from eval.infrastructure.environment import capture_run_environment


def test_capture_run_environment_without_git() -> None:
    with patch("eval.infrastructure.environment._git_commit", return_value=None):
        with patch("eval.infrastructure.environment._git_dirty", return_value=None):
            env = capture_run_environment(config=None)
    assert env.git_commit is None
    assert env.python_version
