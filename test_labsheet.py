"""Check the browser-downloaded Coimbra lab hand-off sample."""

import csv
from io import StringIO
from pathlib import Path


SAMPLE = Path(__file__).resolve().parent / "docs" / "validation" / "lab-sheet-coimbra-replay.csv"
COLUMNS = [
    "rank", "site_code", "site_name", "city", "latitude", "longitude",
    "action", "categories", "stored_scores", "window_start", "window_end",
    "window_label", "review", "draft_notice", "confirmation_sample_date",
    "sewage_distance_m", "filed_service_request", "note",
]


def main():
    raw = SAMPLE.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf"), "Excel needs the UTF-8 BOM for these names"
    assert raw.endswith(b"\r\n")
    assert raw.count(b"\r\n") == 6 and raw.count(b"\n") == 6
    lines = raw.decode("utf-8-sig").split("\r\n")
    assert all(line.startswith('"') and line.endswith('"') for line in lines[:-1])

    reader = csv.DictReader(StringIO(raw.decode("utf-8-sig"), newline=""))
    assert reader.fieldnames == COLUMNS
    rows = list(reader)
    assert [row["site_code"] for row in rows] == ["C5", "C12", "C6", "C7", "C20"]
    assert [row["rank"] for row in rows] == ["1", "2", "3", "4", "5"]
    assert rows[0]["stored_scores"] == "faecal 1.00; pathogen 1.00"
    assert rows[0]["filed_service_request"] == "ServiceRequest/1046 (shape v1)"
    assert rows[0]["window_start"] == "2026-05-11"
    assert rows[0]["window_end"] == "2026-05-12"
    assert rows[3]["site_name"] == "São Romão"
    assert all(row["review"] == "not reviewed" for row in rows)
    print("PASS browser-downloaded Coimbra lab sheet: BOM, CRLF, headers, five ranked rows, accents")


if __name__ == "__main__":
    main()
