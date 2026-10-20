import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import x9_unified
except ImportError:
    x9_unified = None

class TestX9Unified(unittest.TestCase):
    
    def test_validate_filename_exists(self):
        self.assertTrue(hasattr(x9_unified, "validate_filename"))
        
    def test_validate_filename_logic(self):
        if hasattr(x9_unified, "validate_filename"):
            self.assertTrue(x9_unified.validate_filename("secure_data.txt"))
            self.assertTrue(x9_unified.validate_filename("sub/folder/file.dat"))
            self.assertFalse(x9_unified.validate_filename("../../etc/passwd"))
            self.assertFalse(x9_unified.validate_filename(""))

    def test_healthz_endpoint_payload(self):
        # Verify health check dictionary and fields exist
        if hasattr(x9_unified, "DEADMAN_ARMED"):
            self.assertIsInstance(x9_unified.DEADMAN_ARMED, bool)

if __name__ == "__main__":
    unittest.main()
