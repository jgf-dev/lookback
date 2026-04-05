from __future__ import annotations

import json
from typing import Any

import google.generativeai as genai
from openai import OpenAI

from app.config import settings


class AIClients:
    def __init__(self) -> None:
        self.openai = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
            self.gemini = genai.GenerativeModel('gemini-1.5-pro')
        else:
            self.gemini = None

    def transcribe_audio(self, audio_bytes: bytes) -> str:
        if not self.openai:
            return '[No OPENAI_API_KEY configured] transcription unavailable.'
        result = self.openai.audio.transcriptions.create(model='gpt-4o-mini-transcribe', file=('audio.wav', audio_bytes))
        return result.text

    def deep_search(self, text: str) -> dict[str, Any]:
        prompt = (
            'Return concise JSON with keys: facts, useful_links, follow_ups. '
            'Enrich the user note with relevant contextual knowledge. '
            f'Input: {text}'
        )
        if self.gemini:
            response = self.gemini.generate_content(prompt)
            return {'provider': 'gemini', 'content': response.text}
        if self.openai:
            response = self.openai.responses.create(model='gpt-4.1-mini', input=prompt)
            return {'provider': 'openai', 'content': response.output_text}
        return {'provider': 'none', 'content': json.dumps({'facts': [], 'useful_links': [], 'follow_ups': []})}

    def analyze_screenshot(self, image_b64: str, context: str = '') -> str:
        prompt = (
            'Analyze this screenshot and list insights, anomalies, or missed opportunities. '
            f'Context: {context}'
        )
        if self.openai:
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
        return 'Screenshot analysis unavailable without API key.'

    def make_visual_graph(self, relationship_text: str) -> str:
        # Placeholder for Nano Banana pipeline.
        return f'Nano Banana job queued for: {relationship_text[:120]}'


ai_clients = AIClients()
