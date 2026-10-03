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

import fhir_export

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
    assert "antibiotic resistance category 0.90 (highest of 3, relative score)" in site["reason"]
    assert "tied highest" not in site["reason"]


def test_tied_highest_uses_two_decimals_and_keeps_source_precision():
    data = fixture(scores={"T1": (1, 1, 0.3465)}, distances={"T1": 600.125}, rain=24.437)
    site = row(result(data), "T1")
    assert "faecal and pathogen categories 1.00 (tied highest of 3, relative score)" in site["reason"]
    assert "tied highest" in site["reason"]
    assert "faecal category 1 " not in site["reason"]
    assert site["source_health"]["scaledFecalRisk"] == 1
    assert site["source_health"]["scaledPathogenRisk"] == 1
    assert site["source_health"]["scaledArgRisk"] == 0.3465
    assert "sewage works 600.125 m" in site["reason"]
    assert "24.437 mm" in site["reason"]
    paired = row(result(fixture(scores={"T1": (0.2, 0.9, 0.9)})), "T1")
    assert "pathogen and antibiotic resistance categories 0.90 (tied highest of 3, relative score)" in paired["reason"]
    three = row(result(fixture(scores={"T1": (0.8, 0.8, 0.8)})), "T1")
    assert "faecal, pathogen and antibiotic resistance categories 0.80 (tied highest of 3, relative score)" in three["reason"]
    assert three["categories"] == ["faecal", "pathogen"]


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


def test_c5_replay_tie_and_fhir_requests():
    data, metadata = plan.load_cache(ROOT / "data" / "raw")
    output = plan.build_plan(*data, CONFIG, sources=metadata)
    replay = output["cities"]["CO"]["modes"]["replay"]
    site = row(replay, "C5")
    raw = next(item for item in data[1] if item["researchSiteCode"] == "C5")
    assert site["source_health"]["scaledFecalRisk"] == raw["scaledFecalRisk"] == 1
    assert site["source_health"]["scaledPathogenRisk"] == raw["scaledPathogenRisk"] == 1
    assert site["source_health"]["scaledArgRisk"] == raw["scaledArgRisk"]
    assert "faecal and pathogen categories 1.00 (tied highest of 3, relative score)" in site["reason"]
    assert f"sewage works {site['sewage_distance_m']:g} m" in site["reason"]
    rain = replay["storm"]["rain_mm_by_site_by_date"]["C5"][replay["storm"]["anchor_date"]]
    assert f"{rain:g} mm" in site["reason"]
    assert replay["ranking"][0] == "C5"
    fhir_export.attach_requests(output)
    checks, failures, bundle = fhir_export.structural_report(output, "OS", "live", CONFIG["VISITS_PER_CITY"])
    assert not failures, failures
    assert len(checks) == 21 and all(check["passed"] for check in checks)
    assert len(bundle["entry"]) == CONFIG["VISITS_PER_CITY"]
    assert [entry["resource"]["subject"]["identifier"]["value"] for entry in bundle["entry"]] == (
        output["cities"]["OS"]["modes"]["live"]["ranking"][:CONFIG["VISITS_PER_CITY"]])
    request = site["service_request"]
    assert request["reasonCode"][0]["text"] == site["reason"]
    assert "1.00" in request["reasonCode"][0]["text"]
    assert "reference" not in request["subject"]
    coimbra, _, coimbra_bundle = fhir_export.structural_report(output, "CO", "replay", 1)
    assert all(check["passed"] for check in coimbra)
    assert coimbra_bundle["entry"][0]["resource"]["subject"]["identifier"]["value"] == "C5"
    assert "mode=replay; budget=1; city=CO" in coimbra_bundle["meta"]["tag"][0]["display"]


