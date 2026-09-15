import unittest
import warnings
from types import SimpleNamespace

from FlooAudioOutputSwitcher import FlooAudioOutputSwitcher, PycawAudioBackend


class FakeDevice:
    def __init__(self, device_id, name, properties=None):
        self.id = device_id
        self.FriendlyName = name
        self.properties = properties or {}


class FakeBackend:
    def __init__(self, default_device, devices):
        self.default_device = default_device
        self.devices = devices
        self.switches = []
        self.failed_device_ids = set()

    def get_default_output(self):
        return self.default_device

    def get_active_outputs(self):
        return self.devices

    def set_default_output(self, device_id):
        if device_id in self.failed_device_ids:
            raise OSError("device is temporarily unavailable")
        self.switches.append(device_id)
        self.default_device = next(
            device for device in self.devices if device.id == device_id
        )


class FlooAudioOutputSwitcherTests(unittest.TestCase):
    def setUp(self):
        self.speakers = FakeDevice("speakers", "Realtek Speakers")
        self.floogoo = FakeDevice("floogoo", "Speakers (FMA120)")
        self.backend = FakeBackend(
            self.speakers,
            [self.speakers, self.floogoo],
        )
        self.errors = []
        self.restore_states = []
        self.switcher = self._create_switcher()

    def _create_switcher(self, restore_state=None):
        return FlooAudioOutputSwitcher(
            enabled=True,
            backend=self.backend,
            error_callback=self.errors.append,
            restore_state=restore_state,
            restore_state_callback=self.restore_states.append,
            system_name="Windows",
        )

    def test_connect_switches_and_idle_restores(self):
        self.switcher.handle_source_state(4)
        self.switcher.handle_source_state(6)
        self.switcher.handle_source_state(8)

        self.assertEqual(["floogoo"], self.backend.switches)

        self.switcher.handle_source_state(1)

        self.assertEqual(["floogoo", "speakers"], self.backend.switches)
        self.assertEqual([], self.errors)
        self.assertIsNone(self.restore_states[-1])

    def test_restore_state_survives_app_restart(self):
        self.switcher.handle_source_state(4)
        saved_restore_state = self.restore_states[-1]

        restarted_switcher = self._create_switcher(saved_restore_state)
        restarted_switcher.handle_source_state(4)
        restarted_switcher.handle_source_state(1)

        self.assertEqual(["floogoo", "speakers"], self.backend.switches)
        self.assertIsNone(self.restore_states[-1])

    def test_idle_on_startup_restores_saved_output(self):
        restore_state = {
            "previous_device_id": "speakers",
            "target_device_id": "floogoo",
        }
        self.backend.default_device = self.floogoo
        switcher = self._create_switcher(restore_state)

        switcher.handle_source_state(1)

        self.assertEqual(["speakers"], self.backend.switches)
        self.assertIsNone(self.restore_states[-1])

    def test_failed_connect_is_retried_on_next_active_state(self):
        self.backend.devices = [self.speakers]
        self.switcher.handle_source_state(4)
        self.backend.devices.append(self.floogoo)

        self.switcher.handle_source_state(5)

        self.assertEqual(["floogoo"], self.backend.switches)
        self.assertEqual(1, len(self.errors))

    def test_failed_restore_keeps_state_for_retry(self):
        self.switcher.handle_source_state(4)
        self.backend.failed_device_ids.add("speakers")

        self.switcher.handle_source_state(1)

        self.assertIsNotNone(self.restore_states[-1])
        self.backend.failed_device_ids.clear()
        self.switcher.handle_source_state(1)

        self.assertEqual(["floogoo", "speakers"], self.backend.switches)
        self.assertIsNone(self.restore_states[-1])

    def test_stopping_states_do_not_start_a_switch(self):
        self.switcher.handle_source_state(7)
        self.switcher.handle_source_state(11)

        self.assertEqual([], self.backend.switches)

    def test_repeated_active_states_switch_only_once(self):
        for state in (4, 5, 6, 9, 10):
            self.switcher.handle_source_state(state)

        self.assertEqual(["floogoo"], self.backend.switches)

    def test_manual_output_change_is_not_overridden_on_disconnect(self):
        other = FakeDevice("other", "Display Audio")
        self.backend.devices.append(other)
        self.switcher.handle_source_state(4)
        self.backend.default_device = other

        self.switcher.handle_source_state(1)

        self.assertEqual(["floogoo"], self.backend.switches)
        self.assertIsNone(self.restore_states[-1])

    def test_already_default_floogoo_is_not_changed_on_disconnect(self):
        self.backend.default_device = self.floogoo
        self.switcher.handle_source_state(4)
        self.switcher.handle_source_state(1)

        self.assertEqual([], self.backend.switches)
        self.assertEqual([], self.restore_states)

    def test_disabled_switcher_does_nothing(self):
        self.switcher.set_enabled(False)
        self.switcher.handle_source_state(4)

        self.assertEqual([], self.backend.switches)

    def test_disabling_after_switch_does_not_change_output_or_forget_restore(self):
        self.switcher.handle_source_state(4)
        saved_restore_state = self.restore_states[-1]

        self.switcher.set_enabled(False)
        self.switcher.handle_source_state(1)

        self.assertEqual(["floogoo"], self.backend.switches)
        self.assertEqual(saved_restore_state, self.restore_states[-1])

    def test_reenabling_while_idle_completes_pending_restore(self):
        self.switcher.handle_source_state(4)
        self.switcher.set_enabled(False)
        self.switcher.handle_source_state(1)

        self.switcher.set_enabled(True)
        self.switcher.handle_source_state(1)

        self.assertEqual(["floogoo", "speakers"], self.backend.switches)
        self.assertIsNone(self.restore_states[-1])

    def test_manual_change_while_disabled_cancels_pending_restore_on_reenable(self):
        other = FakeDevice("other", "Display Audio")
        self.backend.devices.append(other)
        self.switcher.handle_source_state(4)
        self.switcher.set_enabled(False)
        self.backend.default_device = other

        self.switcher.set_enabled(True)
        self.switcher.handle_source_state(1)

        self.assertEqual(["floogoo"], self.backend.switches)
        self.assertIsNone(self.restore_states[-1])

    def test_non_windows_switcher_does_nothing(self):
        switcher = FlooAudioOutputSwitcher(
            enabled=True,
            backend=self.backend,
            system_name="Linux",
        )
        switcher.handle_source_state(4)

        self.assertEqual([], self.backend.switches)

    def test_missing_floogoo_reports_active_device_names(self):
        self.backend.devices = [self.speakers]
        self.switcher.handle_source_state(4)

        self.assertEqual([], self.backend.switches)
        self.assertIn("no active FMA120/FlooGoo", self.errors[0])
        self.assertIn("Realtek Speakers", self.errors[0])

    def test_floogoo_device_property_is_recognized_after_display_name_change(self):
        self.floogoo.FriendlyName = "Headphones"
        self.floogoo.properties = {"interface_name": "FMA120 USB Audio"}

        self.switcher.handle_source_state(4)

        self.assertEqual(["floogoo"], self.backend.switches)

    def test_saved_target_id_is_recognized_after_display_name_change(self):
        self.floogoo.FriendlyName = "Headphones"
        restore_state = {
            "previous_device_id": "speakers",
            "target_device_id": "floogoo",
        }
        self.backend.default_device = self.floogoo
        switcher = self._create_switcher(restore_state)

        switcher.handle_source_state(4)
        switcher.handle_source_state(1)

        self.assertEqual(["speakers"], self.backend.switches)


