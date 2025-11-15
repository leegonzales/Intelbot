"""macOS launchd scheduler integration."""

import os
import shutil
from pathlib import Path
import subprocess


PLIST_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.catalyst.research-agent</string>

    <key>ProgramArguments</key>
    <array>
        <string>{executable}</string>
        <string>run</string>
    </array>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>{hour}</integer>
        <key>Minute</key>
        <integer>{minute}</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>{log_dir}/launchd.stdout.log</string>

    <key>StandardErrorPath</key>
    <string>{log_dir}/launchd.stderr.log</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
    </dict>

    <key>WorkingDirectory</key>
    <string>{home}</string>

    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
"""


def get_plist_path() -> Path:
    """Get path to launchd plist."""
    return Path.home() / "Library/LaunchAgents/com.catalyst.research-agent.plist"


def install_launchd(hour: int = 7, minute: int = 0):
    """
    Install launchd job.

    Args:
        hour: Hour to run (0-23)
        minute: Minute to run (0-59)
    """
    # Find research-agent executable
    executable = shutil.which('research-agent')
    if not executable:
        raise RuntimeError(
            "research-agent not found in PATH. "
            "Please install the package first with: pip install -e ."
        )

    # Prepare plist content
    config_dir = Path.home() / ".research-agent"
    log_dir = config_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    plist_content = PLIST_TEMPLATE.format(
        executable=executable,
        hour=hour,
        minute=minute,
        log_dir=log_dir,
        home=Path.home()
    )

    # Write plist
    plist_path = get_plist_path()
    plist_path.parent.mkdir(parents=True, exist_ok=True)
    plist_path.write_text(plist_content)

    print(f"Created launchd plist: {plist_path}")
    print(f"Scheduled to run daily at {hour:02d}:{minute:02d}")

    # Load with launchctl
    try:
        subprocess.run(['launchctl', 'load', str(plist_path)], check=True)
        print("Loaded launchd job")
    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not load launchd job: {e}")
        print("You may need to load it manually with:")
        print(f"  launchctl load {plist_path}")


def uninstall_launchd():
    """Uninstall launchd job."""
    plist_path = get_plist_path()

    if not plist_path.exists():
        print("No launchd job found")
        return

    # Unload
    try:
        subprocess.run(['launchctl', 'unload', str(plist_path)], check=False)
        print("Unloaded launchd job")
    except Exception as e:
        print(f"Warning: Could not unload job: {e}")

    # Remove plist
    plist_path.unlink()
    print(f"Removed plist: {plist_path}")


def check_status() -> str:
    """
    Check if job is loaded.

    Returns:
        'loaded' or 'not loaded'
    """
    try:
        result = subprocess.run(
            ['launchctl', 'list'],
            capture_output=True,
            text=True,
            check=False
        )

        if 'com.catalyst.research-agent' in result.stdout:
            return "loaded"
        else:
            return "not loaded"

    except Exception as e:
        return f"error: {e}"
