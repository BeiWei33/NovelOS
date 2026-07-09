"""Tests for provider configuration loading."""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest

from core.types import ProviderConfig, ExecutionProfile
from skills.providers import (
    ProviderRouter,
    OpenAIAdapter,
    _load_yaml_providers,
    _load_env_providers,
    _resolve_env_ref,
)


class TestYamlProviders:
    def test_load_missing_file(self):
        result = _load_yaml_providers("/nonexistent/path/providers.yaml")
        assert result == {}

    def test_load_valid_yaml(self):
        yaml_content = """
providers:
  test-provider:
    base_url: https://api.example.com/v1
    api_key: sk-test
    default_model: test-model
    default_max_tokens: 4096
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            fpath = f.name
            f.write(yaml_content)
            f.flush()
            result = _load_yaml_providers(fpath)

        os.unlink(fpath)

        assert "test-provider" in result
        cfg = result["test-provider"]
        assert cfg.api_key == "sk-test"
        assert cfg.base_url == "https://api.example.com/v1"
        assert cfg.default_model == "test-model"
        assert cfg.default_max_tokens == 4096

    def test_load_with_env_ref(self, monkeypatch):
        monkeypatch.setenv("MY_API_KEY", "sk-from-env")
        yaml_content = """
providers:
  env-provider:
    base_url: https://api.example.com/v1
    api_key: ${MY_API_KEY}
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            fpath = f.name
            f.write(yaml_content)
            f.flush()
            result = _load_yaml_providers(fpath)

        os.unlink(fpath)

        assert result["env-provider"].api_key == "sk-from-env"

    def test_missing_base_url_raises(self):
        yaml_content = """
providers:
  bad-provider:
    api_key: sk-test
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            fpath = f.name
            f.write(yaml_content)
            f.flush()
            with pytest.raises(ValueError, match="base_url is required"):
                _load_yaml_providers(fpath)

        os.unlink(fpath)


class TestEnvProviders:
    def test_load_from_env(self, monkeypatch):
        monkeypatch.setenv("PROVIDER_OLLAMA_BASE_URL", "http://localhost:11434/v1")
        monkeypatch.setenv("PROVIDER_OLLAMA_API_KEY", "ollama")
        monkeypatch.setenv("PROVIDER_OLLAMA_DEFAULT_MODEL", "llama3")

        result = _load_env_providers()
        assert "ollama" in result
        cfg = result["ollama"]
        assert cfg.base_url == "http://localhost:11434/v1"
        assert cfg.api_key == "ollama"
        assert cfg.default_model == "llama3"

    def test_no_providers_without_base_url(self, monkeypatch):
        monkeypatch.setenv("PROVIDER_OLLAMA_API_KEY", "test")
        result = _load_env_providers()
        assert "ollama" not in result


class TestResolveEnvRef:
    def test_resolve_simple(self, monkeypatch):
        monkeypatch.setenv("TEST_KEY", "resolved-value")
        result = _resolve_env_ref("${TEST_KEY}")
        assert result == "resolved-value"

    def test_resolve_missing_unchanged(self):
        result = _resolve_env_ref("${NONEXISTENT_KEY}")
        assert result == "${NONEXISTENT_KEY}"

    def test_no_ref_unchanged(self):
        result = _resolve_env_ref("plain-string")
        assert result == "plain-string"


class TestIntegration:
    def test_yaml_and_env_registered(self, monkeypatch):
        router = ProviderRouter()
        yaml_content = """
providers:
  yaml-provider:
    base_url: https://yaml.example.com/v1
    api_key: yaml-key
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            fpath = f.name
            f.write(yaml_content)
            f.flush()
            yaml_providers = _load_yaml_providers(fpath)

        os.unlink(fpath)

        for name, cfg in yaml_providers.items():
            router.register(name, OpenAIAdapter, cfg)

        monkeypatch.setenv("PROVIDER_ENV_PROVIDER_BASE_URL", "https://env.example.com/v1")
        monkeypatch.setenv("PROVIDER_ENV_PROVIDER_API_KEY", "env-key")
        env_providers = _load_env_providers()
        for name, cfg in env_providers.items():
            router.register(name, OpenAIAdapter, cfg)

        providers = router.list_providers()
        assert "yaml-provider" in providers
        assert "env_provider" in providers  # underscores from PROVIDER_ENV_PROVIDER