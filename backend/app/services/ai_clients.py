from __future__ import annotations

import json
import logging
from typing import Any

import google.generativeai as genai
from openai import OpenAI

from app.config import get_settings

logger = logging.getLogger(__name__)


class AIClients:
    def __init__(self) -> None:
        """
        Initialize AIClients and configure provider clients based on runtime API keys.

        Sets self.openai to an OpenAI client when settings.openai_api_key is present, otherwise None. If settings.gemini_api_key is present, configures and sets self.gemini to a Gemini generative model instance, otherwise sets self.gemini to None.

        Attributes:
            self.openai: OpenAI client instance or None.
            self.gemini: Gemini generative model instance or None.
        """
        settings = get_settings()
        self.openai = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
            self.gemini = genai.GenerativeModel('gemini-1.5-pro')
        else:
            self.gemini = None

    def transcribe_audio(self, audio_bytes: bytes) -> str:
        """
        Transcribes the provided audio bytes using the configured OpenAI transcription model.

        Parameters:
            audio_bytes (bytes): Raw audio file bytes (e.g., WAV or MP3) to be transcribed.

        Returns:
            str: The transcription text, or the message "[No OPENAI_API_KEY configured] transcription unavailable." if no OpenAI API key is configured.
        """
        if not self.openai:
            return '[No OPENAI_API_KEY configured] transcription unavailable.'
        try:
            result = self.openai.audio.transcriptions.create(model='gpt-4o-mini-transcribe', file=('audio.wav', audio_bytes))
            return result.text
        except Exception as e:
            logger.exception('transcribe_audio failed: %s', e)
            return '[transcription unavailable]'

    def deep_search(self, text: str) -> dict[str, Any]:
        """
        Generate a concise, JSON-formatted enrichment of the provided text containing facts, useful links, and follow-up questions.

        Parameters:
            text (str): User-provided note or excerpt to enrich and analyze.

        Returns:
            dict[str, Any]: A dictionary with keys:
                - 'provider': the configured provider used ('gemini', 'openai', or 'none').
                - 'content': the provider's response text, or a JSON string with empty
                  'facts', 'useful_links', and 'follow_ups' when no provider is available.
        """
        prompt = (
            'Return concise JSON with keys: facts, useful_links, follow_ups. '
            'Enrich the user note with relevant contextual knowledge. '
            f'Input: {text}'
        )
        if self.gemini:
            try:
                response = self.gemini.generate_content(prompt)
                return {'provider': 'gemini', 'content': response.text}
            except Exception as e:
                logger.exception('deep_search with Gemini failed: %s', e)
                return {'provider': 'gemini', 'content': json.dumps({'facts': [], 'useful_links': [], 'follow_ups': []})}
        if self.openai:
            try:
                response = self.openai.responses.create(model='gpt-4.1-mini', input=prompt)
                return {'provider': 'openai', 'content': response.output_text}
            except Exception as e:
                logger.exception('deep_search with OpenAI failed: %s', e)
                return {'provider': 'openai', 'content': json.dumps({'facts': [], 'useful_links': [], 'follow_ups': []})}
        return {'provider': 'none', 'content': json.dumps({'facts': [], 'useful_links': [], 'follow_ups': []})}

    def analyze_screenshot(self, image_b64: str, context: str = '') -> str:
        """
        Analyze a screenshot for insights, anomalies, and missed opportunities.

        Parameters:
            image_b64 (str): Base64-encoded image data (e.g., PNG or JPEG) of the screenshot.
            context (str): Optional contextual information to guide the analysis.

        Returns:
            str: The model-generated analysis text when an OpenAI client is configured, otherwise
            the literal string 'Screenshot analysis unavailable without API key.'.
        """
        prompt = (
            'Analyze this screenshot and list insights, anomalies, or missed opportunities. '
            f'Context: {context}'
        )
        if self.openai:
            try:
                response = self.openai.responses.create(
                    model='gpt-4.1-mini',
                    input=[
                        {
                            'role': 'user',
                            'content': [
                                {'type': 'input_text', 'text': prompt},
                                {'type': 'input_image', 'image_base64': image_b64},
                            ],
                        }
                    ],
                )
                return response.output_text
            except Exception as e:
                logger.exception('analyze_screenshot failed: %s', e)
                return 'Screenshot analysis unavailable.'
        return 'Screenshot analysis unavailable without API key.'

    def make_visual_graph(self, relationship_text: str) -> str:
        # Placeholder for Nano Banana pipeline.
        """
        Queue a visual graph generation job using the provided relationship description.
        
        Parameters:
            relationship_text (str): Natural-language description of relationships to visualize.
        
        Returns:
            str: A status message indicating a "Nano Banana" job was queued for the given relationship text (message includes up to the first 120 characters of the input).
        """
        return f'Nano Banana job queued for: {relationship_text[:120]}'


ai_clients = AIClients()