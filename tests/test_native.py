import json
from pathlib import Path
import subprocess
import sys
import unittest
from fifine_a8_control.control import SERVER

@unittest.skipUnless(sys.platform == 'win32', 'Windows Core Audio integration')
class NativeBridgeTests(unittest.TestCase):
    def test_native_bridge_compiles_and_enumerates_without_writing_audio(self):
        result = subprocess.run(
            ['powershell.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
             '-File', str(SERVER), '-ListOnly'],
            capture_output=True, text=True, encoding='utf-8', timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload['ok'], payload)
        self.assertEqual(payload['count'], len(payload['devices']))

if __name__ == '__main__':
    unittest.main()
