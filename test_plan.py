"""Run with python test_plan.py. Tiny fixtures are tests, not demo data."""

from copy import deepcopy
from contextlib import redirect_stdout
from datetime import date, timedelta
import hashlib
import io
import json
from pathlib import Path

try:
    import plan
except ModuleNotFoundError as exc:
    if exc.name != "plan":
        raise
    plan = None

ROOT = Path(__file__).resolve().parent
CONFIG = {"RAIN_MM": 20, "TEST_MIN": 0.5, "ADVISORY_MIN": 0.5,
          "VISITS_PER_CITY": 5, "WINDOW_DAYS": 2}


def fixture(codes=("T1",), scores=None, distances=None, rain=20):
    city = {"id": "TO", "name": "Toulouse", "latitude": 43.6, "longitude": 1.44}
    sites = [{"code": code, "name": code, "city": city,
              "latitude": 43.6, "longitude": 1.44} for code in codes]
    scores = scores if scores is not None else {codes[0]: (0.7, 0.6, 0.2)}
    health = [{"researchSiteCode": code, "samplingDate": "2023-05-05T00:00:00",
               "scaledFecalRisk": values[0], "scaledPathogenRisk": values[1],
               "scaledArgRisk": values[2], "healthRiskScore": 0.4}
              for code, values in scores.items()]
    distances = distances if distances is not None else {code: 100 for code in codes}
    urban = [{"researchSiteCode": code, "distanceToSewageStations": distance}
             for code, distance in distances.items()]
    weather = {code: [{"siteCode": code, "date": "2026-08-03", "precipTotalMm": rain}]
               for code in codes}
    days = [(date(2026, 10, 3) + timedelta(days=i)).isoformat() for i in range(7)]
    forecast = {"daily": {"time": days, "precipitation_sum": [rain] + [0] * 6},
                "daily_units": {"time": "iso8601", "precipitation_sum": "mm"},
                "timezone": "Europe/Paris"}
    return sites, health, urban, weather, {"TO": forecast}


def result(data, config=None, mode="live"):
    return plan.build_plan(*data, config or CONFIG)["cities"]["TO"]["modes"][mode]


def row(output, code):
    return next(site for site in output["sites"] if site["code"] == code)


def rejects(call):
    try:
        call()
    except ValueError:
        return
    assert False, "Expected ValueError"


def test_planner_exists_and_defaults_match():
    assert plan is not None, "Phase 2 plan.py is not implemented yet"
    assert plan.load_config(ROOT / "config.json") == CONFIG


def test_rain_threshold_boundary():
    assert result(fixture(rain=19.9))["storm"] is None
    assert result(fixture(rain=19.9))["weather_status"] == "no_storm"
    assert result(fixture(rain=20))["storm"]["anchor_date"] == "2026-10-03"


def test_dominant_and_second_category_are_not_assays():
    output = result(fixture(scores={"T1": (0.5, 0.7, 0.9)}))
    site = row(output, "T1")
    assert site["categories"] == ["antibiotic resistance", "pathogen"]
    assert site["dominant_value"] == 0.9
    assert site["action"] == "new category assessment"
    assert "scaledArgRisk" in site["source_health"]


def test_below_threshold_has_no_storm_visit():
    output = result(fixture(scores={"T1": (0.49, 0.2, 0.3)}))
    assert not output["ranking"] and not output["allocated_codes"]
    assert row(output, "T1")["status"] == "low priority this storm"


def test_calendar_window_and_consecutive_days():
    data = fixture()
    data[4]["TO"]["daily"]["precipitation_sum"] = [20, 25, 0, 0, 0, 0, 0]
    storm = result(data)["storm"]
    assert storm["wet_dates"] == ["2026-10-03", "2026-10-04"]
    assert storm["anchor_date"] == "2026-10-04"
    assert storm["window"]["start_date"] == "2026-10-05"
    assert storm["window"]["end_date"] == "2026-10-06"
    assert storm["window"]["label"] == "Experimental window (heuristic, not validated)"
    assert all("T" not in storm["window"][key] for key in ("start_date", "end_date"))
    assert plan.sampling_window("2026-12-31", 2)["end_date"] == "2027-01-02"


