"""
position_memory.py — Self-learning position memory for WeChat RPA

Records successful UI element positions and recalls them for faster,
more accurate targeting. Coordinates are window-relative percentages
(xPct, yPct) to survive window moves and resizes.

Every successful operation is remembered. Next time, the system uses
the most-confident position first, then falls back to UIA scanning.

Confidence = (hit_count + 1) / (hit_count + miss_count + 2)  (Bayesian smoothed)
Scored by confidence * recency decay.

Usage:
    from position_memory import PositionMemory
    pm = PositionMemory(wxid="szyuyangmin")
    pm.remember("contacts_main", "group_header_群聊", x=320, y=180, w=1280, h=900)
    result = pm.recall("contacts_main", "group_header_群聊", window_w=1280, window_h=900)
    # result = {"xPct": 0.25, "yPct": 0.20, "x": 320, "y": 180, "confidence": 0.75, ...}
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta

DATA_ROOT = Path(os.environ.get(
    "PEEKABOO_DATA_ROOT",
    Path.home() / "Documents" / "PeekabooWin"
))

MAX_AGE_DAYS = 30
CONFIDENCE_DECAY_DAYS = 7
MIN_CONFIDENCE = 0.1


class PositionMemory:
    """Persistent self-learning position memory with Bayesian confidence scoring."""

    def __init__(self, wxid="default", platform="wechat"):
        self.wxid = wxid
        self.platform = platform
        self._data_dir = DATA_ROOT / platform / wxid
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._file_path = self._data_dir / "position_memory.json"
        self._records = {}   # key -> list[entry]
        self._loaded = False

    # ── Persistence ──

    def load(self):
        """Load position memory from JSON file."""
        if self._loaded:
            return
        if self._file_path.exists():
            try:
                with open(self._file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._records = data.get("records", {})
            except (json.JSONDecodeError, IOError):
                self._records = {}
        self._loaded = True

    def save(self):
        """Persist current records to JSON file."""
        data = {
            "_meta": {
                "version": "1.0",
                "wxid": self.wxid,
                "updated_at": datetime.now().isoformat(),
                "total_records": sum(len(v) for v in self._records.values())
            },
            "records": self._records
        }
        with open(self._file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ── Core API ──

    def remember(self, page_id, element_id, x, y, window_w, window_h,
                 fingerprint=None, action="click", automation_id=None):
        """Add or update a position memory entry.

        Args:
            page_id: Stable page id from nav_map (e.g. 'contacts_main')
            element_id: Unique element name (e.g. 'group_header_群聊')
            x, y: Absolute screen coordinates of successful click
            window_w, window_h: Window dimensions at time of click
            fingerprint: Optional OCR text for verification
            action: 'click' | 'scroll_to' | 'navigate_to'
            automation_id: Optional UIA AutomationId
        """
        self.load()

        key = f"{page_id}::{element_id}"
        if key not in self._records:
            self._records[key] = []

        x_pct = round(x / window_w, 6) if window_w else 0.0
        y_pct = round(y / window_h, 6) if window_h else 0.0
        now = datetime.now().isoformat()

        # Update existing entry within 2% tolerance
        for entry in self._records[key]:
            if (abs(entry["xPct"] - x_pct) < 0.02 and
                abs(entry["yPct"] - y_pct) < 0.02):
                entry["hit_count"] += 1
                entry["last_seen"] = now
                entry["confidence"] = self._calc_confidence(
                    entry["hit_count"], entry.get("miss_count", 0))
                return

        # New entry
        self._records[key].append({
            "xPct": x_pct,
            "yPct": y_pct,
            "action": action,
            "automation_id": automation_id,
            "fingerprint": fingerprint,
            "hit_count": 1,
            "miss_count": 0,
            "first_seen": now,
            "last_seen": now,
            "confidence": 1.0,
        })

    def recall(self, page_id, element_id, window_w=None, window_h=None,
               min_confidence=0.3):
        """Find best-known position for a page/element pair.

        Returns:
            dict with {xPct, yPct, confidence, hit_count, last_seen, ...}
            plus absolute {x, y} if window_w/h are provided.
            Returns None if no confident match found.
        """
        self.load()

        key = f"{page_id}::{element_id}"
        entries = self._records.get(key, [])
        if not entries:
            return None

        now = datetime.now()
        scored = []
        for e in entries:
            s = self._score_entry(e, now)
            if s >= min_confidence:
                e_copy = dict(e)
                e_copy["_score"] = s
                scored.append(e_copy)

        if not scored:
            return None

        scored.sort(key=lambda e: e["_score"], reverse=True)
        best = scored[0]

        result = {
            "xPct": best["xPct"],
            "yPct": best["yPct"],
            "confidence": best["_score"],
            "hit_count": best["hit_count"],
            "last_seen": best["last_seen"],
            "fingerprint": best.get("fingerprint"),
            "automation_id": best.get("automation_id"),
        }

        if window_w and window_h:
            result["x"] = int(best["xPct"] * window_w)
            result["y"] = int(best["yPct"] * window_h)

        return result

    def miss(self, page_id, element_id, x_pct=None, y_pct=None):
        """Record a failed attempt. Decrements confidence."""
        self.load()

        key = f"{page_id}::{element_id}"
        entries = self._records.get(key, [])
        if not entries:
            return

        # Penalize specific entry if coords provided
        if x_pct is not None and y_pct is not None:
            for e in entries:
                if (abs(e["xPct"] - x_pct) < 0.02 and
                    abs(e["yPct"] - y_pct) < 0.02):
                    e["miss_count"] += 1
                    e["confidence"] = self._calc_confidence(
                        e["hit_count"], e["miss_count"])
                    return

        # Penalize all entries
        for e in entries:
            e["miss_count"] += 1
            e["confidence"] = self._calc_confidence(
                e["hit_count"], e["miss_count"])

    def get_page_snapshot(self, page_id):
        """Return all memorized positions for a page, sorted by confidence."""
        self.load()

        prefix = f"{page_id}::"
        results = []
        for key, entries in self._records.items():
            if key.startswith(prefix):
                element_id = key[len(prefix):]
                for e in entries:
                    results.append({
                        "element_id": element_id,
                        "xPct": e["xPct"],
                        "yPct": e["yPct"],
                        "confidence": e.get("confidence", 0),
                        "hit_count": e["hit_count"],
                        "last_seen": e["last_seen"],
                    })
        results.sort(key=lambda r: r["confidence"], reverse=True)
        return results

    def prune(self, max_age_days=MAX_AGE_DAYS):
        """Remove entries older than max_age_days."""
        self.load()

        cutoff = datetime.now() - timedelta(days=max_age_days)
        for key in list(self._records.keys()):
            self._records[key] = [
                e for e in self._records[key]
                if self._parse_ts(e.get("last_seen", "2000-01-01")) >= cutoff
            ]
            if not self._records[key]:
                del self._records[key]

    def stats(self):
        """Return summary: {total_entries, total_pages, pages: {page_id: count}}."""
        self.load()

        pages = {}
        total = 0
        for key, entries in self._records.items():
            page_id = key.split("::")[0]
            pages[page_id] = pages.get(page_id, 0) + len(entries)
            total += len(entries)
        return {
            "total_entries": total,
            "total_pages": len(pages),
            "pages": pages,
            "file": str(self._file_path),
        }

    # ── Internal ──

    @staticmethod
    def _calc_confidence(hit_count, miss_count):
        """Bayesian-smoothed confidence: (hits+1) / (hits+misses+2).

        Add-one smoothing prevents overconfidence on small samples.
        With 1 hit, 0 miss: (1+1)/(1+0+2) = 2/3 = 0.67
        With 10 hits, 0 miss: (10+1)/(10+0+2) = 11/12 = 0.92
        With 9 hits, 1 miss: (9+1)/(9+1+2) = 10/12 = 0.83
        """
        total = hit_count + miss_count
        if total == 0:
            return 0.5
        return (hit_count + 1) / (total + 2)

    @staticmethod
    def _parse_ts(ts_str):
        """Parse ISO timestamp, return datetime.min on failure."""
        try:
            return datetime.fromisoformat(ts_str)
        except (ValueError, TypeError):
            return datetime.min

    def _score_entry(self, entry, now):
        """Score = confidence * recency_decay. Range [0, 1]."""
        confidence = entry.get("confidence", 0.5)
        last_seen = self._parse_ts(entry.get("last_seen", ""))
        age_days = (now - last_seen).total_seconds() / 86400.0 if last_seen != datetime.min else 999.0

        if age_days <= CONFIDENCE_DECAY_DAYS:
            recency = 1.0
        else:
            decay_days = age_days - CONFIDENCE_DECAY_DAYS
            recency = max(0.05, 1.0 - decay_days / MAX_AGE_DAYS)

        return round(confidence * recency, 4)


# ── CLI test ──
if __name__ == "__main__":
    pm = PositionMemory(wxid="test")
    print("=== PositionMemory Test ===")

    # Remember
    pm.remember("contacts_main", "group_header_群聊", x=320, y=180, window_w=1280, window_h=900)
    pm.remember("contacts_main", "group_header_群聊", x=322, y=181, window_w=1280, window_h=900)
    pm.remember("contacts_main", "group_header_联系人", x=320, y=600, window_w=1280, window_h=900)

    # Recall
    r = pm.recall("contacts_main", "group_header_群聊", window_w=1280, window_h=900)
    print(f"Recall 群聊: {r}")

    r2 = pm.recall("contacts_main", "group_header_联系人", window_w=1280, window_h=900)
    print(f"Recall 联系人: {r2}")

    # Miss
    pm.miss("contacts_main", "group_header_群聊")
    r3 = pm.recall("contacts_main", "group_header_群聊", window_w=1280, window_h=900)
    print(f"After miss: {r3}")

    # Stats
    print(f"Stats: {pm.stats()}")

    # Snapshot
    snap = pm.get_page_snapshot("contacts_main")
    print(f"Snapshot contacts_main: {snap}")

    # Save
    pm.save()
    print(f"Saved to {pm._file_path}")

    # Reload
    pm2 = PositionMemory(wxid="test")
    r4 = pm2.recall("contacts_main", "group_header_群聊")
    print(f"After reload: {r4}")

    print("=== OK ===")
