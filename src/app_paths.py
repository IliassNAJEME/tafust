import os
import sys


def get_project_root() -> str:
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_runtime_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return get_project_root()


def get_resource_path(*parts: str) -> str:
    return os.path.join(get_project_root(), *parts)


def get_data_dir() -> str:
    if os.name == "nt":
        base = os.getenv("LOCALAPPDATA") or get_runtime_dir()
        return os.path.join(base, "Tafust", "tafust_data")
    return os.path.join(get_runtime_dir(), "tafust_data")
