"""User consent management — routes and gating dependency.

Consent is enforced only when the application is in *production mode*
(``LOOKBACK_API_KEY`` is set in the environment).  In dev mode the consent
check is skipped entirely so existing development workflows are unaffected.

The single-user model uses the fixed ``user_id`` value ``"default_user"``.
"""

import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.auth import require_auth
from app.db.session import get_db
from app.models.db_models import AuditLog, UserConsent
from app.models.schemas import ConsentCreate, ConsentRead

router = APIRouter(prefix="/api")

_DEFAULT_USER = "default_user"
_DATA_CAPTURE = "data_capture"


# ─── Shared DB dependency ────────────────────────────────────────────────────

def _db(request: Request):  # noqa: ANN201
    yield from get_db(request.app.state.session_factory)


# ─── Internal helpers ─────────────────────────────────────────────────────────

def _latest_consent(
    db: Session, user_id: str, consent_type: str
) -> UserConsent | None:
    return (
        db.query(UserConsent)
        .filter(UserConsent.user_id == user_id, UserConsent.consent_type == consent_type)
        .order_by(UserConsent.timestamp.desc())
        .first()
    )


# ─── Consent gating dependency ───────────────────────────────────────────────

def require_data_capture_consent(
    request: Request,
    db: Session = Depends(_db),
) -> None:
    """Raise HTTP 403 when data-capture consent has not been granted.

    In dev mode (no ``LOOKBACK_API_KEY`` configured) this check is bypassed.
    """
    if not os.environ.get("LOOKBACK_API_KEY", "").strip():
        return  # dev mode — bypass consent enforcement

    record = _latest_consent(db, _DEFAULT_USER, _DATA_CAPTURE)
    if record is None or not record.granted:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Data-capture consent has not been granted. "
                'POST /api/consent with {"consent_type": "data_capture", "granted": true} '
                "to enable capture."
            ),
        )


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.get("/consent", response_model=list[ConsentRead])
def get_consent_status(
    request: Request,
    db: Session = Depends(_db),
) -> list[ConsentRead]:
    """Return the latest consent record for each consent type."""
    records = (
        db.query(UserConsent)
        .filter(UserConsent.user_id == _DEFAULT_USER)
        .order_by(UserConsent.consent_type, UserConsent.timestamp.desc())
        .all()
    )
    seen: set[str] = set()
    result: list[ConsentRead] = []
    for r in records:
        if r.consent_type not in seen:
            seen.add(r.consent_type)
            result.append(
                ConsentRead(
                    user_id=r.user_id,
                    consent_type=r.consent_type,
                    granted=r.granted,
                    timestamp=r.timestamp,
                )
            )
    return result


@router.post("/consent", response_model=ConsentRead, status_code=201)
def update_consent(
    payload: ConsentCreate,
    request: Request,
    actor: str = Depends(require_auth),
    db: Session = Depends(_db),
) -> ConsentRead:
    """Grant or revoke consent for a given consent type.

    Each call appends a new immutable record (full history is preserved).
    """
    now = datetime.now(timezone.utc)
    record = UserConsent(
        user_id=_DEFAULT_USER,
        consent_type=payload.consent_type,
        granted=payload.granted,
        timestamp=now,
        provenance={"actor": actor},
    )
    db.add(record)
    db.add(
        AuditLog(
            item_id=None,
            action="consent_updated",
            actor=actor,
            changes={
                "consent_type": payload.consent_type,
                "granted": payload.granted,
            },
        )
    )
    db.commit()
    return ConsentRead(
        user_id=_DEFAULT_USER,
        consent_type=record.consent_type,
        granted=record.granted,
        timestamp=record.timestamp,
    )
