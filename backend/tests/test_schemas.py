"""Tests for app/schemas.py – Pydantic request/response models."""
from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas import EntryIn, EntryOut, InsightOut, ScreenshotIn


class TestEntryIn:
    def test_minimal_valid_payload(self):
        e = EntryIn(source='manual', content='hello world')
        assert e.source == 'manual'
        assert e.content == 'hello world'

    def test_optional_fields_default_to_none(self):
        e = EntryIn(source='voice', content='test')
        assert e.project is None
        assert e.task is None
        assert e.context is None
        assert e.metadata is None

    def test_all_fields_populated(self):
        e = EntryIn(
            source='screenshot',
            content='observed a bug',
            project='ProjectX',
            task='debugging',
            context='CI environment',
            metadata={'key': 'value', 'count': 3},
        )
        assert e.project == 'ProjectX'
        assert e.task == 'debugging'
        assert e.context == 'CI environment'
        assert e.metadata == {'key': 'value', 'count': 3}

    def test_missing_required_source_raises(self):
        with pytest.raises(ValidationError):
            EntryIn(content='hello')

    def test_missing_required_content_raises(self):
        with pytest.raises(ValidationError):
            EntryIn(source='manual')

    def test_metadata_accepts_nested_dict(self):
        e = EntryIn(source='manual', content='x', metadata={'nested': {'a': 1}})
        assert e.metadata['nested']['a'] == 1

    def test_metadata_accepts_none_explicitly(self):
        e = EntryIn(source='manual', content='x', metadata=None)
        assert e.metadata is None

    def test_empty_content_is_accepted_by_schema(self):
        """Schema itself has no min-length constraint – content guard is in business logic."""
        e = EntryIn(source='manual', content='')
        assert e.content == ''


class TestScreenshotIn:
    def test_minimal_valid_payload(self):
        s = ScreenshotIn(image_b64='base64encodedstring==')
        assert s.image_b64 == 'base64encodedstring=='

    def test_optional_fields_default_to_none(self):
        s = ScreenshotIn(image_b64='abc')
        assert s.project is None
        assert s.task is None
        assert s.context is None

    def test_all_fields_populated(self):
        s = ScreenshotIn(image_b64='abc', project='P', task='T', context='C')
        assert s.project == 'P'
        assert s.task == 'T'
        assert s.context == 'C'

    def test_missing_image_b64_raises(self):
        with pytest.raises(ValidationError):
            ScreenshotIn()


class TestEntryOut:
    def _make_entry_out(self, **kwargs):
        defaults = {
            'id': 1,
            'created_at': datetime(2024, 1, 1, 12, 0, 0),
            'source': 'manual',
            'content': 'test content',
            'project': None,
            'task': None,
            'context': None,
        }
        defaults.update(kwargs)
        return EntryOut(**defaults)

    def test_valid_construction(self):
        e = self._make_entry_out()
        assert e.id == 1
        assert e.source == 'manual'
        assert e.content == 'test content'

    def test_optional_fields_accept_none(self):
        e = self._make_entry_out(project=None, task=None, context=None)
        assert e.project is None
        assert e.task is None
        assert e.context is None

    def test_optional_fields_accept_strings(self):
        e = self._make_entry_out(project='MyProject', task='MyTask', context='MyContext')
        assert e.project == 'MyProject'
        assert e.task == 'MyTask'
        assert e.context == 'MyContext'

    def test_created_at_is_datetime(self):
        e = self._make_entry_out()
        assert isinstance(e.created_at, datetime)

    def test_missing_id_raises(self):
        with pytest.raises(ValidationError):
            EntryOut(
                created_at=datetime.utcnow(),
                source='manual',
                content='x',
                project=None,
                task=None,
                context=None,
            )


class TestInsightOut:
    def _make_insight_out(self, **kwargs):
        defaults = {
            'id': 1,
            'created_at': datetime(2024, 1, 1),
            'title': 'Primary focus area',
            'description': 'You worked mostly on ProjectX.',
            'action': None,
            'confidence': 0.8,
        }
        defaults.update(kwargs)
        return InsightOut(**defaults)

    def test_valid_construction(self):
        i = self._make_insight_out()
        assert i.id == 1
        assert i.title == 'Primary focus area'
        assert i.confidence == 0.8

    def test_action_optional(self):
        i = self._make_insight_out(action=None)
        assert i.action is None

    def test_action_string(self):
        i = self._make_insight_out(action='Block time tomorrow.')
        assert i.action == 'Block time tomorrow.'

    def test_confidence_boundary_zero(self):
        i = self._make_insight_out(confidence=0.0)
        assert i.confidence == 0.0

    def test_confidence_boundary_one(self):
        i = self._make_insight_out(confidence=1.0)
        assert i.confidence == 1.0

    def test_missing_title_raises(self):
        with pytest.raises(ValidationError):
            InsightOut(
                id=1,
                created_at=datetime.utcnow(),
                description='desc',
                action=None,
                confidence=0.5,
            )