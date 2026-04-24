"""
system_info.py
--------------
Lightweight host hardware detection for the System settings page.
"""

from __future__ import annotations

import platform
import subprocess
import json


WINDOWS_CPU_REGISTRY_KEY = r"HKLM:\HARDWARE\DESCRIPTION\System\CentralProcessor\0"
WINDOWS_GPU_REGISTRY_KEY = r"HKLM:\SYSTEM\CurrentControlSet\Control\Video"

GPU_VENDOR_HINTS = (
    "nvidia",
    "amd",
    "advanced micro devices",
    "ati",
    "intel",
)

GPU_EXCLUDE_HINTS = (
    "virtual",
    "parsec",
    "remote",
    "basic display",
    "microsoft basic",
    "hyper-v",
    "vmware",
    "virtualbox",
    "citrix",
)


def _run_powershell(command: str, timeout: int = 4) -> str:
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def detect_cpu_name() -> str:
    if platform.system() == "Windows":
        registry_name = _run_powershell(
            f"(Get-ItemProperty '{WINDOWS_CPU_REGISTRY_KEY}').ProcessorNameString"
        )
        if registry_name:
            return registry_name

    candidates = [
        platform.processor().strip(),
        platform.uname().processor.strip(),
    ]
    for candidate in candidates:
        if candidate:
            return candidate
    return "CPU not identified"


def _looks_like_real_gpu(name: str, provider: str, device_id: str) -> bool:
    combined = " ".join((name, provider, device_id)).lower()
    if any(hint in combined for hint in GPU_EXCLUDE_HINTS):
        return False
    if any(hint in combined for hint in GPU_VENDOR_HINTS):
        return True
    return "pci\\ven_" in combined


def _detect_gpu_names_windows() -> list[str]:
    command = rf"""
Get-ChildItem '{WINDOWS_GPU_REGISTRY_KEY}' | ForEach-Object {{
    Get-ChildItem $_.PSPath -ErrorAction SilentlyContinue |
        Where-Object {{ $_.PSChildName -match '^\d{{4}}$' }} |
        ForEach-Object {{
            try {{
                $p = Get-ItemProperty $_.PSPath
                [PSCustomObject]@{{
                    Name = $p.'HardwareInformation.AdapterString'
                    DriverDesc = $p.DriverDesc
                    ProviderName = $p.ProviderName
                    MatchingDeviceId = $p.MatchingDeviceId
                }}
            }} catch {{}}
        }}
}} | ConvertTo-Json -Compress
"""
    raw = _run_powershell(command, timeout=6)
    if not raw:
        return []

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []

    entries: list[tuple[str, str, str]] = []
    if isinstance(parsed, dict):
        parsed = [parsed]

    for item in parsed:
        if not isinstance(item, dict):
            continue
        name = str(item.get("Name") or "").strip()
        driver_desc = str(item.get("DriverDesc") or "").strip()
        provider = str(item.get("ProviderName") or "").strip()
        device_id = str(item.get("MatchingDeviceId") or "").strip()
        display_name = name or driver_desc
        if not display_name:
            continue
        entries.append((display_name, provider, device_id))

    preferred: list[str] = []
    fallback: list[str] = []
    seen: set[str] = set()

    for display_name, provider, device_id in entries:
        key = display_name.lower()
        if key in seen:
            continue
        seen.add(key)
        if _looks_like_real_gpu(display_name, provider, device_id):
            preferred.append(display_name)
        else:
            fallback.append(display_name)

    return preferred or fallback


def detect_gpu_names() -> list[str]:
    if platform.system() == "Windows":
        return _detect_gpu_names_windows()
    return []
