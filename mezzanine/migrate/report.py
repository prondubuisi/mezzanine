"""Printed migration report for WordPress imports (design §12 / KD15)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MigrationReport:
    posts_imported: int = 0
    pages_imported: int = 0
    redirects_created: int = 0
    comments_imported: int = 0
    url_pairs: list[tuple[str, str]] = field(default_factory=list)
    unmapped_types: dict[str, int] = field(default_factory=dict)
    failed_attachments: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)

    def note_unmapped(self, post_type: str) -> None:
        self.unmapped_types[post_type] = self.unmapped_types.get(post_type, 0) + 1

    def note_redirect(self, old_url: str, new_path: str) -> None:
        self.redirects_created += 1
        self.url_pairs.append((old_url, new_path))

    def note_attachment_failure(self, message: str) -> None:
        self.failed_attachments.append(message)

    def to_dict(self) -> dict[str, Any]:
        """Machine-readable report (KD15: MigrationReport JSON)."""
        return {
            "posts_imported": self.posts_imported,
            "pages_imported": self.pages_imported,
            "comments_imported": self.comments_imported,
            "redirects_created": self.redirects_created,
            "unmapped_types": dict(sorted(self.unmapped_types.items())),
            "failed_attachments": list(self.failed_attachments),
            "skipped": list(self.skipped),
            "url_fidelity": [
                {"old": old, "new": new} for old, new in self.url_pairs
            ],
        }

    def to_json(self, *, indent: int | None = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def render(self) -> str:
        lines = [
            "=== Nova WordPress migration report ===",
            f"Posts imported:      {self.posts_imported}",
            f"Pages imported:      {self.pages_imported}",
            f"Comments imported:   {self.comments_imported}",
            f"Redirects created:   {self.redirects_created}",
        ]
        if self.unmapped_types:
            lines.append("Unmapped types:")
            for name, count in sorted(self.unmapped_types.items()):
                lines.append(f"  - {name}: {count}")
        else:
            lines.append("Unmapped types: none")
        if self.failed_attachments:
            lines.append("Failed attachments:")
            for msg in self.failed_attachments:
                lines.append(f"  - {msg}")
        else:
            lines.append("Failed attachments: none")
        if self.skipped:
            lines.append("Skipped:")
            for msg in self.skipped:
                lines.append(f"  - {msg}")
        if self.url_pairs:
            lines.append("URL fidelity (old → new):")
            for old, new in self.url_pairs[:50]:
                lines.append(f"  {old} → {new}")
            if len(self.url_pairs) > 50:
                lines.append(f"  … and {len(self.url_pairs) - 50} more")
        lines.append("=== end report ===")
        return "\n".join(lines)
