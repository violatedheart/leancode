from __future__ import annotations

import os
import platform
import shutil
import subprocess
import ctypes
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Hardware:
    os: str
    ram_gb: float | None
    gpu: str | None
    gpu_memory_gb: float | None
    accelerator: str


@dataclass
class Recommendation:
    model: str
    context: int
    pull_command: str
    reason: str


def _command_output(*args: str) -> str:
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=4, check=False)
        return result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def detect_hardware() -> Hardware:
    ram: float | None = None
    if Path("/proc/meminfo").exists():
        try:
            mem = Path("/proc/meminfo").read_text(encoding="utf-8")
            value = next(int(line.split()[1]) for line in mem.splitlines() if line.startswith("MemTotal:"))
            ram = round(value / 1024 / 1024, 1)
        except (OSError, StopIteration, ValueError):
            pass
    if ram is None:
        output = _command_output("free", "-m")
        for line in output.splitlines():
            if line.lower().startswith("mem:"):
                try:
                    ram = round(int(line.split()[1]) / 1024, 1)
                except (IndexError, ValueError):
                    pass
                break
    if ram is None and platform.system() == "Windows":
        class MemoryStatus(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        status = MemoryStatus()
        status.dwLength = ctypes.sizeof(status)
        try:
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                ram = round(status.ullTotalPhys / 1024**3, 1)
        except (AttributeError, OSError):
            pass

    gpu = None
    gpu_memory = None
    accelerator = "cpu"
    nvidia = _command_output("nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits")
    if nvidia:
        first = nvidia.splitlines()[0].split(",", 1)
        gpu = first[0].strip()
        accelerator = "cuda"
        if len(first) > 1:
            try:
                gpu_memory = round(float(first[1].strip()) / 1024, 1)
            except ValueError:
                pass
    else:
        rocm = _command_output("rocm-smi", "--showproductname", "--showmeminfo", "vram")
        if rocm:
            gpu = rocm.splitlines()[0].strip()[:120]
            accelerator = "rocm"
        else:
            pci = _command_output("lspci")
            candidates = [line.strip() for line in pci.splitlines() if any(x in line.lower() for x in ("vga", "3d controller", "display controller"))]
            if candidates:
                gpu = candidates[0][:160]
                if any(x in gpu.lower() for x in ("amd", "advanced micro devices")):
                    accelerator = "rocm-unknown-vram"
                elif "nvidia" in gpu.lower():
                    accelerator = "cuda-unknown-vram"
    if ram is None:
        ram = round(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1024**3, 1) if hasattr(os, "sysconf") else None
    return Hardware(platform.platform(), ram, gpu, gpu_memory, accelerator)


def recommend(hardware: Hardware) -> Recommendation:
    gpu_memory = hardware.gpu_memory_gb or 0
    ram = hardware.ram_gb or 0
    if gpu_memory >= 6 or (hardware.accelerator == "cpu" and ram >= 12):
        model = "qwen2.5-coder:7b-instruct-q4_K_M"
        reason = "At least 6 GB of dedicated GPU memory or 12 GB of system RAM detected; a 7B 4-bit coder should fit with headroom."
    elif gpu_memory >= 3 or ram >= 6:
        model = "qwen2.5-coder:3b-instruct-q4_K_M"
        reason = "At least 3 GB of GPU memory or 6 GB of system RAM detected; a 3B 4-bit coder leaves room for the OS and KV cache."
    else:
        model = "qwen2.5-coder:1.5b-instruct-q4_0"
        reason = "Less than 5 GB available or memory is unknown; use the compact 1.5B 4-bit coder."
    return Recommendation(model, 4096, f"ollama pull {model}", reason)


def doctor_report() -> tuple[Hardware, Recommendation]:
    hardware = detect_hardware()
    return hardware, recommend(hardware)
