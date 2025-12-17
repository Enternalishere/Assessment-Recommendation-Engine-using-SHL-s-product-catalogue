from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import hashlib
import json
import datetime


def canonical_id(url: str) -> str:
    u = url.strip().lower()
    return hashlib.md5(u.encode("utf-8")).hexdigest()


@dataclass
class Assessment:
    id: str
    name: str
    url: str
    type: str
    description: str
    skills: List[str]
    tags: List[str]
    language: str
    scraped_at: str

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Assessment":
        return Assessment(
            id=d["id"],
            name=d.get("name", ""),
            url=d.get("url", ""),
            type=d.get("type", ""),
            description=d.get("description", ""),
            skills=d.get("skills", []) or [],
            tags=d.get("tags", []) or [],
            language=d.get("language", "en"),
            scraped_at=d.get("scraped_at", ""),
        )

    def to_json(self) -> str:
        return json.dumps(
            {
                "id": self.id,
                "name": self.name,
                "url": self.url,
                "type": self.type,
                "description": self.description,
                "skills": self.skills,
                "tags": self.tags,
                "language": self.language,
                "scraped_at": self.scraped_at,
            },
            ensure_ascii=False,
        )


def now_iso() -> str:
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

