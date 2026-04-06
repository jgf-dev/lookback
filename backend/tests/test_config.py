"""Tests for app/config.py – Settings class."""
from __future__ import annotations

import pytest
from pydantic import ValidationError


class TestSettings:
    def test_default_app_name(self):
        from app.config import Settings

        s = Settings()
        assert s.app_name == 'Lookback API'

    def test_default_database_url(self):
        from app.config import Settings

        s = Settings()
        assert s.database_url == 'sqlite:///./lookback.db'

    def test_default_api_keys_are_empty_strings(self):
        from app.config import Settings

        s = Settings()
        assert s.openai_api_key == ''
        assert s.gemini_api_key == ''

    def test_env_var_override_openai_key(self, monkeypatch):
        monkeypatch.setenv('OPENAI_API_KEY', 'sk-test-123')
        from importlib import reload
        import app.config as config_module

        # Rebuild the Settings object with the patched env
        s = config_module.Settings()
        assert s.openai_api_key == 'sk-test-123'

    def test_env_var_override_gemini_key(self, monkeypatch):
        monkeypatch.setenv('GEMINI_API_KEY', 'gemini-key-xyz')
        from app.config import Settings

        s = Settings()
        assert s.gemini_api_key == 'gemini-key-xyz'

    def test_env_var_override_database_url(self, monkeypatch):
        monkeypatch.setenv('DATABASE_URL', 'sqlite:///./test.db')
        from app.config import Settings

        s = Settings()
        assert s.database_url == 'sqlite:///./test.db'

    def test_settings_is_singleton_module_level(self):
        """The module-level `settings` object should be an instance of Settings."""
        from app.config import settings, Settings

        assert isinstance(settings, Settings)

    def test_app_name_is_string(self):
        from app.config import Settings

        s = Settings()
        assert isinstance(s.app_name, str)
        assert len(s.app_name) > 0