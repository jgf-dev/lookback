"""Integration tests for app/main.py – all FastAPI endpoints."""
from __future__ import annotations

import io
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from app.db.models import DailySummary, Entry, Insight
from app.db.session import get_session
from app.main import app
from app.services.ai_clients import ai_clients as real_ai_clients


# ---------------------------------------------------------------------------
# Per-test in-memory database + TestClient fixture
# ---------------------------------------------------------------------------

@pytest.fixture()
def db_engine():
    engine = create_engine(
        'sqlite://',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture()
def db_session(db_engine):
    with Session(db_engine) as session:
        yield session


@pytest.fixture()
def client(db_session):
    """TestClient backed by an isolated in-memory DB and stub AI clients."""

    def override_get_session():
        yield db_session

    # Stub ai_clients so we never call real external APIs
    stub = MagicMock(spec=real_ai_clients.__class__)
    stub.deep_search.return_value = {'provider': 'none', 'content': '{}'}
    stub.transcribe_audio.return_value = 'transcribed text'
    stub.analyze_screenshot.return_value = 'screenshot analysis'

    app.dependency_overrides[get_session] = override_get_session

    with patch('app.main.ai_clients', stub):
        with TestClient(app) as c:
            yield c

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------

class TestHealthEndpoint:
    def test_returns_200(self, client):
        response = client.get('/health')
        assert response.status_code == 200

    def test_returns_ok_status(self, client):
        response = client.get('/health')
        assert response.json() == {'status': 'ok'}


# ---------------------------------------------------------------------------
# POST /entries
# ---------------------------------------------------------------------------

class TestAddEntry:
    def test_returns_201_or_200(self, client):
        response = client.post('/entries', json={'source': 'manual', 'content': 'hello'})
        assert response.status_code in (200, 201)

    def test_response_contains_expected_fields(self, client):
        response = client.post('/entries', json={'source': 'manual', 'content': 'test note'})
        data = response.json()
        assert 'id' in data
        assert data['source'] == 'manual'
        assert data['content'] == 'test note'

    def test_optional_fields_passed_through(self, client):
        payload = {
            'source': 'manual',
            'content': 'with extras',
            'project': 'Proj',
            'task': 'Task1',
            'context': 'Ctx',
        }
        data = client.post('/entries', json=payload).json()
        assert data['project'] == 'Proj'
        assert data['task'] == 'Task1'
        assert data['context'] == 'Ctx'

    def test_entry_persisted_to_db(self, client, db_session):
        client.post('/entries', json={'source': 'manual', 'content': 'persisted'})
        entries = db_session.exec(select(Entry)).all()
        assert any(e.content == 'persisted' for e in entries)

    def test_missing_content_returns_422(self, client):
        response = client.post('/entries', json={'source': 'manual'})
        assert response.status_code == 422

    def test_missing_source_returns_422(self, client):
        response = client.post('/entries', json={'content': 'hello'})
        assert response.status_code == 422

    def test_ai_deep_search_called(self, client):
        with patch('app.main.ai_clients') as mock_ai:
            mock_ai.deep_search.return_value = {'provider': 'none', 'content': '{}'}
            client.post('/entries', json={'source': 'manual', 'content': 'enrich me'})
            mock_ai.deep_search.assert_called_once_with('enrich me')

    def test_returned_id_is_integer(self, client):
        data = client.post('/entries', json={'source': 'manual', 'content': 'id check'}).json()
        assert isinstance(data['id'], int)
        assert data['id'] > 0


# ---------------------------------------------------------------------------
# POST /audio/transcribe
# ---------------------------------------------------------------------------

class TestTranscribeAudio:
    def test_returns_200(self, client):
        audio_bytes = b'\x00\x01\x02\x03'
        response = client.post(
            '/audio/transcribe',
            files={'audio': ('test.wav', audio_bytes, 'audio/wav')},
        )
        assert response.status_code == 200

    def test_response_source_is_voice(self, client):
        audio_bytes = b'\x00\x01'
        data = client.post(
            '/audio/transcribe',
            files={'audio': ('test.wav', audio_bytes, 'audio/wav')},
        ).json()
        assert data['source'] == 'voice'

    def test_response_content_matches_transcription(self, client):
        audio_bytes = b'\x00\x01'
        data = client.post(
            '/audio/transcribe',
            files={'audio': ('test.wav', audio_bytes, 'audio/wav')},
        ).json()
        assert data['content'] == 'transcribed text'

    def test_optional_query_params_stored(self, client):
        audio_bytes = b'\x00'
        data = client.post(
            '/audio/transcribe?project=MyProj&task=MyTask&context=MyCxt',
            files={'audio': ('a.wav', audio_bytes, 'audio/wav')},
        ).json()
        assert data['project'] == 'MyProj'
        assert data['task'] == 'MyTask'
        assert data['context'] == 'MyCxt'

    def test_entry_saved_to_db(self, client, db_session):
        client.post(
            '/audio/transcribe',
            files={'audio': ('a.wav', b'\x00', 'audio/wav')},
        )
        entries = db_session.exec(select(Entry).where(Entry.source == 'voice')).all()
        assert len(entries) >= 1

    def test_no_audio_file_returns_422(self, client):
        response = client.post('/audio/transcribe')
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /screenshots
# ---------------------------------------------------------------------------

class TestAddScreenshot:
    def test_returns_200(self, client):
        response = client.post('/screenshots', json={'image_b64': 'abc123=='})
        assert response.status_code == 200

    def test_response_source_is_screenshot(self, client):
        data = client.post('/screenshots', json={'image_b64': 'abc'}).json()
        assert data['source'] == 'screenshot'

    def test_response_content_from_analysis(self, client):
        data = client.post('/screenshots', json={'image_b64': 'img'}).json()
        assert data['content'] == 'screenshot analysis'

    def test_optional_fields_stored(self, client):
        payload = {'image_b64': 'img', 'project': 'P', 'task': 'T', 'context': 'C'}
        data = client.post('/screenshots', json=payload).json()
        assert data['project'] == 'P'
        assert data['task'] == 'T'
        assert data['context'] == 'C'

    def test_entry_source_correct_in_db(self, client, db_session):
        client.post('/screenshots', json={'image_b64': 'x'})
        entries = db_session.exec(select(Entry).where(Entry.source == 'screenshot')).all()
        assert len(entries) >= 1

    def test_missing_image_b64_returns_422(self, client):
        response = client.post('/screenshots', json={})
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /timeline
# ---------------------------------------------------------------------------

class TestGetTimeline:
    def test_returns_200(self, client):
        assert client.get('/timeline').status_code == 200

    def test_empty_db_returns_empty_list(self, client):
        data = client.get('/timeline').json()
        assert data == []

    def test_entries_returned_in_order(self, client, db_session):
        from datetime import timedelta

        t1 = datetime(2024, 1, 1, 10, 0, 0)
        t2 = datetime(2024, 1, 1, 11, 0, 0)
        db_session.add(Entry(source='manual', content='first', created_at=t1))
        db_session.add(Entry(source='manual', content='second', created_at=t2))
        db_session.commit()

        data = client.get('/timeline').json()
        assert data[0]['content'] == 'first'
        assert data[1]['content'] == 'second'

    def test_returns_all_entries(self, client, db_session):
        for i in range(5):
            db_session.add(Entry(source='manual', content=f'entry {i}'))
        db_session.commit()

        data = client.get('/timeline').json()
        assert len(data) == 5

    def test_each_entry_has_required_fields(self, client, db_session):
        db_session.add(Entry(source='manual', content='check fields'))
        db_session.commit()

        data = client.get('/timeline').json()
        entry = data[0]
        for field in ('id', 'created_at', 'source', 'content'):
            assert field in entry


# ---------------------------------------------------------------------------
# POST /insights/generate
# ---------------------------------------------------------------------------

class TestRunInsights:
    def test_returns_200(self, client, db_session):
        db_session.add(Entry(source='manual', content='seed'))
        db_session.commit()
        assert client.post('/insights/generate').status_code == 200

    def test_empty_entries_returns_empty_list(self, client):
        data = client.post('/insights/generate').json()
        assert data == []

    def test_returns_two_insights_for_single_entry(self, client, db_session):
        db_session.add(Entry(source='voice', content='note'))
        db_session.commit()
        data = client.post('/insights/generate').json()
        assert len(data) == 2

    def test_insight_fields_present(self, client, db_session):
        db_session.add(Entry(source='manual', content='x'))
        db_session.commit()
        data = client.post('/insights/generate').json()
        for i in data:
            assert 'id' in i
            assert 'title' in i
            assert 'description' in i
            assert 'confidence' in i


# ---------------------------------------------------------------------------
# GET /insights
# ---------------------------------------------------------------------------

class TestListInsights:
    def test_returns_200(self, client):
        assert client.get('/insights').status_code == 200

    def test_empty_returns_empty_list(self, client):
        assert client.get('/insights').json() == []

    def test_returns_persisted_insights(self, client, db_session):
        db_session.add(Insight(title='T', description='D', confidence=0.5))
        db_session.commit()
        data = client.get('/insights').json()
        assert len(data) == 1
        assert data[0]['title'] == 'T'


# ---------------------------------------------------------------------------
# POST /day/finish
# ---------------------------------------------------------------------------

class TestFinishDay:
    def test_returns_200(self, client):
        assert client.post('/day/finish').status_code == 200

    def test_returns_summary_ready_status(self, client):
        data = client.post('/day/finish').json()
        assert data == {'status': 'summary_ready'}

    def test_daily_summary_created_in_db(self, client, db_session):
        client.post('/day/finish')
        summaries = db_session.exec(select(DailySummary)).all()
        assert len(summaries) == 1

    def test_summary_contains_today_date(self, client, db_session):
        client.post('/day/finish')
        summary = db_session.exec(select(DailySummary)).first()
        today = datetime.utcnow().strftime('%Y-%m-%d')
        assert today in summary.summary_markdown

    def test_summary_contains_entry_content(self, client, db_session):
        db_session.add(Entry(source='manual', content='important task'))
        db_session.commit()

        client.post('/day/finish')
        summary = db_session.exec(select(DailySummary)).first()
        assert 'important task' in summary.summary_markdown

    def test_second_call_overwrites_summary(self, client, db_session):
        db_session.add(Entry(source='manual', content='first'))
        db_session.commit()
        client.post('/day/finish')

        db_session.add(Entry(source='manual', content='second update'))
        db_session.commit()
        client.post('/day/finish')

        summaries = db_session.exec(select(DailySummary)).all()
        assert len(summaries) == 1  # Not duplicated

    def test_summary_includes_next_step_text(self, client, db_session):
        client.post('/day/finish')
        summary = db_session.exec(select(DailySummary)).first()
        assert 'voice session' in summary.summary_markdown.lower() or \
               'Next step' in summary.summary_markdown

    def test_finish_day_with_many_entries_truncates_to_25(self, client, db_session):
        for i in range(30):
            db_session.add(Entry(source='manual', content=f'entry {i}'))
        db_session.commit()

        client.post('/day/finish')
        summary = db_session.exec(select(DailySummary)).first()
        # The last 25 entries should appear; the first 5 (entry 0..4) should not
        bullet_count = summary.summary_markdown.count('- [manual]')
        assert bullet_count == 25