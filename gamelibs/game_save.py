from typing import Any

from gamelibs import interfaces, hardware


class GameSave(interfaces.GameSave):
    def __init__(self) -> None:
        self.data: dict[str, Any] = {}
        self.tmp_data: dict[str, Any] = {}
        self._loaded_path: interfaces.FileID

    @property
    def loaded_path(self) -> interfaces.FileID:
        return self._loaded_path

    def get_state(self, key: str) -> Any:
        return self.data[key]

    def set_state(self, key: str, value: Any) -> None:
        self.data[key] = value

    def get_tmp(self, key: str) -> Any:
        return self.tmp_data[key]

    def set_tmp(self, key: str, value: Any) -> None:
        self.tmp_data[key] = value

    def new(self, path: interfaces.FileID) -> None:
        self.load("start1")
        self._loaded_path = path
        self.save()

    def load(self, path: interfaces.FileID) -> None:
        self.data = hardware.loader.get_save(path)
        self._loaded_path = path

    def save(self, path: interfaces.FileID | None = None) -> None:
        if path is None:
            path = self.loaded_path
        old_health: int = self.get_state("health")
        self.set_state("health", self.get_state("max_health"))
        hardware.loader.save_data(path, self.data)
        self.set_state("health", old_health)

    def delete(self, path: interfaces.FileID | None = None) -> None:
        if path is None:
            path = self.loaded_path
        hardware.loader.delete_save(path)
