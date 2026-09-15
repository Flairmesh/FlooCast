from __future__ import annotations

import logging
import platform
import warnings
from typing import Callable, Dict, Iterable, Mapping, Optional


logger = logging.getLogger(__name__)


class PycawAudioBackend:
    """Expose the small subset of pycaw used by FlooCast."""

    def __init__(self):
        from pycaw.constants import DEVICE_STATE, EDataFlow, ERole
        from pycaw.pycaw import AudioUtilities

        self._device_state = DEVICE_STATE
        self._data_flow = EDataFlow
        self._roles = ERole
        self._audio_utilities = AudioUtilities

    def get_default_output(self):
        return self._audio_utilities.GetSpeakers()

    def get_active_outputs(self):
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message=r"COMError attempting to get property .*",
                category=UserWarning,
            )
            return self._audio_utilities.GetAllDevices(
                data_flow=self._data_flow.eRender.value,
                device_state=self._device_state.ACTIVE.value,
            )

    def set_default_output(self, device_id: str) -> None:
        self._audio_utilities.SetDefaultDevice(
            device_id,
            roles=[self._roles.eConsole, self._roles.eMultimedia],
        )


class FlooAudioOutputSwitcher:
    """Switch the Windows output in response to FlooGoo source-state changes."""

    IDLE_STATE = 1
    ACTIVE_STATES = frozenset((4, 5, 6, 9, 10))
    TARGET_NAME_PARTS = ("fma120", "floogoo")
    PREVIOUS_DEVICE_KEY = "previous_device_id"
    TARGET_DEVICE_KEY = "target_device_id"

    def __init__(
        self,
        enabled: bool = False,
        backend=None,
        error_callback: Optional[Callable[[str], None]] = None,
        restore_state: Optional[Mapping[str, str]] = None,
        restore_state_callback: Optional[
            Callable[[Optional[Dict[str, str]]], None]
        ] = None,
        system_name: Optional[str] = None,
    ):
        self.enabled = enabled
        self._backend = backend
        self._error_callback = error_callback
        self._restore_state_callback = restore_state_callback
        self._is_windows = (system_name or platform.system()).lower().startswith("win")
        self._connection_handled = False
        self._previous_device_id = None
        self._target_device_id = None
        self._load_restore_state(restore_state)

    @property
    def supported(self) -> bool:
        return self._is_windows

    def set_enabled(self, enabled: bool) -> None:
        """Enable future switching without changing the current Windows output."""
        self.enabled = enabled
        if not enabled:
            self._connection_handled = False

    def handle_source_state(self, state: Optional[int]) -> None:
        if not self.enabled or not self.supported or state is None:
            return

        if state in self.ACTIVE_STATES:
            if not self._connection_handled:
                self._connection_handled = self._switch_to_floogoo()
        elif state == self.IDLE_STATE:
            self._connection_handled = False
            if self._has_restore_state():
                self._restore_previous_output()

    def _get_backend(self):
        if self._backend is None:
            try:
                self._backend = PycawAudioBackend()
            except Exception as exc:
                raise RuntimeError(
                    "pycaw is unavailable; install the Windows requirements and "
                    "restart FlooCast"
                ) from exc
        return self._backend

    def _switch_to_floogoo(self) -> bool:
        try:
            backend = self._get_backend()
            current = backend.get_default_output()
            active_outputs = backend.get_active_outputs()
            target = self._find_target(active_outputs, self._target_device_id)
            if target is None:
                active_names = ", ".join(
                    device.FriendlyName or "<unnamed>" for device in active_outputs
                )
                raise RuntimeError(
                    "no active FMA120/FlooGoo audio output was found; active outputs: "
                    + (active_names or "none")
                )

            if current is not None and current.id == target.id:
                if (
                    self._previous_device_id is not None
                    and self._target_device_id != target.id
                ):
                    self._store_restore_state(self._previous_device_id, target.id)
                return True

            previous_device_id = current.id if current is not None else None
            if previous_device_id is not None:
                # Persist before changing Windows so an app exit cannot lose the
                # endpoint that needs to be restored.
                self._store_restore_state(previous_device_id, target.id)

            backend.set_default_output(target.id)
            return True
        except Exception as exc:
            self._report_error(str(exc))
            return False

    def _restore_previous_output(self) -> None:
        try:
            backend = self._get_backend()
            current = backend.get_default_output()
            if current is not None and current.id != self._target_device_id:
                # The user selected another output while the headset was connected.
                self._clear_restore_state()
                return

            backend.set_default_output(self._previous_device_id)
            self._clear_restore_state()
        except Exception as exc:
            # Keep the restore state so a later Idle notification or app restart can
            # retry if the previous endpoint was temporarily unavailable.
            self._report_error(str(exc))

    @classmethod
    def _find_target(cls, devices: Iterable, preferred_device_id=None):
        devices = list(devices)
        if preferred_device_id is not None:
            for device in devices:
                if device.id == preferred_device_id:
                    return device

        for device in devices:
            if cls._is_floogoo_output(device):
                return device
        return None

    @classmethod
    def _is_floogoo_output(cls, device) -> bool:
        searchable_values = [device.id, device.FriendlyName]
        properties = getattr(device, "properties", None)
        if isinstance(properties, Mapping):
            searchable_values.extend(properties.values())

        search_text = " ".join(
            str(value).casefold() for value in searchable_values if value is not None
        )
        return any(part in search_text for part in cls.TARGET_NAME_PARTS)

    def _load_restore_state(self, restore_state: Optional[Mapping[str, str]]) -> None:
        if not isinstance(restore_state, Mapping):
            return

        previous_device_id = restore_state.get(self.PREVIOUS_DEVICE_KEY)
        target_device_id = restore_state.get(self.TARGET_DEVICE_KEY)
        if (
            isinstance(previous_device_id, str)
            and isinstance(target_device_id, str)
            and previous_device_id
            and target_device_id
            and previous_device_id != target_device_id
        ):
            self._previous_device_id = previous_device_id
            self._target_device_id = target_device_id

    def _has_restore_state(self) -> bool:
        return (
            self._previous_device_id is not None
            and self._target_device_id is not None
        )

    def _store_restore_state(self, previous_device_id: str, target_device_id: str) -> None:
        restore_state = {
            self.PREVIOUS_DEVICE_KEY: previous_device_id,
            self.TARGET_DEVICE_KEY: target_device_id,
        }
        if self._restore_state_callback is not None:
            self._restore_state_callback(restore_state)
        self._previous_device_id = previous_device_id
        self._target_device_id = target_device_id

    def _clear_restore_state(self) -> None:
        if self._restore_state_callback is not None:
            self._restore_state_callback(None)
        self._previous_device_id = None
        self._target_device_id = None

    def _report_error(self, message: str) -> None:
        if self._error_callback is not None:
            self._error_callback(message)
        else:
            logger.error("Audio output switching failed: %s", message)
