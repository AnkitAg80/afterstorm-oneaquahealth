"""Phase 1 tests. All fixtures here are synthetic, not project observations."""

import contextlib
import hashlib
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import subprocess
import shutil
import sys
import threading
import unittest
from uuid import uuid4
from urllib.parse import parse_qs, urlsplit

try:
    import fetch
except ModuleNotFoundError as exc:
    if exc.name != "fetch":
        raise
    fetch = None


SITES = [
    {"code": "C1", "name": "Fixture one", "latitude": 40.1,
     "longitude": -8.4, "city": {"id": "CO", "name": "Coimbra",
                                "latitude": 40.2, "longitude": -8.42}},
    {"code": "C2", "name": "Fixture two", "latitude": None,
     "longitude": None, "city": {"id": "CO", "name": "Coimbra",
                                "latitude": 40.2, "longitude": -8.42}},
    {"code": "C3", "name": "Fixture three", "latitude": 40.3,
     "longitude": -8.4, "city": {"id": "CO", "name": "Coimbra",
                                "latitude": 40.2, "longitude": -8.42}},
]
HEALTH = [{"id": 1, "researchSiteCode": "C1",
           "samplingDate": "2023-06-28T00:00:00",
           "scaledFecalRisk": 0.7, "scaledPathogenRisk": 0.4,
           "scaledArgRisk": 0.1, "healthRiskScore": 0.4}]
URBAN = [{"researchSiteCode": "C1", "distanceToSewageStations": 0},
         {"researchSiteCode": "C2", "distanceToSewageStations": None}]
WEATHER = {
    "C1": [{"siteCode": "C1", "date": "2026-09-25", "precipTotalMm": 25.0}],
    "C2": [],
    "C3": [{"siteCode": "C3", "date": "2026-09-25", "precipTotalMm": 0},
           {"siteCode": "C3", "date": "2026-09-26", "precipTotalMm": None}],
}
FORECAST = {"latitude": 40.2, "longitude": -8.42,
            "timezone": "Europe/Lisbon", "utc_offset_seconds": 3600,
            "daily_units": {"time": "iso8601", "precipitation_sum": "mm"},
            "daily": {"time": ["2026-10-03", "2026-10-04", "2026-10-05",
                               "2026-10-06", "2026-10-07", "2026-10-08", "2026-10-09"],
                      "precipitation_sum": [0.0, 2.0, 0.0, 0.0, 1.0, 0.0, 0.0]}}


@contextlib.contextmanager
def temporary_directory():
    root = (Path(__file__).resolve().parent / ".superpowers" / "test-runs").resolve()
    root.mkdir(parents=True, exist_ok=True)
    # Python 3.13+ tempfile uses a Windows private ACL that excludes sandbox tokens.
    # Inherit the project's permissions for these public, synthetic test fixtures.
    tmp = root / uuid4().hex
    tmp.mkdir()
    try:
        yield str(tmp)
    finally:
        if not tmp.resolve().is_relative_to(root):
            raise ValueError("Temporary test directory escaped project scratch space")
        shutil.rmtree(tmp)


@contextlib.contextmanager
def server_responses(responses):
    """Use real local HTTP for retry/cache behavior, with controlled responses."""
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append({"path": self.path, "headers": dict(self.headers)})
            status, body = responses[min(len(requests) - 1, len(responses) - 1)]
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/source", requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


