import os
import subprocess


def test_backend_module_importable_from_backend_cwd() -> None:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)

    result = subprocess.run(
        ["python", "-c", "import app.main"],
        cwd=".",
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
