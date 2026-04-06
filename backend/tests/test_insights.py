"""Tests for app/services/insights.py – generate_insights() and safe_metadata()."""
from __future__ import annotations

import json

import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from sqlmodel import select

from app.db.models import Entry, Insight
from app.services.insights import generate_insights, safe_metadata


# ---------------------------------------------------------------------------
# Isolated in-memory DB fixture for this module
# ---------------------------------------------------------------------------

@pytest.fixture(name='db_session')
def db_session_fixture():
    engine = create_engine(
        'sqlite://',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


# ---------------------------------------------------------------------------
# safe_metadata
# ---------------------------------------------------------------------------

class TestSafeMetadata:
    def test_none_input_returns_none(self):
        assert safe_metadata(None) is None

    def test_empty_dict_returns_none(self):
        """Empty dict is falsy – should return None."""
        assert safe_metadata({}) is None

    def test_non_empty_dict_returns_json_string(self):
        result = safe_metadata({'key': 'value'})
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed == {'key': 'value'}

    def test_nested_dict_serialised_correctly(self):
        meta = {'provider': 'gemini', 'content': {'facts': ['a', 'b']}}
        result = safe_metadata(meta)
        assert json.loads(result) == meta

    def test_unicode_characters_preserved(self):
        meta = {'note': 'résumé – café'}
        result = safe_metadata(meta)
        assert 'résumé' in result
        assert 'café' in result

    def test_returns_valid_json(self):
        meta = {'nums': [1, 2, 3], 'flag': True, 'nothing': None}
        result = safe_metadata(meta)
        parsed = json.loads(result)
        assert parsed['nums'] == [1, 2, 3]
        assert parsed['flag'] is True
        assert parsed['nothing'] is None

    def test_ensure_ascii_false(self):
        """Non-ASCII characters should NOT be backslash-escaped."""
        meta = {'emoji': '😊'}
        result = safe_metadata(meta)
        assert '😊' in result


# ---------------------------------------------------------------------------
# generate_insights
# ---------------------------------------------------------------------------

class TestGenerateInsights:
    def test_empty_entries_returns_empty_list(self, db_session):
        result = generate_insights(db_session)
        assert result == []

    def test_single_entry_produces_two_insights(self, db_session):
        db_session.add(Entry(source='manual', content='hello', project='Alpha'))
        db_session.commit()

        results = generate_insights(db_session)
        assert len(results) == 2

    def test_insights_have_correct_titles(self, db_session):
        db_session.add(Entry(source='voice', content='note', project='Beta'))
        db_session.commit()

        results = generate_insights(db_session)
        titles = {r.title for r in results}
        assert 'Primary focus area' in titles
        assert 'Capture channel trend' in titles

    def test_primary_focus_area_reflects_top_project(self, db_session):
        for _ in range(3):
            db_session.add(Entry(source='manual', content='x', project='ProjectX'))
        db_session.add(Entry(source='manual', content='y', project='ProjectY'))
        db_session.commit()

        results = generate_insights(db_session)
        focus = next(r for r in results if r.title == 'Primary focus area')
        assert 'ProjectX' in focus.description
        assert '3' in focus.description

    def test_entries_with_no_project_bucket_into_general(self, db_session):
        for _ in range(2):
            db_session.add(Entry(source='screenshot', content='s'))
        db_session.commit()

        results = generate_insights(db_session)
        focus = next(r for r in results if r.title == 'Primary focus area')
        assert 'General' in focus.description

    def test_capture_channel_trend_reflects_top_source(self, db_session):
        for _ in range(4):
            db_session.add(Entry(source='voice', content='audio note'))
        db_session.add(Entry(source='manual', content='typed'))
        db_session.commit()

        results = generate_insights(db_session)
        trend = next(r for r in results if r.title == 'Capture channel trend')
        assert 'voice' in trend.description
        assert '4' in trend.description

    def test_insights_persisted_to_db(self, db_session):
        db_session.add(Entry(source='manual', content='persisted test'))
        db_session.commit()

        generate_insights(db_session)

        stored = db_session.exec(select(Insight)).all()
        assert len(stored) >= 2

    def test_insights_have_ids_after_generation(self, db_session):
        db_session.add(Entry(source='manual', content='x'))
        db_session.commit()

        results = generate_insights(db_session)
        for r in results:
            assert r.id is not None

    def test_confidence_values_in_range(self, db_session):
        db_session.add(Entry(source='manual', content='check confidence'))
        db_session.commit()

        results = generate_insights(db_session)
        for r in results:
            assert 0.0 <= r.confidence <= 1.0

    def test_multiple_calls_append_more_insights(self, db_session):
        db_session.add(Entry(source='manual', content='first call'))
        db_session.commit()

        generate_insights(db_session)
        generate_insights(db_session)

        stored = db_session.exec(select(Insight)).all()
        # Each call generates 2 insights
        assert len(stored) >= 4

    def test_action_field_not_empty_for_primary_focus(self, db_session):
        db_session.add(Entry(source='manual', content='action check', project='ActionProject'))
        db_session.commit()

        results = generate_insights(db_session)
        focus = next(r for r in results if r.title == 'Primary focus area')
        assert focus.action is not None and len(focus.action) > 0