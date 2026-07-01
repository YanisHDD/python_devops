import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../api")))

from config import ConfigLoader, ConfigError


def test_config_loader_success(tmp_path):
    """Verify loading from a valid JSON config."""
    f = tmp_path / "servers.json"
    f.write_text('[{"name": "test", "host": "localhost", "port": 80, "tags": ["prod"], "health_path": "/status/200"}]')
    loader = ConfigLoader(str(f))
    servers = loader.load()
    assert len(servers) == 1
    assert servers[0].name == "test"
    assert servers[0].tags == ["prod"]
    assert servers[0].health_path == "/status/200"


def test_config_loader_file_not_found():
    """Verify raising ConfigError when file is missing."""
    loader = ConfigLoader("nonexistent_file.json")
    with pytest.raises(ConfigError):
        loader.load()


def test_config_loader_invalid_json(tmp_path):
    """Verify raising ConfigError on malformed JSON."""
    f = tmp_path / "servers.json"
    f.write_text("invalid json format")
    loader = ConfigLoader(str(f))
    with pytest.raises(ConfigError):
        loader.load()
