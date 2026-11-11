"""Capture real Windows console windows, never a synthetic terminal image."""
import json
import os
from pathlib import Path
import subprocess
import time

SCRIPT = Path(__file__).with_name("capture_terminal.ps1")


def launch(args, transcript, destination, cwd):
    if os.name != "nt":
        raise RuntimeError("Automatic terminal capture requires an interactive Windows desktop.")
    config = Path(str(destination) + ".command.json")
    config.write_text(json.dumps({"args": list(map(str, args)), "cwd": str(cwd)}), encoding="utf-8")
    return subprocess.Popen([
        "conhost.exe", "powershell.exe", "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(SCRIPT), "-Transcript", str(transcript), "-Destination", str(destination),
        "-CommandConfig", str(config),
    ])


def verify(destination):
    destination = Path(destination)
    status = Path(str(destination) + ".status")
    if not status.exists() or status.read_text(encoding="utf-8-sig") != "PASS" or not destination.exists():
        message = status.read_text(encoding="utf-8-sig") if status.exists() else "No capture result"
        raise RuntimeError(f"Terminal capture failed: {message}")


def capture(transcript, destination):
    process = subprocess.Popen([
        "conhost.exe", "powershell.exe", "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(SCRIPT), "-Transcript", str(transcript), "-Destination", str(destination),
    ])
    try:
        process.wait(timeout=30)
        verify(destination)
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=10)


def command(args, folder, name, timeout, cwd):
    destination = folder / (Path(name).stem + ".png")
    process = launch(args, folder / name, destination, cwd)
    try:
        process.wait(timeout=timeout)
        verify(destination)
        return (folder / name).read_text(encoding="utf-8-sig")
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=10)