class FetchTests(unittest.TestCase):
    def require_fetch(self):
        self.assertIsNotNone(fetch, "Phase 1 fetch.py has not been implemented")
        return fetch

    def test_transient_http_failure_retries_then_caches_exact_source_bytes(self):
        # Catches a missing retry, wrong UA, or rewriting the original payload.
        module = self.require_fetch()
        body = b'[ { "code": "C1", "name": "source spacing preserved" } ]'
        with temporary_directory() as tmp, server_responses(
            [(503, b'{}'), (200, body)]
        ) as (url, requests):
            path = Path(tmp) / "sites.json"
            payload, metadata = module.fetch_cached(
                url, path, attempts=2, timeout=1, validate=module.validate_rows
            )
            self.assertEqual(payload[0]["code"], "C1")
            self.assertEqual(path.read_bytes(), body)
            self.assertEqual(len(requests), 2)
            self.assertEqual(requests[0]["headers"]["User-Agent"], "Mozilla/5.0")
            self.assertEqual(metadata["status"], "live")
            self.assertEqual(metadata["url"], url)
            self.assertEqual(metadata["sha256"], hashlib.sha256(body).hexdigest())
            self.assertTrue(metadata["fetched_at"].endswith("Z"))

    def test_failed_refresh_preserves_cache_and_original_retrieval_time(self):
        # Catches outage fallback being mislabelled as a freshly obtained source.
        module = self.require_fetch()
        body = b'[{"code":"C1"}]'
        previous = {"url": "https://original.example/data",
                    "fetched_at": "2026-10-02T10:00:00Z",
                    "sha256": hashlib.sha256(body).hexdigest()}
        with temporary_directory() as tmp, server_responses(
            [(503, b'{}')]
        ) as (url, requests):
            path = Path(tmp) / "sites.json"
            path.write_bytes(body)
            payload, metadata = module.fetch_cached(
                url, path, previous=previous, attempts=2, timeout=1,
                validate=module.validate_rows
            )
            self.assertEqual(payload, [{"code": "C1"}])
            self.assertEqual(path.read_bytes(), body)
            self.assertEqual(metadata["status"], "cache_fallback")
            self.assertEqual(metadata["fetched_at"], "2026-10-02T10:00:00Z")
            self.assertEqual(metadata["url"], "https://original.example/data")
            self.assertIn("503", metadata["warning"])
            self.assertEqual(len(requests), 2)

    def test_wrong_shape_never_overwrites_valid_cache(self):
        # Catches a valid-JSON upstream error object replacing a data array.
        module = self.require_fetch()
        original = b'[{"code":"C1"}]'
        with temporary_directory() as tmp, server_responses(
            [(200, b'{"error":"not the expected data"}')]
        ) as (url, _):
            path = Path(tmp) / "sites.json"
            path.write_bytes(original)
            _, metadata = module.fetch_cached(
                url, path, attempts=1, timeout=1, validate=module.validate_rows
            )
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(metadata["status"], "cache_fallback")

    def test_offline_mode_reads_cache_without_contacting_source(self):
        # Catches an offline run attempting network access.
        module = self.require_fetch()
        with temporary_directory() as tmp, server_responses(
            [(200, b'[]')]
        ) as (url, requests):
            path = Path(tmp) / "sites.json"
            path.write_text('[{"code":"C1"}]', encoding="utf-8")
            data, metadata = module.fetch_cached(
                url, path, offline=True, validate=module.validate_rows
            )
            self.assertEqual(data, [{"code": "C1"}])
            self.assertEqual(metadata["status"], "offline")
            self.assertEqual(len(requests), 0)

    def test_offline_mode_rejects_a_cache_that_disagrees_with_its_hash(self):
        # Catches silently using changed data with old provenance metadata.
        module = self.require_fetch()
        with temporary_directory() as tmp:
            path = Path(tmp) / "sites.json"
            path.write_text('[{"code":"C2"}]', encoding="utf-8")
            with self.assertRaises(ValueError):
                module.fetch_cached(
                    "http://127.0.0.1:1/unreachable", path, offline=True,
                    previous={"sha256": hashlib.sha256(b'[]').hexdigest()},
                    validate=module.validate_rows
                )

    def test_join_retains_roster_and_distinguishes_missing_data_from_zero(self):
        # Catches dropping baseline/unpositioned sites or treating zero as absent.
        module = self.require_fetch()
        report = module.build_join_report(SITES, HEALTH, URBAN, WEATHER,
                                          {"CO": FORECAST})
        self.assertEqual(report["counts"]["roster_sites"], 3)
        self.assertEqual(report["counts"]["sites_with_lab_result"], 1)
        self.assertEqual(report["counts"]["sites_with_coordinates"], 2)
        self.assertEqual(report["counts"]["sites_with_weather"], 2)
        self.assertEqual(report["counts"]["sites_with_sewage_distance"], 1)
        self.assertEqual(report["counts"]["sites_with_all_joined_inputs"], 1)
        self.assertEqual(report["no_lab_result_sites"], ["C2", "C3"])
        self.assertEqual(report["missing"]["coordinates"], ["C2"])
        self.assertEqual(report["missing"]["weather"], ["C2"])
        self.assertEqual(report["weather_coverage"]["C3"]["usable_rain_days"], 1)
        self.assertEqual(report["weather_coverage"]["C3"]["missing_rain_days"], 1)

    def test_join_exposes_duplicate_and_unmatched_records(self):
        # Catches duplicate rows or unknown codes being silently merged as valid.
        module = self.require_fetch()
        report = module.build_join_report(
            SITES, HEALTH + HEALTH + [{"researchSiteCode": "T99"}],
            URBAN, WEATHER, {"CO": FORECAST}
        )
        self.assertEqual(report["duplicate_codes"]["health"], ["C1"])
        self.assertEqual(report["unmatched_codes"]["health"], ["T99"])
        self.assertEqual(report["counts"]["sites_with_lab_result"], 1)

    def test_absent_calendar_days_are_reported_without_fabricating_rainfall(self):
        # Catches an absent daily row being hidden by checking only existing rows.
        module = self.require_fetch()
        rows = [{"siteCode": "C1", "date": "2026-09-25", "precipTotalMm": 1.0},
                {"siteCode": "C1", "date": "2026-09-27", "precipTotalMm": None}]
        report = module.build_join_report(SITES, HEALTH, URBAN, {"C1": rows},
                                          {"CO": FORECAST})
        coverage = report["weather_coverage"]["C1"]
        self.assertEqual(coverage.get("missing_calendar_dates"), ["2026-09-26"])
        self.assertEqual(coverage["missing_rain_days"], 1)
        self.assertEqual(coverage["usable_rain_days"], 1)
        self.assertEqual(len(rows), 2)
        self.assertIsNone(rows[1]["precipTotalMm"])

    def test_identifierless_core_responses_never_replace_good_caches(self):
        # Catches upstream error records inventing baseline sites or dropping roster.
        module = self.require_fetch()
        for validator_name, original in [("validate_sites", SITES),
                                          ("validate_health", HEALTH),
                                          ("validate_urban", URBAN)]:
            with self.subTest(feed=validator_name), temporary_directory() as tmp, server_responses(
                [(200, b'[{"error":"Unavailable"}]')]
            ) as (url, _):
                body = json.dumps(original).encode("utf-8")
                path = Path(tmp) / "source.json"
                path.write_bytes(body)
                validator = getattr(module, validator_name, module.validate_core_rows)
                _, metadata = module.fetch_cached(url, path, attempts=1, timeout=1,
                                                  validate=validator)
                self.assertEqual(path.read_bytes(), body)
                self.assertEqual(metadata["status"], "cache_fallback")

    def test_join_rejects_identifierless_health_rows_instead_of_inventing_baselines(self):
        # Catches direct consumers bypassing fetch validation and losing core rows.
        module = self.require_fetch()
        with self.assertRaises(ValueError):
            module.build_join_report(SITES, [{"error": "Unavailable"}], URBAN,
                                     WEATHER, {"CO": FORECAST})

    def test_malformed_or_short_forecast_falls_back_to_the_good_cache(self):
        # Catches false seven-day coverage and an uncaught malformed-units exception.
        module = self.require_fetch()
        short = json.loads(json.dumps(FORECAST))
        short["daily"] = {"time": ["2026-10-03", "2026-10-04"],
                          "precipitation_sum": [0.0, 2.0]}
        bad_date = json.loads(json.dumps(FORECAST))
        bad_date["daily"]["time"][0] = "garbage"
        skipped_date = json.loads(json.dumps(FORECAST))
        skipped_date["daily"]["time"][1] = "2026-10-05"
        bad_units = json.loads(json.dumps(FORECAST))
        bad_units["daily_units"] = None
        for invalid in [short, bad_date, skipped_date, bad_units]:
            with self.subTest(forecast=invalid), temporary_directory() as tmp, server_responses(
                [(200, json.dumps(invalid).encode("utf-8"))]
            ) as (url, _):
                original = json.dumps(FORECAST).encode("utf-8")
                path = Path(tmp) / "forecast.json"
                path.write_bytes(original)
                try:
                    _, metadata = module.fetch_cached(url, path, attempts=1, timeout=1,
                                                      validate=module.validate_forecast)
                except Exception as exc:
                    self.fail(f"Malformed forecast bypassed cache fallback: {type(exc).__name__}: {exc}")
                self.assertEqual(path.read_bytes(), original)
                self.assertEqual(metadata["status"], "cache_fallback")

    def test_null_forecast_rain_is_unknown_not_complete_city_coverage(self):
        # Catches null precipitation becoming a usable forecast/no-storm conclusion.
        module = self.require_fetch()
        forecast = json.loads(json.dumps(FORECAST))
        forecast["daily"]["precipitation_sum"][1] = None
        module.validate_forecast(forecast)
        report = module.build_join_report(SITES, HEALTH, URBAN, WEATHER,
                                          {"CO": forecast})
        self.assertEqual(report["missing"]["forecast"], ["C1", "C2", "C3"])
        self.assertEqual(report["forecast_coverage"]["CO"].get("missing_rain_dates"),
                         ["2026-10-04"])
        self.assertEqual(report["forecast_coverage"]["CO"].get("complete"), False)

    def test_weather_query_uses_sample_date_or_baseline_date_and_z_suffix(self):
        # Catches missing baseline history, a malformed API date, or code encoding.
        module = self.require_fetch()
        sampled = module.weather_request_url("C1", HEALTH[0], "2026-10-04")
        baseline = module.weather_request_url("C2", None, "2026-10-04")
        self.assertEqual(parse_qs(urlsplit(sampled).query)["start"],
                         ["2023-06-28T00:00:00Z"])
        self.assertEqual(parse_qs(urlsplit(baseline).query)["start"],
                         ["2023-01-01T00:00:00Z"])
        self.assertEqual(parse_qs(urlsplit(baseline).query)["end"],
                         ["2026-10-04T00:00:00Z"])
        self.assertEqual(parse_qs(urlsplit(baseline).query)["siteCode"], ["C2"])

    def test_cli_offline_uses_cached_files_and_writes_a_complete_join_report(self):
        # Catches CLI wiring losing sites or requiring APIs for a cached run.
        self.require_fetch()
        with temporary_directory() as tmp:
            root = Path(tmp)
            fixtures = {"sites.json": SITES, "health-risks.json": HEALTH,
                        "urban-parameters.json": URBAN,
                        "forecasts/CO.json": FORECAST}
            fixtures.update({f"weather/{code}.json": rows
                             for code, rows in WEATHER.items()})
            for name, value in fixtures.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(value), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(Path(__file__).with_name("fetch.py")),
                 "--offline", "--data-dir", str(root)],
                capture_output=True, text=True, timeout=10
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads((root / "_join-report.json").read_text())
            self.assertEqual(report["counts"]["roster_sites"], 3)
            self.assertEqual(report["no_lab_result_sites"], ["C2", "C3"])
            self.assertEqual(report["retrieval_counts"], {"offline": 7})
            self.assertIn("C2, C3", result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
