"""
Pytest Configuration
Fixtures and test setup
"""
import pytest
import asyncio
from typing import Generator


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_settings():
    """Mock application settings"""
    from core.config import Settings
    
    return Settings(
        openai={"api_key": "test-key"},
        storage={"working_dir": "./test_storage"}
    )