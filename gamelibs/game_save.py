from typing import Any

from gamelibs import interfaces, hardware


class GameSave(interfaces.GameSave):
    def __init__(self) -> None:
        self.data: dict[str, Any] = {}
        self.tmp_data: dict[str, Any] = {}
        self.loaded_path: str

    def __getattr__(self, attr: str) -> Any:
        if attr in {"data", "game"} or attr[:2] == attr[-2:] == "__":
            return super().__getattribute__(attr)
        return self.data[attr]

    def __setattr__(self, name: str, value: Any) -> None:
        if name in {"data", "game"}:
            return super().__setattr__(name, value)
        self.data[name] = value

    def get_state(self, key: str) -> Any:
        return self.data[key]

    def set_state(self, key: str, value: Any) -> None:
        self.data[key] = value

    def get_tmp(self, key: str) -> Any:
        return self.tmp_data[key]

    def set_tmp(self, key: str, value: Any) -> None:
        self.tmp_data[key] = value

    def load(self, path: interfaces.FileID) -> None:
        self.data = hardware.loader.get_save(path)
        self.loaded_path = path

    def save(self, path: interfaces.FileID | None = None) -> None:
        if path is None:
            path = self.loaded_path
        old_health: int = self.health
        self.health: int = self.health_capacity
        hardware.loader.save_data(path, self.data)
        self.health = old_health

    def delete(self, path: interfaces.FileID | None = None) -> None:
        if path is None:
            path = self.loaded_path
        hardware.loader.delete_save(path)