def test_budget_ties_and_baseline_after_storm():
    data = fixture(codes=("T1", "T2", "T3", "T10", "T21", "T24"),
                   scores={"T1": (0.8, 0.7, 0.1), "T2": (0.8, 0.2, 0.1),
                           "T10": (0.8, 0.2, 0.1)},
                   distances={"T1": 200, "T2": 100, "T10": 100, "T3": 1})
    config = {**CONFIG, "VISITS_PER_CITY": 4}
    output = result(data, config)
    assert output["ranking"] == ["T2", "T10", "T1", "T3", "T21", "T24"]
    assert output["allocated_codes"] == ["T2", "T10", "T1", "T3"]
    assert row(output, "T3")["categories"] == ["faecal", "pathogen", "antibiotic resistance"]
    assert row(output, "T24")["allocation"] == "if capacity allows"
    assert len(output["allocated_codes"]) == 4, "Budget counts visits, not categories"
    assert not result(data, {**config, "VISITS_PER_CITY": 0})["allocated_codes"]


def test_missing_sewage_distance_ranks_last_and_shows_reason():
    data = fixture(codes=("T24", "T3", "T21", "T2"), scores={},
                   distances={"T2": 0, "T3": 800}, rain=0)
    output = result(data)
    assert output["ranking"] == ["T2", "T3", "T21", "T24"]
    for code in ("T21", "T24"):
        site = row(output, code)
        assert site["sewage_distance_m"] is None
        assert "missing sewage distance" in site["reason"].lower()
        assert "last" in site["reason"].lower()


def test_invalid_health_is_retained_and_never_becomes_a_baseline():
    for bad in (-0.1, 1.01, None, True, "0.8", float("nan")):
        data = fixture(scores={"T1": (bad, 0.8, 0.2)})
        output = result(data)
        assert len(output["sites"]) == 1
        assert row(output, "T1")["status"] == "invalid source data"
        assert not output["ranking"]
    for bad in (None, "", "2023-02-30"):
        data = fixture()
        data[1][0]["samplingDate"] = bad
        assert not result(data)["allocated_codes"]


def test_missing_coordinates_do_not_block_visit():
    data = fixture()
    data[0][0]["latitude"] = None
    site = row(result(data), "T1")
    assert site["allocation"] == "allocated"
    assert site["position"] is None and "no map pin" in site["map_note"].lower()


def test_no_storm_only_allocates_baselines():
    data = fixture(codes=("T1", "T2"), rain=0)
    output = result(data)
    assert output["allocated_codes"] == ["T2"]
    assert row(output, "T2")["source_health"] is None
    assert row(output, "T2")["window"] is None
    assert row(output, "T1")["status"] == "no storm sampling needed"
    assert not output["notices"]


def test_archive_gaps_break_runs_and_cannot_anchor_storms():
    for gap in ("2026-08-04", "2026-08-27"):
        middle = date.fromisoformat(gap)
        before, after = [(middle + timedelta(days=offset)).isoformat() for offset in (-1, 1)]
        assert plan.wet_runs({before: 25, after: 30}, 20) == [[before], [after]]
        data = fixture(codes=("T1", "T2"))
        for code in ("T1", "T2"):
            data[3][code] = [{"siteCode": code, "date": before, "precipTotalMm": 25},
                             {"siteCode": code, "date": after, "precipTotalMm": 30}]
        output = result(data, mode="replay")
        assert output["storm"]["anchor_date"] == after
        assert output["storm"]["wet_dates"] == [after]
        assert gap in output["archive"]["unknown_dates"]
        assert gap not in output["archive"]["valid_dates"]


def test_replay_rejects_missing_null_duplicate_or_wrong_site_rain():
    for damage in ("missing", "null", "duplicate", "wrong_site"):
        data = fixture(codes=("T1", "T2"))
        if damage == "missing":
            data[3]["T2"] = []
        elif damage == "null":
            data[3]["T2"][0]["precipTotalMm"] = None
        elif damage == "duplicate":
            data[3]["T2"].append(deepcopy(data[3]["T2"][0]))
        else:
            data[3]["T2"][0]["siteCode"] = "T1"
        output = result(data, mode="replay")
        assert output["storm"] is None, damage
        assert output["weather_status"] == "unknown", damage


