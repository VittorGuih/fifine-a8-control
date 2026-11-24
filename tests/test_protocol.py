import unittest
from fifine_a8_control.protocol import BUTTON_REPORT, consumer_interfaces, is_button_report
from fifine_a8_control.control import ControlClient

class ProtocolTests(unittest.TestCase):
    def test_identical_press_reports_are_independent_events(self):
        reports = [BUTTON_REPORT, BUTTON_REPORT, BUTTON_REPORT]
        self.assertEqual(sum(is_button_report(r) for r in reports), 3)

    def test_consumer_mute_is_not_the_vendor_button_event(self):
        consumer_mute = bytearray(BUTTON_REPORT)
        consumer_mute[1] = 0x40
        self.assertFalse(is_button_report(consumer_mute))

    def test_truncated_or_unrecognized_reports_are_ignored(self):
        self.assertFalse(is_button_report([]))
        self.assertFalse(is_button_report(BUTTON_REPORT[:-1]))
        self.assertFalse(is_button_report(BUTTON_REPORT + b'\0'))
        self.assertFalse(is_button_report(b'\x02\x01'))

    def test_other_models_and_other_collections_are_not_selected(self):
        devices = [
            dict(vendor_id=0x3142, product_id=0xA010, usage_page=0xC, usage=1),
            dict(vendor_id=0x3142, product_id=0xA8, usage_page=0xB, usage=5),
            dict(vendor_id=0x1234, product_id=0xA8, usage_page=0xC, usage=1),
            dict(vendor_id=0x3142, product_id=0xA8, usage_page=0xC, usage=1),
        ]
        self.assertEqual(consumer_interfaces(devices), [devices[-1]])

    def test_unsupported_output_commands_are_rejected_before_io(self):
        client = ControlClient()
        with self.assertRaises(ValueError):
            client.request('firmware-update')
        self.assertIsNone(client.process)

if __name__ == '__main__':
    unittest.main()
