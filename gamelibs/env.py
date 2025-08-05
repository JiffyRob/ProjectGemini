import sys
import platform
import json
from typing import Any
from gamelibs import interfaces

PYGBAG = sys.platform == "emscripten"
HTML_WINDOW = None

settings: dict[str, Any] = {}
saves = {}

if PYGBAG:
    HTML_WINDOW = platform.window  #type: ignore
    settings = json.loads(HTML_WINDOW.localStorage.getItem("settings") or "{}")  # type: ignore
    saves = json.loads(HTML_WINDOW.localStorage.getItem("saves") or "{}")  # type: ignore


def get_settings() -> dict[str, Any]:
    return settings


def update_save(path: interfaces.FileID, data: dict[str, Any]) -> None:
    global saves

    print("SAVING")

    saves[str(path)] = json.dumps(data)


def delete_save(path: interfaces.FileID) -> None:
    global saves

    saves.pop(str(path))  # type: ignore


def get_save(path: interfaces.FileID) -> dict[str, Any]:
    return json.loads(saves[str(path)])  # type: ignore


def update_settings(updated_settings: dict[str, Any]) -> None:
    global settings

    settings = {**settings, **updated_settings}


def write_settings() -> None:
    if not PYGBAG:
        return
    HTML_WINDOW.localStorage.setItem("settings", json.dumps(settings))  # type: ignore


def write_saves() -> None:
    if not PYGBAG:
        return
    HTML_WINDOW.localStorage.setItem("saves", json.dumps(saves))  # type: ignore
