from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

@dataclass
class BaseEvent:
    event_id: UUID
    event_type: str
    timestamp: datetime
    payload: Dict[str, Any]
    aggregate_id: Optional[UUID] = None  # ID de l'entité principale

    @classmethod
    def create(cls, event_type: str, payload: Dict[str, Any], aggregate_id: Optional[UUID] = None):
        return cls(
            event_id=uuid4(),
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            payload=payload,
            aggregate_id=aggregate_id
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': str(self.event_id),
            'event_type': self.event_type,
            'timestamp': self.timestamp.isoformat(),
            'aggregate_id': str(self.aggregate_id) if self.aggregate_id else None,
            'payload': self.payload
        }
