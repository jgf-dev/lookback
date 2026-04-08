import pytest
from pydantic import ValidationError

from shared.python.contracts import AnalysisRequest, AnalysisResponse


class TestAnalysisRequest:
    def test_valid_note(self) -> None:
        req = AnalysisRequest(note="some content")
        assert req.note == "some content"

    def test_single_character_note_is_valid(self) -> None:
        req = AnalysisRequest(note="x")
        assert req.note == "x"

    def test_empty_note_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            AnalysisRequest(note="")

    def test_missing_note_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            AnalysisRequest()  # type: ignore[call-arg]

    def test_note_with_whitespace_is_valid(self) -> None:
        req = AnalysisRequest(note="  spaces  ")
        assert req.note == "  spaces  "

    def test_note_with_newlines_is_valid(self) -> None:
        req = AnalysisRequest(note="line one\nline two")
        assert req.note == "line one\nline two"

    def test_long_note_is_valid(self) -> None:
        long_note = "word " * 1000
        req = AnalysisRequest(note=long_note)
        assert req.note == long_note

    def test_extra_fields_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AnalysisRequest(note="valid", extra_field="oops")  # type: ignore[call-arg]


class TestAnalysisResponse:
    def test_valid_response(self) -> None:
        resp = AnalysisResponse(summary="Processed note with 3 words", score=0.5)
        assert resp.summary == "Processed note with 3 words"
        assert resp.score == 0.5

    def test_score_zero_is_valid(self) -> None:
        resp = AnalysisResponse(summary="summary", score=0.0)
        assert resp.score == 0.0

    def test_score_one_is_valid(self) -> None:
        resp = AnalysisResponse(summary="summary", score=1.0)
        assert resp.score == 1.0

    def test_score_below_zero_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            AnalysisResponse(summary="summary", score=-0.01)

    def test_score_above_one_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            AnalysisResponse(summary="summary", score=1.01)

    def test_missing_summary_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            AnalysisResponse(score=0.5)  # type: ignore[call-arg]

    def test_missing_score_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            AnalysisResponse(summary="summary")  # type: ignore[call-arg]

    def test_score_midpoint_is_valid(self) -> None:
        resp = AnalysisResponse(summary="ok", score=0.5)
        assert resp.score == 0.5

    def test_empty_summary_is_valid(self) -> None:
        # summary: str has no min_length constraint
        resp = AnalysisResponse(summary="", score=0.0)
        assert resp.summary == ""