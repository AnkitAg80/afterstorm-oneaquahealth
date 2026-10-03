"""AfterStorm Phase 1: read public sources and cache their unchanged JSON.

Python standard library only. All remote requests are GET requests.
Run `python fetch.py --offline` to inspect the cache without contacting APIs.
"""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_ROOT = "https://api.enora-oah.eu/api"
FORECAST_ROOT = "https://api.open-meteo.com/v1/forecast"
DEFAULT_DATA_DIR = Path(__file__).resolve().parent / "data" / "raw"
RISK_FIELDS = ("scaledFecalRisk", "scaledPathogenRisk", "scaledArgRisk")


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def reject_nonfinite(value):
    raise ValueError(f"Non-standard JSON numeric value: {value}")


def decode_json(body):
    return json.loads(body.decode("utf-8-sig"), parse_constant=reject_nonfinite)


def validate_rows(data):
    if not isinstance(data, list) or any(not isinstance(row, dict) for row in data):
        raise ValueError("Expected a JSON array of records")


def validate_core_rows(data):
    validate_rows(data)
    if not data:
        raise ValueError("Unexpectedly empty core feed; do not infer that records are absent")


def validate_coded_rows(data, field):
    validate_core_rows(data)
    for row in data:
        code = row.get(field)
        if not isinstance(code, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", code):
            raise ValueError(f"Source record lacks a usable {field}")


def validate_sites(data):
    validate_coded_rows(data, "code")
    if any(not isinstance(row.get("city"), dict) for row in data):
        raise ValueError("Roster record lacks its city object")


def validate_health(data):
    validate_coded_rows(data, "researchSiteCode")


def validate_urban(data):
    validate_coded_rows(data, "researchSiteCode")


def validate_forecast(data):
    if not isinstance(data, dict) or not isinstance(data.get("daily"), dict):
        raise ValueError("Expected a forecast with daily data")
    days = data["daily"].get("time")
    rain = data["daily"].get("precipitation_sum")
    if not isinstance(days, list) or not isinstance(rain, list) or len(days) != 7 or len(rain) != 7:
        raise ValueError("Forecast must contain seven dates and seven precipitation values")
    try:
        parsed_days = [date.fromisoformat(day) for day in days]
    except (TypeError, ValueError) as exc:
        raise ValueError("Forecast dates must be ISO calendar dates") from exc
    if any(day != parsed_days[0] + timedelta(days=index) for index, day in enumerate(parsed_days)):
        raise ValueError("Forecast dates must be consecutive and ordered")
    units = data.get("daily_units")
    if not isinstance(units, dict) or units.get("precipitation_sum") != "mm":
        raise ValueError("Forecast precipitation unit is not mm")
    if any(value is not None and not valid_number(value) for value in rain):
        raise ValueError("Forecast precipitation must be nonnegative numbers or null")


def atomic_write(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(body)
    temporary.replace(path)


def write_json(path, value):
    body = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
    atomic_write(path, body)


def fetch_cached(url, path, *, offline=False, previous=None, timeout=20,
                 attempts=3, validate=validate_rows):
    """Return source data and provenance; a failed refresh never destroys a cache."""
    path = Path(path)
    previous = previous or {}
    failure = None
    if not offline:
        for attempt in range(attempts):
            try:
                request = Request(url, headers={"User-Agent": "Mozilla/5.0",
                                               "Accept": "application/json"}, method="GET")
                with urlopen(request, timeout=timeout) as response:
                    body = response.read()
                data = decode_json(body)
                validate(data)
                metadata = {"url": url, "fetched_at": utc_now(), "status": "live",
                            "sha256": hashlib.sha256(body).hexdigest(),
                            "bytes": len(body)}
                atomic_write(path, body)
                return data, metadata
            except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
                failure = f"{type(exc).__name__}: {exc}"
                # Retrying a permanent 4xx cannot repair authorization or a bad URL.
                if isinstance(exc, HTTPError):
                    status = exc.code
                    exc.close()
                    if status not in (408, 429) and status < 500:
                        break
                if attempt + 1 < attempts:
                    time.sleep(min(2, 0.5 * (2 ** attempt)))
    try:
        body = path.read_bytes()
        checksum = hashlib.sha256(body).hexdigest()
        if previous.get("sha256") and previous["sha256"] != checksum:
            raise ValueError(f"Cache checksum disagrees with provenance: {path.name}")
        data = decode_json(body)
        validate(data)
    except (OSError, ValueError) as exc:
        if offline:
            raise ValueError(f"Offline cache is missing or invalid: {path}: {exc}") from exc
        raise ValueError(f"Refresh failed ({failure}); no usable cache for {path.name}: {exc}") from exc
    metadata = dict(previous)
    metadata.update({"url": previous.get("url"),
                     "fetched_at": previous.get("fetched_at"),
                     "status": "offline" if offline else "cache_fallback",
                     "sha256": checksum, "bytes": len(body), "read_at": utc_now()})
    if failure:
        metadata["warning"] = failure
        metadata["requested_url"] = url
    else:
        metadata.pop("warning", None)
        metadata.pop("requested_url", None)
    return data, metadata


def source_date(value):
    if not isinstance(value, str):
        return None
    try:
        if len(value) == 10:
            return date.fromisoformat(value).isoformat()
        return datetime.fromisoformat(value).date().isoformat()
    except ValueError:
        return None


def weather_request_url(code, health_record, end_date):
    start = source_date((health_record or {}).get("samplingDate")) or "2023-01-01"
    query = urlencode({"siteCode": code, "start": start + "T00:00:00Z",
                       "end": end_date + "T00:00:00Z"})
    return API_ROOT + "/resilience-map/weather?" + query


def site_sort_key(code):
    match = re.fullmatch(r"([A-Za-z]+)(\d+)", str(code))
    return (match[1], int(match[2])) if match else (str(code), -1)


def index_rows(rows, field):
    indexed = {}
    duplicates = set()
    for row in rows:
        code = row.get(field)
        if not isinstance(code, str) or not code:
            raise ValueError(f"Source record lacks a usable {field}; absence cannot be inferred")
        if code in indexed:
            duplicates.add(code)
        else:
            indexed[code] = row
    return indexed, sorted(duplicates, key=site_sort_key)


def valid_number(value, low=0, high=None):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and value >= low
            and (high is None or value <= high))


def valid_position(record):
    return (valid_number(record.get("latitude"), -90, 90)
            and valid_number(record.get("longitude"), -180, 180))


def weather_coverage(code, rows):
    days = []
    usable = 0
    invalid_rows = 0
    for row in rows:
        day = source_date(row.get("date"))
        if not day or row.get("siteCode") != code:
            invalid_rows += 1
            continue
        days.append(day)
        if valid_number(row.get("precipTotalMm")):
            usable += 1
    unique_days = sorted(set(days))
    missing_calendar_dates = []
    if unique_days:
        first, last = date.fromisoformat(unique_days[0]), date.fromisoformat(unique_days[-1])
        present = set(unique_days)
        missing_calendar_dates = [(first + timedelta(days=offset)).isoformat()
                                  for offset in range((last - first).days + 1)
                                  if (first + timedelta(days=offset)).isoformat() not in present]
    return {"rows": len(rows), "start": unique_days[0] if unique_days else None,
            "end": unique_days[-1] if unique_days else None,
            "usable_rain_days": usable, "missing_rain_days": len(days) - usable,
            "missing_calendar_dates": missing_calendar_dates,
            "invalid_rows": invalid_rows,
            "duplicate_dates": sorted(day for day, count in Counter(days).items() if count > 1)}


def forecast_is_complete(forecast):
    try:
        validate_forecast(forecast)
    except ValueError:
        return False
    return all(valid_number(value) for value in forecast["daily"]["precipitation_sum"])


def build_join_report(sites, health, urban, weather, forecasts):
    roster, site_duplicates = index_rows(sites, "code")
    labs, lab_duplicates = index_rows(health, "researchSiteCode")
    parameters, urban_duplicates = index_rows(urban, "researchSiteCode")
    missing = {key: [] for key in ("lab_result", "coordinates", "weather",
                                   "sewage_distance", "forecast")}
    coverage = {}
    cities = {}
    invalid_health = {}
    counts = {"roster_sites": len(roster), "sites_with_lab_result": 0,
              "sites_with_coordinates": 0, "sites_with_weather": 0,
              "sites_with_sewage_distance": 0, "sites_with_all_joined_inputs": 0}
    for code in sorted(roster, key=site_sort_key):
        site = roster[code]
        city = site.get("city") or {}
        city_name = city.get("name") or "Unknown city"
        city_counts = cities.setdefault(city_name, {key: 0 for key in counts})
        city_counts["roster_sites"] += 1
        coverage[code] = weather_coverage(code, weather.get(code, []))
        available = {"lab_result": code in labs, "coordinates": valid_position(site),
                     "weather": coverage[code]["usable_rain_days"] > 0,
                     "sewage_distance": valid_number(parameters.get(code, {}).get("distanceToSewageStations")),
                     "forecast": forecast_is_complete(forecasts.get(city.get("id")))}
        for field, present in available.items():
            if not present:
                missing[field].append(code)
            counter = "sites_with_" + field
            if counter in counts and present:
                counts[counter] += 1
                city_counts[counter] += 1
        if all(available.values()):
            counts["sites_with_all_joined_inputs"] += 1
            city_counts["sites_with_all_joined_inputs"] += 1
        if code in labs:
            issues = [field for field in RISK_FIELDS if not valid_number(labs[code].get(field), 0, 1)]
            if not source_date(labs[code].get("samplingDate")):
                issues.append("samplingDate")
            if issues:
                invalid_health[code] = issues
    forecast_summary = {}
    for city_id, forecast in sorted(forecasts.items()):
        daily = forecast["daily"]
        forecast_summary[city_id] = {"timezone": forecast.get("timezone"),
                                     "start": daily["time"][0], "end": daily["time"][-1],
                                     "days": len(daily["time"]),
                                     "usable_rain_days": sum(valid_number(v) for v in daily["precipitation_sum"]),
                                     "missing_rain_dates": [day for day, rain in zip(daily["time"], daily["precipitation_sum"])
                                                            if not valid_number(rain)],
                                     "complete": forecast_is_complete(forecast)}
    return {"generated_at": utc_now(), "counts": counts, "cities": cities,
            "no_lab_result_sites": missing["lab_result"], "missing": missing,
            "duplicate_codes": {"roster": site_duplicates, "health": lab_duplicates,
                                "urban": urban_duplicates},
            "unmatched_codes": {"health": sorted(set(labs) - set(roster), key=site_sort_key),
                                "urban": sorted(set(parameters) - set(roster), key=site_sort_key)},
            "invalid_health_records": invalid_health, "weather_coverage": coverage,
            "weather_gap_sites": [code for code, value in coverage.items() if value["missing_calendar_dates"]],
            "weather_gap_date_counts": dict(sorted(Counter(day for value in coverage.values()
                                                           for day in value["missing_calendar_dates"]).items())),
            "forecast_coverage": forecast_summary,
            "raw_record_counts": {"sites": len(sites), "health": len(health), "urban": len(urban),
                                  "weather": sum(len(rows) for rows in weather.values())}}


def print_report(report):
    print("\nPhase 1 join report", flush=True)
    for key, value in report["counts"].items():
        print(f"  {key}: {value}")
    print("  No lab result: " + (", ".join(report["no_lab_result_sites"]) or "none"))
    for key, codes in report["missing"].items():
        print(f"  Missing {key}: " + (", ".join(codes) or "none"))
    print(f"  Histories with missing calendar dates: {len(report['weather_gap_sites'])}")
    if report["weather_gap_sites"]:
        print("  Sites with archive gaps: " + ", ".join(report["weather_gap_sites"]))
        print("  Absent archive dates (number of sites): " + json.dumps(report["weather_gap_date_counts"], sort_keys=True))
    for name, counts in sorted(report["cities"].items()):
        print(f"  {name}: roster={counts['roster_sites']}, lab={counts['sites_with_lab_result']}, "
              f"coordinates={counts['sites_with_coordinates']}, weather={counts['sites_with_weather']}, "
              f"sewage_distance={counts['sites_with_sewage_distance']}")
    print("  Retrieval: " + json.dumps(report["retrieval_counts"], sort_keys=True))
    for source, codes in report["duplicate_codes"].items():
        if codes:
            print(f"  Duplicate {source} codes: {', '.join(codes)}")
    for source, codes in report["unmatched_codes"].items():
        if codes:
            print(f"  Unmatched {source} codes: {', '.join(codes)}")
    for code, fields in report["invalid_health_records"].items():
        print(f"  Invalid health fields for {code}: {', '.join(fields)}")
    for name, message in report["errors"].items():
        print(f"  Unavailable {name}: {message}", file=sys.stderr)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="Read cached sources only; never contact APIs")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--workers", type=int, choices=range(1, 9), default=8)
    parser.add_argument("--timeout", type=float, default=20, help="Seconds per network attempt")
    args = parser.parse_args(argv)
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    root = args.data_dir.resolve()
    root.mkdir(parents=True, exist_ok=True)
    manifest_path = root / "_manifest.json"
    try:
        manifest = decode_json(manifest_path.read_bytes()) if manifest_path.exists() else {"sources": {}}
        if not isinstance(manifest, dict) or not isinstance(manifest.get("sources"), dict):
            raise ValueError("Manifest must contain a sources object")
    except (OSError, ValueError) as exc:
        print(f"Invalid source manifest: {exc}", file=sys.stderr)
        return 2
    sources = manifest["sources"]
    current_sources = {}
    errors = {}
    manifest["last_run"] = {"started_at": utc_now(), "offline": args.offline,
                            "workers": args.workers}

    def download(name, url, validate=validate_rows):
        return fetch_cached(url, root / name, previous=sources.get(name),
                            offline=args.offline, timeout=args.timeout, validate=validate)

    def collect(name, result):
        data, metadata = result
        sources[name] = metadata
        current_sources[name] = metadata
        write_json(manifest_path, manifest)
        if metadata["status"] == "cache_fallback":
            print(f"Using dated cache for {name}: {metadata['warning']}", flush=True)
        return data

    try:
        sites = collect("sites.json", download("sites.json", API_ROOT + "/sites/all", validate_sites))
        health = collect("health-risks.json", download("health-risks.json", API_ROOT + "/resilience-map/health-risks", validate_health))
        urban = collect("urban-parameters.json", download("urban-parameters.json", API_ROOT + "/resilience-map/urban-parameters", validate_urban))
    except ValueError as exc:
        print(f"Required source unavailable: {exc}", file=sys.stderr)
        return 2
    roster, _ = index_rows(sites, "code")
    labs, _ = index_rows(health, "researchSiteCode")
    if not roster or any(not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", code) for code in roster):
        print("Roster contains no usable codes or an unsafe cache filename", file=sys.stderr)
        return 2
    print(f"Core sources: {len(roster)} roster sites, {len(health)} lab records, {len(urban)} urban records", flush=True)
    weather = {}
    end_date = (datetime.now(timezone.utc).date() + timedelta(days=1)).isoformat()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        jobs = {pool.submit(download, f"weather/{code}.json",
                            weather_request_url(code, labs.get(code), end_date)): code
                for code in sorted(roster, key=site_sort_key)}
        for done, future in enumerate(as_completed(jobs), 1):
            code = jobs[future]
            name = f"weather/{code}.json"
            try:
                weather[code] = collect(name, future.result())
            except ValueError as exc:
                errors[name] = str(exc)
            if done % 10 == 0 or done == len(jobs):
                print(f"Weather histories inspected: {done}/{len(jobs)}", flush=True)
    city_records = {}
    for site in roster.values():
        city = site.get("city") or {}
        city_id = city.get("id")
        if not isinstance(city_id, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", city_id):
            errors[f"city/{site['code']}"] = "Missing or unsafe city id in roster"
            continue
        if city_id in city_records and city_records[city_id] != city:
            errors[f"city/{city_id}"] = "Conflicting first-party city metadata"
        else:
            city_records[city_id] = city
    forecasts = {}
    for city_id, city in sorted(city_records.items()):
        name = f"forecasts/{city_id}.json"
        if not valid_position(city) or f"city/{city_id}" in errors:
            errors[name] = "No consistent first-party city-centre coordinates"
            continue
        query = urlencode({"latitude": city["latitude"], "longitude": city["longitude"],
                           "daily": "precipitation_sum", "forecast_days": 7, "timezone": "auto"})
        try:
            forecasts[city_id] = collect(name, download(name, FORECAST_ROOT + "?" + query, validate_forecast))
            print(f"City forecast inspected: {city['name']} ({city_id})", flush=True)
        except ValueError as exc:
            errors[name] = str(exc)
    report = build_join_report(sites, health, urban, weather, forecasts)
    report["retrieval_counts"] = dict(Counter(meta["status"] for meta in current_sources.values()))
    report["errors"] = errors
    report["cache_directory"] = str(root)
    manifest["last_run"].update({"finished_at": utc_now(), "errors": errors,
                                 "retrieval_counts": report["retrieval_counts"]})
    write_json(manifest_path, manifest)
    write_json(root / "_join-report.json", report)
    print_report(report)
    print(f"  Source provenance: {manifest_path}", flush=True)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
