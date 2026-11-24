import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import queue
import unittest
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from fifine_a8_control import runtime
from fifine_a8_control.ui import App

class InterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        runtime.closing.clear()
        for q in (runtime.events, runtime.commands):
            while True:
                try: q.get_nowait()
                except queue.Empty: break
        self.window = App(demo=True)

    def tearDown(self):
        self.window.close()
        QTest.qWait(20)

    def apply(self, muted):
        self.window.choose(muted)
        QTest.qWait(230)
        self.window.tick()

    def test_demo_does_not_send_hardware_commands_and_marks_one_selection(self):
        self.apply(False)
        self.assertEqual(self.window.unmute.accessibleDescription(), 'Selected state')
        self.assertEqual(self.window.mute.accessibleDescription(), 'Apply this state')
        self.assertIn('Active', self.window.unmute.text())
        self.assertTrue(runtime.commands.empty())
        self.apply(True)
        self.assertEqual(self.window.mute.accessibleDescription(), 'Selected state')
        self.assertEqual(self.window.unmute.accessibleDescription(), 'Apply this state')
        self.assertTrue(runtime.commands.empty())

    def test_physical_press_clears_unconfirmed_selection(self):
        self.apply(False)
        runtime.events.put(('button', '12:00:00'))
        self.window.tick()
        self.assertIsNone(self.window.confirmed)
        self.assertEqual(self.window.mode, 'physical')
        self.assertEqual(self.window.unmute.accessibleDescription(), 'Apply this state')
        self.assertEqual(self.window.mute.accessibleDescription(), 'Apply this state')

    def test_keep_state_recovers_after_event_and_disconnect_disarms_it(self):
        self.apply(False)
        self.window.lock.setChecked(True)
        QTest.qWait(230)
        runtime.events.put(('button', '12:00:00'))
        self.window.tick()
        QTest.qWait(230)
        self.window.tick()
        self.assertFalse(self.window.confirmed)
        self.assertTrue(self.window.lock.isChecked())
        runtime.events.put(('device_error', 'Unplugged'))
        self.window.tick()
        self.assertFalse(self.window.lock.isChecked())
        self.assertIsNone(self.window.confirmed)
        self.assertFalse(self.window.unmute.isEnabled())

if __name__ == '__main__':
    unittest.main()
