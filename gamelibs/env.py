import sys
import platform
import json
from typing import Any
from gamelibs import interfaces

PYGBAG = sys.platform == "emscripten"
HTML_WINDOW = None

settings = {}
saves = {}

if PYGBAG:
    HTML_WINDOW = platform.window  #type: ignore
    settings = json.loads(HTML_WINDOW.localStorage.getItem("settings") or "{}")
    saves = json.loads(HTML_WINDOW.localStorage.getItem("saves") or "{}")


def get_settings() -> dict[str, Any]:
    return settings


def update_save(path: interfaces.FileID, data: dict[str, Any]):
    global saves

    print("SAVING")

    saves[str(path)] = json.dumps(data)


def delete_save(path):
    global saves

    saves.pop(str(path))


def get_save(path):
    return json.loads(saves[str(path)])


def update_settings(updated_settings):
    global settings

    settings = {**settings, **updated_settings}


def write_settings():
    if not PYGBAG:
        return
    HTML_WINDOW.localStorage.setItem("settings", json.dumps(settings))


def write_saves():
    if not PYGBAG:
        return
    HTML_WINDOW.localStorage.setItem("saves", json.dumps(saves))
