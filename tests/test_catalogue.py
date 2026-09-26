# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""Validate source parsing and the offline site build."""

import datetime as dt
import json
from pathlib import Path
import tempfile
import unittest

from build import build, read_catalogue


class CatalogueTests(unittest.TestCase):
    def test_catalogue_covers_every_year_and_type(self):
        rows = read_catalogue()
        self.assertEqual(set(range(2001, 2101)), {r["year"] for r in rows})
        self.assertEqual({"T": 85, "P": 57, "N": 86}, {t: sum(r["type"] == t for r in rows) for t in "TPN"})
        self.assertEqual(len(rows), len({r["id"] for r in rows}))
        for r in rows:
            self.assertGreater(r["penumbralMinutes"], 0)
            self.assertGreaterEqual(r["penumbralMinutes"], r["umbralMinutes"] or 0)
            self.assertGreaterEqual(r["umbralMinutes"] or 0, r["totalMinutes"] or 0)

    def test_known_2026_td_to_ut_conversion(self):
        march = next(r for r in read_catalogue() if r["date"] == "2026-03-03")
        expected = dt.datetime(2026, 3, 3, 11, 33, 37, tzinfo=dt.timezone.utc)
        self.assertEqual(march["greatestUT"], expected.timestamp() * 1000)
        self.assertEqual(march["totalMinutes"], 58.3)
        self.assertEqual(march["deltaT"], 75)

    def test_build_contains_local_assets_and_parseable_json(self):
        with tempfile.TemporaryDirectory() as directory:
            output = build(directory)
            for name in ["index.html", "styles.css", "app.js", "instrument.mjs", "model.mjs", "eclipses.json"]:
                self.assertTrue((output / name).is_file(), name)
            self.assertEqual(len(json.loads((Path(directory) / "eclipses.json").read_text())), 228)


if __name__ == "__main__":
    unittest.main()
