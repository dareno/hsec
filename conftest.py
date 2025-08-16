import pytest

def pytest_addoption(parser):
    parser.addoption(
        "--run-hardware", action="store_true", default=False, help="run hardware integration tests"
    )

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "hardware: mark test as requiring hardware to run"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )

@pytest.fixture(autouse=True)
def _show_output_for_manual_tests(request):
    """Disable pytest output capturing for tests marked 'manual'.

    This ensures operator prompts (print/log) appear live when running
    multiple manual tests as a group.
    """
    manual = request.node.get_closest_marker("manual") is not None
    if not manual:
        # Normal behavior for non-manual tests
        yield
        return

    capman = request.config.pluginmanager.getplugin("capturemanager")
    if capman is not None:
        # Disable global capture so output streams go straight to the console
        capman.suspend_global_capture(in_=True)
    try:
        yield
    finally:
        if capman is not None:
            capman.resume_global_capture()
