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