def test_unknown_forecast_is_not_no_storm():
    data = fixture(codes=("T1", "T2"), rain=0)
    data[4]["TO"]["daily"]["precipitation_sum"][2] = None
    output = result(data)
    assert output["weather_status"] == "unknown"
    assert output["allocated_codes"] == ["T2"]
    assert "unknown" in output["message"].lower()
    data[4]["TO"]["daily_units"]["precipitation_sum"] = "inch"
    assert result(data)["weather_status"] == "unknown"


def test_drafts_require_review_have_no_expiry_and_use_actual_sample_year():
    data = fixture()
    data[1][0]["samplingDate"] = "2024-08-05T00:00:00"
    notice = result(data)["notices"][0]
    assert notice["status"] == "draft"
    assert notice["label"] == "Draft — requires coordinator review"
    assert "2024" in notice["basis"] and "2023" not in notice["basis"]
    assert "people and pets" in notice["text"]
    assert not any("expir" in key.lower() for key in notice)
    assert not result(fixture(scores={"T1": (0.2, 0.2, 0.9)}))["notices"]


def test_duplicate_health_is_excluded_not_silently_selected():
    data = fixture()
    data[1].append(deepcopy(data[1][0]))
    output = result(data)
    assert row(output, "T1")["status"] == "invalid source data"
    assert "duplicate" in row(output, "T1")["reason"].lower()
    assert not output["allocated_codes"]


def test_configuration_validation():
    for key, value in (("RAIN_MM", 0), ("RAIN_MM", True), ("TEST_MIN", 1.1),
                       ("ADVISORY_MIN", -0.1), ("WINDOW_DAYS", 0),
                       ("VISITS_PER_CITY", -1), ("VISITS_PER_CITY", 1.5)):
        rejects(lambda: plan.validate_config({**CONFIG, key: value}))
    rejects(lambda: plan.validate_config({"RAIN_MM": 20}))


def test_live_summary_names_forecast_anchor_and_never_calls_it_observed():
    data = fixture()
    data[4]["TO"]["daily"]["precipitation_sum"] = [0, 0, 0, 0, 0, 0, 25]
    output = plan.build_plan(*data, CONFIG)
    live = output["cities"]["TO"]["modes"]["live"]
    assert "observed" not in live["storm"]["boundary_note"].lower()
    assert "observed" not in live["storm"]["window"]["why"].lower()
    capture = io.StringIO()
    with redirect_stdout(capture):
        plan.print_summary({"cities": {"TO": {"name": "Toulouse", "modes": {"live": live}}}})
    assert "Storm anchor (live): 2026-10-09" in capture.getvalue()


def test_real_cache_modes_anchors_provenance_and_raw_integrity():
    root = ROOT / "data" / "raw"
    sources = json.loads((root / "_manifest.json").read_text(encoding="utf-8"))["sources"]
    before = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in sources}
    data, metadata = plan.load_cache(root)
    snapshot = deepcopy(data)
    output = plan.build_plan(*data, CONFIG, sources=metadata)
    assert data == snapshot, "Planner must not change input values"
    for mode in ("live", "replay"):
        assert sum(len(city["modes"][mode]["sites"]) for city in output["cities"].values()) == 106
    for city in output["cities"].values():
        replay = city["modes"]["replay"]
        assert replay["label"].startswith("REPLAY of real storm on ")
        storm = replay["storm"]
        for site in replay["sites"]:
            for day in storm["wet_dates"]:
                rows = [r for r in data[3][site["code"]] if r["date"] == day]
                assert len(rows) == 1 and rows[0]["precipTotalMm"] >= CONFIG["RAIN_MM"]
                assert storm["rain_mm_by_site_by_date"][site["code"]][day] == rows[0]["precipTotalMm"]
            assert site["provenance"]["roster"]["url"].endswith("/api/sites/all")
        assert storm["anchor_date"] in replay["archive"]["valid_dates"]
        assert not set(storm["wet_dates"]) & {"2026-08-04", "2026-08-27"}
    live = output["cities"]["OS"]["modes"]["live"]
    assert live["storm"]["anchor_date"] == "2026-10-08"
    assert live["storm"]["rain_mm_by_date"]["2026-10-08"] == 42.9
    assert output["cities"]["TO"]["modes"]["live"]["ranking"] == ["T15", "T21", "T24"]
    assert before == {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in sources}


if __name__ == "__main__":
    assert __debug__, "Run without -O: these checks use Python assert statements"
    tests = [value for name, value in globals().copy().items() if name.startswith("test_")]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} assert-based checks passed")