class PycawAudioBackendTests(unittest.TestCase):
    def setUp(self):
        self.audio_utilities = SimpleNamespace()
        self.backend = object.__new__(PycawAudioBackend)
        self.backend._audio_utilities = self.audio_utilities
        self.backend._data_flow = SimpleNamespace(
            eRender=SimpleNamespace(value="render")
        )
        self.backend._device_state = SimpleNamespace(
            ACTIVE=SimpleNamespace(value="active")
        )
        self.console_role = SimpleNamespace(value="console")
        self.multimedia_role = SimpleNamespace(value="multimedia")
        self.backend._roles = SimpleNamespace(
            eConsole=self.console_role,
            eMultimedia=self.multimedia_role,
        )

    def test_enumerates_only_active_render_devices(self):
        calls = []

        def get_all_devices(**kwargs):
            calls.append(kwargs)
            return ["device"]

        self.audio_utilities.GetAllDevices = get_all_devices

        devices = self.backend.get_active_outputs()

        self.assertEqual(["device"], devices)
        self.assertEqual(
            [{"data_flow": "render", "device_state": "active"}],
            calls,
        )

    def test_sets_console_and_multimedia_roles_only(self):
        calls = []
        self.audio_utilities.SetDefaultDevice = (
            lambda device_id, roles: calls.append((device_id, roles))
        )

        self.backend.set_default_output("floogoo")

        self.assertEqual(
            [("floogoo", [self.console_role, self.multimedia_role])],
            calls,
        )

    def test_suppresses_only_known_pycaw_property_warning(self):
        def get_all_devices(**kwargs):
            warnings.warn(
                "COMError attempting to get property 3 from device 'FMA120'",
                UserWarning,
            )
            warnings.warn("unexpected warning", UserWarning)
            return []

        self.audio_utilities.GetAllDevices = get_all_devices

        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            self.backend.get_active_outputs()

        self.assertEqual(["unexpected warning"], [str(item.message) for item in captured])


if __name__ == "__main__":
    unittest.main()
