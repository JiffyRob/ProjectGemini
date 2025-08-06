import pygame
from gamelibs import interfaces
from dataclasses import dataclass

pygame.mixer.init()


@dataclass
class UsedChannel:
    priority: int
    channel: pygame.mixer.Channel


class ChannelRack:
    def __init__(self, channels: int, start_index: int = 0) -> None:
        self._free_channels = [
            pygame.mixer.Channel(i + start_index) for i in range(channels)
        ]
        self._free_channels: list[pygame.mixer.Channel] = []
        self._used_channels: list[UsedChannel] = []

    def _get_least_priority(self) -> UsedChannel:
        return sorted(self._used_channels, key=lambda x: x.priority)[0]

    def allocate_channel(self, priority: int) -> pygame.mixer.Channel | None:
        self.free_done()
        if self._free_channels:
            channel = self._free_channels.pop(-1)
            self._used_channels.append(UsedChannel(priority, channel))
            return channel
        else:
            used_channel = self._get_least_priority()
            if used_channel.priority < priority:
                used_channel.channel.stop()
                used_channel.priority = priority
                return used_channel.channel

    def free_done(self) -> None:
        to_free: list[UsedChannel] = []
        for channel_data in self._used_channels:
            if not channel_data.channel.get_busy():
                to_free.append(channel_data)
        for channel_data in to_free:
            self._used_channels.remove(channel_data)
            self._free_channels.append(channel_data.channel)


class SoundManager:
    def __init__(self, loader: interfaces.Loader, channels: int = 8) -> None:
        self._channel_rack = ChannelRack(channels)
        self.loader = loader
        self.current_track: str | None = None
        self.sound_volume = 1
        self.music_volume = 1

    def play_sound(
        self,
        path: interfaces.FileID,
        priority: int = 10,
        loops: int = 0,
        volume: float = 1,
        fade_ms: int = 0,
        polar_location: tuple[int, int] = (0, 0),
    ) -> bool:
        sound = self.loader.get_sound(path)
        channel = self._channel_rack.allocate_channel(priority)
        if channel is not None:  # if all channels are in use and of higher priority
            channel.set_source_location(*polar_location)
            channel.set_volume(volume * self.sound_volume)
            channel.play(sound, loops, 0, fade_ms)
        return channel is not None

    def set_sound_volume(self, value: float) -> None:
        self.sound_volume = pygame.math.clamp(value, 0.0, 1.0)  # type: ignore

    def get_sound_value(self) -> float:
        return self.sound_volume

    def set_music_volume(self, value: float) -> None:
        self.music_volume = pygame.math.clamp(value, 0.0, 1.0)  # type: ignore

    def get_music_volume(self) -> float:
        return self.music_volume

    def switch_track(
        self,
        track: interfaces.FileID | None = None,
        volume: float = 1,
        loops: int = -1,
        start: float = 0.0,
        fade_ms: int = 0,
    ) -> None:
        if track is None:
            return
        path = self.loader.join(track)
        if track != self.current_track:
            pygame.mixer.music.set_volume(self.music_volume * volume)
            pygame.mixer.music.stop()
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(loops, start, fade_ms)
            self.current_track = str(path)
        else:
            pass

    def stop_track(self) -> None:
        pygame.mixer.music.stop()
        self.current_track = None