def test_fhir_slice_baseline_window_and_sandbox_reference_policy():
    data = fixture(codes=("T1", "T2", "T3"),
                   scores={"T1": (1, 1, 0.2), "T2": (0.9, 0.1, 0.1)},
                   distances={"T1": 50, "T2": 10, "T3": 5})
    data[1][0]["samplingDate"] = "2024-08-05T00:00:00"
    output = plan.build_plan(*data, {**CONFIG, "VISITS_PER_CITY": 2})
    fhir_export.attach_requests(output)
    checks, failures, bundle = fhir_export.structural_report(output, "TO", "live", 1)
    assert not failures, failures
    assert [entry["resource"]["subject"]["identifier"]["value"] for entry in bundle["entry"]] == ["T1"]
    ranked = output["cities"]["TO"]["modes"]["live"]["ranking"]
    assert ranked[0] == "T1"
    t1 = row(output["cities"]["TO"]["modes"]["live"], "T1")
    assert "based on 2024 results; live" in t1["service_request"]["note"][0]["text"]
    assert "Precautionary: avoid water contact" in t1["service_request"]["note"][0]["text"]
    assert t1["service_request"]["occurrencePeriod"] == {"start": "2026-10-04", "end": "2026-10-05"}
    t3 = row(output["cities"]["TO"]["modes"]["live"], "T3")
    assert "service_request" in t3
    assert t3["code"] not in [entry["resource"]["subject"]["identifier"]["value"] for entry in bundle["entry"]]
    dry = plan.build_plan(*fixture(codes=("T1", "T2"), rain=0), CONFIG)
    fhir_export.attach_requests(dry)
    baseline = row(dry["cities"]["TO"]["modes"]["live"], "T2")
    assert "occurrencePeriod" not in baseline["service_request"]
    assert "no lab result on file; live" in baseline["service_request"]["note"][0]["text"]
    assert "service_request" not in row(dry["cities"]["TO"]["modes"]["live"], "T1")
    empty_checks, empty_failures, empty = fhir_export.structural_report(dry, "TO", "live", 0)
    assert not empty_failures, empty_failures
    assert empty["entry"] == []
    saved = fhir_export.bundle_for(output, "TO", "live", 2)
    posted, notes = fhir_export.apply_location_references(saved, {"T1": ["590", "892"], "T2": ["10"]})
    assert "reference" not in saved["entry"][0]["resource"]["subject"]
    assert "reference" not in posted["entry"][0]["resource"]["subject"]
    assert posted["entry"][1]["resource"]["subject"]["reference"] == "Location/10"
    assert any("Duplicate sandbox Locations for T1: 590, 892" in line for line in notes)
    assert fhir_export.location_ids_from_search({
        "entry": [
            {"resource": {"resourceType": "Location", "id": "590",
                          "identifier": [{"system": fhir_export.SITE_SYSTEM, "value": "C5"}]}},
            {"resource": {"resourceType": "Location", "id": "892",
                          "identifier": [{"system": fhir_export.SITE_SYSTEM, "value": "C5"}]}},
            {"resource": {"resourceType": "Location", "id": "1",
                          "identifier": [{"system": "https://example.invalid", "value": "C5"}]}},
        ]}, "C5") == ["590", "892"]
    broken = deepcopy(output)
    row(broken["cities"]["TO"]["modes"]["live"], "T1")["service_request"]["status"] = "completed"
    _, broken_failures, _ = fhir_export.structural_report(broken, "TO", "live", 1)
    assert any("status is draft" in name for name in broken_failures)
    referenced = deepcopy(output)
    row(referenced["cities"]["TO"]["modes"]["live"], "T1")["service_request"]["subject"]["reference"] = "Location/1"
    _, reference_failures, _ = fhir_export.structural_report(referenced, "TO", "live", 1)
    assert any("no reference field" in name for name in reference_failures)


if __name__ == "__main__":
    assert __debug__, "Run without -O: these checks use Python assert statements"
    tests = [value for name, value in globals().copy().items() if name.startswith("test_")]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} assert-based checks passed")
