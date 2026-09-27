"""Smoke test: every module imports (catches NameErrors/typos like the old ChatDisplay bug)."""
import importlib

import pytest

MODULES = [
    "src.services.ollama_service",
    "src.services.chat_manager",
    "src.services.rag",
    "src.services.system_monitor",
    "src.utils.helpers",
]


@pytest.mark.parametrize("name", MODULES)
def test_import(name):
    importlib.import_module(name)


def test_ui_imports():
    pytest.importorskip("tkinter")
    pytest.importorskip("customtkinter")
    for m in ["src.ui.sidebar", "src.ui.chat_display", "src.ui.main_window", "src.main"]:
        importlib.import_module(m)


def test_system_monitor_sample():
    from src.services.system_monitor import SystemMonitor
    cpu, ram = SystemMonitor().sample()
    assert 0 <= cpu <= 100 and 0 <= ram <= 100
