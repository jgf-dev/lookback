"""Tests for app/services/ai_clients.py – AIClients class."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from app.services.ai_clients import AIClients


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_clients(openai_key: str = '', gemini_key: str = '') -> AIClients:
    """Build an AIClients instance with controlled settings, patching external calls."""
    with patch('app.services.ai_clients.settings') as mock_settings, \
         patch('app.services.ai_clients.genai') as mock_genai, \
         patch('app.services.ai_clients.OpenAI') as mock_openai_cls:

        mock_settings.openai_api_key = openai_key
        mock_settings.gemini_api_key = gemini_key

        mock_openai_cls.return_value = MagicMock()
        mock_genai.GenerativeModel.return_value = MagicMock()

        clients = AIClients.__new__(AIClients)
        clients.openai = mock_openai_cls.return_value if openai_key else None
        clients.gemini = mock_genai.GenerativeModel.return_value if gemini_key else None
        return clients


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

class TestAIClientsInit:
    def test_no_keys_both_clients_none(self):
        with patch('app.services.ai_clients.settings') as s, \
             patch('app.services.ai_clients.OpenAI'), \
             patch('app.services.ai_clients.genai'):
            s.openai_api_key = ''
            s.gemini_api_key = ''
            clients = AIClients()
        assert clients.openai is None
        assert clients.gemini is None

    def test_openai_key_creates_openai_client(self):
        with patch('app.services.ai_clients.settings') as s, \
             patch('app.services.ai_clients.OpenAI') as mock_cls, \
             patch('app.services.ai_clients.genai'):
            s.openai_api_key = 'sk-test'
            s.gemini_api_key = ''
            mock_cls.return_value = MagicMock()
            clients = AIClients()
        assert clients.openai is not None
        assert clients.gemini is None

    def test_gemini_key_creates_gemini_model(self):
        with patch('app.services.ai_clients.settings') as s, \
             patch('app.services.ai_clients.OpenAI'), \
             patch('app.services.ai_clients.genai') as mock_genai:
            s.openai_api_key = ''
            s.gemini_key = 'gemini-key'
            s.gemini_api_key = 'gemini-key'
            mock_genai.GenerativeModel.return_value = MagicMock()
            clients = AIClients()
        assert clients.gemini is not None


# ---------------------------------------------------------------------------
# transcribe_audio
# ---------------------------------------------------------------------------

class TestTranscribeAudio:
    def test_no_openai_returns_fallback_message(self):
        clients = make_clients()
        result = clients.transcribe_audio(b'audio data')
        assert 'transcription unavailable' in result.lower()
        assert 'OPENAI_API_KEY' in result

    def test_with_openai_calls_transcription_api(self):
        clients = make_clients(openai_key='sk-test')
        mock_result = MagicMock()
        mock_result.text = 'hello world'
        clients.openai.audio.transcriptions.create.return_value = mock_result

        result = clients.transcribe_audio(b'audio data')
        assert result == 'hello world'
        clients.openai.audio.transcriptions.create.assert_called_once()

    def test_with_openai_passes_correct_model(self):
        clients = make_clients(openai_key='sk-test')
        mock_result = MagicMock()
        mock_result.text = 'transcribed'
        clients.openai.audio.transcriptions.create.return_value = mock_result

        clients.transcribe_audio(b'bytes')
        call_kwargs = clients.openai.audio.transcriptions.create.call_args
        assert call_kwargs.kwargs.get('model') == 'gpt-4o-mini-transcribe' or \
               call_kwargs[1].get('model') == 'gpt-4o-mini-transcribe'

    def test_with_openai_wraps_bytes_in_tuple(self):
        clients = make_clients(openai_key='sk-test')
        mock_result = MagicMock()
        mock_result.text = 'ok'
        clients.openai.audio.transcriptions.create.return_value = mock_result

        audio_bytes = b'\x00\x01\x02'
        clients.transcribe_audio(audio_bytes)
        call_kwargs = clients.openai.audio.transcriptions.create.call_args
        file_arg = call_kwargs.kwargs.get('file') or call_kwargs[1].get('file')
        assert isinstance(file_arg, tuple)
        assert file_arg[1] == audio_bytes


# ---------------------------------------------------------------------------
# deep_search
# ---------------------------------------------------------------------------

class TestDeepSearch:
    def test_no_clients_returns_provider_none(self):
        clients = make_clients()
        result = clients.deep_search('some text')
        assert result['provider'] == 'none'

    def test_no_clients_returns_empty_facts(self):
        clients = make_clients()
        result = clients.deep_search('some text')
        content = json.loads(result['content'])
        assert content['facts'] == []
        assert content['useful_links'] == []
        assert content['follow_ups'] == []

    def test_gemini_preferred_over_openai(self):
        clients = make_clients(openai_key='sk-test', gemini_key='g-key')
        mock_response = MagicMock()
        mock_response.text = '{"facts": ["f1"]}'
        clients.gemini.generate_content.return_value = mock_response

        result = clients.deep_search('test input')
        assert result['provider'] == 'gemini'
        clients.gemini.generate_content.assert_called_once()

    def test_openai_used_when_no_gemini(self):
        clients = make_clients(openai_key='sk-test')
        mock_response = MagicMock()
        mock_response.output_text = '{"facts": []}'
        clients.openai.responses.create.return_value = mock_response

        result = clients.deep_search('test input')
        assert result['provider'] == 'openai'

    def test_gemini_prompt_includes_input_text(self):
        clients = make_clients(gemini_key='g-key')
        clients.gemini.generate_content.return_value = MagicMock(text='{}')

        clients.deep_search('unique test phrase 12345')
        call_args = clients.gemini.generate_content.call_args
        prompt_arg = call_args[0][0] if call_args[0] else call_args[1].get('prompt', '')
        assert 'unique test phrase 12345' in prompt_arg

    def test_result_contains_content_key(self):
        clients = make_clients()
        result = clients.deep_search('anything')
        assert 'content' in result


# ---------------------------------------------------------------------------
# analyze_screenshot
# ---------------------------------------------------------------------------

class TestAnalyzeScreenshot:
    def test_no_openai_returns_fallback(self):
        clients = make_clients()
        result = clients.analyze_screenshot('base64data')
        assert 'unavailable' in result.lower()

    def test_with_openai_calls_responses_create(self):
        clients = make_clients(openai_key='sk-test')
        mock_response = MagicMock()
        mock_response.output_text = 'Found 3 anomalies.'
        clients.openai.responses.create.return_value = mock_response

        result = clients.analyze_screenshot('imgdata', context='testing')
        assert result == 'Found 3 anomalies.'
        clients.openai.responses.create.assert_called_once()

    def test_context_included_in_prompt(self):
        clients = make_clients(openai_key='sk-test')
        mock_response = MagicMock()
        mock_response.output_text = 'analysis'
        clients.openai.responses.create.return_value = mock_response

        clients.analyze_screenshot('img', context='special context XYZ')
        call_args = clients.openai.responses.create.call_args
        # input list is passed as kwarg
        input_payload = call_args.kwargs.get('input') or call_args[1].get('input')
        payload_str = str(input_payload)
        assert 'special context XYZ' in payload_str

    def test_image_b64_included_in_request(self):
        clients = make_clients(openai_key='sk-test')
        mock_response = MagicMock()
        mock_response.output_text = 'ok'
        clients.openai.responses.create.return_value = mock_response

        clients.analyze_screenshot('MY_IMAGE_B64_DATA')
        call_args = clients.openai.responses.create.call_args
        input_payload = call_args.kwargs.get('input') or call_args[1].get('input')
        payload_str = str(input_payload)
        assert 'MY_IMAGE_B64_DATA' in payload_str

    def test_default_context_empty_string(self):
        clients = make_clients(openai_key='sk-test')
        mock_response = MagicMock()
        mock_response.output_text = 'result'
        clients.openai.responses.create.return_value = mock_response

        # Should not raise when context omitted
        result = clients.analyze_screenshot('imgdata')
        assert result == 'result'


# ---------------------------------------------------------------------------
# make_visual_graph
# ---------------------------------------------------------------------------

class TestMakeVisualGraph:
    def test_returns_queued_message(self):
        clients = make_clients()
        result = clients.make_visual_graph('Alice knows Bob')
        assert 'Nano Banana' in result
        assert 'Alice knows Bob' in result

    def test_truncates_long_input_to_120_chars(self):
        long_text = 'x' * 200
        clients = make_clients()
        result = clients.make_visual_graph(long_text)
        # The embedded portion should be at most 120 chars
        prefix = 'Nano Banana job queued for: '
        embedded = result[len(prefix):]
        assert len(embedded) == 120

    def test_short_input_not_truncated(self):
        clients = make_clients()
        short = 'short'
        result = clients.make_visual_graph(short)
        assert short in result

    def test_returns_string(self):
        clients = make_clients()
        assert isinstance(clients.make_visual_graph('anything'), str)