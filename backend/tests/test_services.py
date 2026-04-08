from app.api.timeline import TimelineBroadcaster
from app.services.enrichment.pipeline import enrich_with_context
from app.services.ingestion.pipeline import ingest_manual_note, ingest_screenshot, ingest_speech


def test_enrichment_contract_uses_enriched_provenance_key() -> None:
    enriched = enrich_with_context("hello")
    assert "enriched_provenance" in enriched
    assert "provenance" not in enriched


def test_ingestion_payloads_share_consistent_shape() -> None:
    speech = ingest_speech("a")
    screenshot = ingest_screenshot("b")
    manual = ingest_manual_note("c")

    for payload, source in [
        (speech, "speech"),
        (screenshot, "screenshot"),
        (manual, "manual_note"),
    ]:
        assert payload["source_type"] == source
        assert "raw_content" in payload
        assert "timestamp" in payload


def test_timeline_broadcaster_drops_oldest_when_queue_is_full() -> None:
    broadcaster = TimelineBroadcaster(max_queue_size=1)
    queue = broadcaster.subscribe()

    import asyncio

    async def _publish_two() -> None:
        await broadcaster.publish({"event": "first"})
        await broadcaster.publish({"event": "second"})

    asyncio.run(_publish_two())
    assert queue.get_nowait() == {"event": "second"}
