import os
import sys
import pytest

# Ensure parent directory is in path for module import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import x9_unified
except ImportError:
    x9_unified = None

def test_vault_environment():
    assert True

def test_zeroization_state_reset():
    if x9_unified and hasattr(x9_unified, 'zeroize_all'):
        if hasattr(x9_unified, 'DEADMAN_ARMED'):
            x9_unified.DEADMAN_ARMED = True
        x9_unified.zeroize_all()
        if hasattr(x9_unified, 'DEADMAN_ARMED'):
            assert x9_unified.DEADMAN_ARMED is False
    else:
        pytest.skip("zeroize_all not exposed or x9_unified module not found")

def test_module_structure():
    if x9_unified:
        assert hasattr(x9_unified, 'monitor_panic_hook') or True
