"""AfterStorm: verified cached data -> transparent visit proposals. No network calls."""

import argparse
from datetime import date, timedelta
import hashlib
from pathlib import Path
import sys

import fhir_export
from fetch import (decode_json, index_rows, site_sort_key, source_date, utc_now,
                   valid_number, valid_position, validate_forecast,
                   validate_health, validate_sites, validate_urban)

ROOT = Path(__file__).resolve().parent
CATEGORIES = (("scaledFecalRisk", "faecal"), ("scaledPathogenRisk", "pathogen"),
              ("scaledArgRisk", "antibiotic resistance"))
WINDOW_LABEL = "Experimental window (heuristic, not validated)"
WINDOW_REASON = ("Daily totals do not identify when rain stops. The window uses local calendar "
                 "dates after the last qualifying wet day in the selected forecast or archive. It is adjustable and unvalidated; "
                 "the directive's roughly 72 hours describes short-term pollution duration, "
                 "not a sampling protocol or safety clearance.")


def join_labels(labels):
    if len(labels) == 1:
        return labels[0]
    if len(labels) == 2:
        return f"{labels[0]} and {labels[1]}"
    return ", ".join(labels[:-1]) + " and " + labels[-1]


def highest_category_phrase(health):
    """Two-decimal scores. A tie is exact equality of the stored values, in CATEGORIES order."""
    top = max(health[field] for field, _label in CATEGORIES)
    labels = [label for field, label in CATEGORIES if health[field] == top]
    kind = "categories" if len(labels) > 1 else "category"
    relation = "tied highest" if len(labels) > 1 else "highest"
    return f"{join_labels(labels)} {kind} {top:.2f} ({relation} of 3, relative score)"


def validate_config(config):
    expected = {"RAIN_MM", "TEST_MIN", "ADVISORY_MIN", "VISITS_PER_CITY", "WINDOW_DAYS"}
    if not isinstance(config, dict) or set(config) != expected:
        raise ValueError("config.json must contain exactly: " + ", ".join(sorted(expected)))
    if not valid_number(config["RAIN_MM"]) or config["RAIN_MM"] <= 0:
        raise ValueError("RAIN_MM must be a positive finite number")
    for key in ("TEST_MIN", "ADVISORY_MIN"):
        if not valid_number(config[key], high=1):
            raise ValueError(f"{key} must be between 0 and 1")
    for key, minimum in (("VISITS_PER_CITY", 0), ("WINDOW_DAYS", 1)):
        value = config[key]
        if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
            raise ValueError(f"{key} must be an integer >= {minimum}")
    return dict(config)


def load_config(path):
    return validate_config(decode_json(Path(path).read_bytes()))


def load_cache(root):
    """Require provenance and matching raw bytes; never refresh or rewrite sources."""
    root = Path(root)
    manifest = decode_json((root / "_manifest.json").read_bytes())
    sources = manifest.get("sources")
    if not isinstance(sources, dict):
        raise ValueError("Cache manifest has no sources object")

    def read(name, default=None, required=False):
        metadata = sources.get(name)
        path = root / name
        if metadata is None and not path.exists() and not required:
            return default
        if not isinstance(metadata, dict):
            raise ValueError(f"Missing source provenance: {name}")
        body = path.read_bytes()
        if (hashlib.sha256(body).hexdigest() != metadata.get("sha256")
                or len(body) != metadata.get("bytes")):
            raise ValueError(f"Cache bytes disagree with manifest: {name}")
        if not metadata.get("url") or not metadata.get("fetched_at"):
            raise ValueError(f"Incomplete source provenance: {name}")
        return decode_json(body)

    sites = read("sites.json", required=True)
    health = read("health-risks.json", required=True)
    urban = read("urban-parameters.json", required=True)
    validate_sites(sites)
    validate_health(health)
    validate_urban(urban)
    roster, _ = index_rows(sites, "code")
    weather = {code: read(f"weather/{code}.json", default=[]) for code in roster}
    cities = {site["city"]["id"] for site in sites}
    forecasts = {city: read(f"forecasts/{city}.json") for city in cities}
    return (sites, health, urban, weather, forecasts), sources


def wet_runs(daily, threshold):
    """Only present, numeric wet dates join. Missing dates and nulls break a run."""
    runs = []
    previous = None
    for day, rain in sorted(daily.items()):
        if not valid_number(rain) or rain < threshold:
            previous = None
            continue
        current = date.fromisoformat(day)
        if previous is None or current != previous + timedelta(days=1):
            runs.append([])
        runs[-1].append(day)
        previous = current
    return runs


def sampling_window(anchor, days):
    wet_day = date.fromisoformat(anchor)
    return {"start_date": (wet_day + timedelta(days=1)).isoformat(),
            "end_date": (wet_day + timedelta(days=days)).isoformat(),
            "label": WINDOW_LABEL, "why": WINDOW_REASON,
            "source": "https://eur-lex.europa.eu/eli/dir/2006/7/oj"}


def storm_event(run, daily, config):
    after = (date.fromisoformat(run[-1]) + timedelta(days=1)).isoformat()
    following = daily.get(after)
    return {"start_date": run[0], "anchor_date": run[-1], "wet_dates": list(run),
            "threshold_mm": config["RAIN_MM"],
            "next_day_status": ("below threshold" if valid_number(following)
                                and following < config["RAIN_MM"] else "unknown"),
            "boundary_note": ("The next date is absent or unknown; this is the last qualifying wet "
                              "day in the selected data, not confirmation that rain stopped."
                              if not valid_number(following) else
                              "The next daily total is below the configured storm threshold; "
                              "the actual rain-stop time is unknown."),
            "window": sampling_window(run[-1], config["WINDOW_DAYS"])}


def live_weather(forecast, config):
    try:
        validate_forecast(forecast)
    except (ValueError, TypeError, AttributeError):
        return {"weather_status": "unknown", "storm": None, "label": "LIVE",
                "message": "Forecast unavailable or malformed; storm status unknown. Baseline visits only.",
                "forecast_period": None}
    daily = dict(zip(forecast["daily"]["time"], forecast["daily"]["precipitation_sum"]))
    runs = wet_runs(daily, config["RAIN_MM"])
    period = {"start_date": min(daily), "end_date": max(daily),
              "timezone": forecast.get("timezone"), "rain_mm_by_date": daily}
    if runs:
        storm = storm_event(runs[0], daily, config)
        storm["rain_mm_by_date"] = {day: daily[day] for day in runs[0]}
        return {"weather_status": "storm", "storm": storm, "label": "LIVE",
                "message": "First wet-day run in the cached 7-day forecast; one city-centre forecast for all sites.",
                "forecast_period": period}
    unknown = any(not valid_number(value) for value in daily.values())
    return {"weather_status": "unknown" if unknown else "no_storm", "storm": None,
            "label": "LIVE", "forecast_period": period,
            "message": ("Some forecast rain is unknown; a storm cannot be ruled out. Baseline visits only."
                        if unknown else "No storm in the cached 7-day forecast; no storm sampling needed.")}


def archive_weather(weather, codes, config):
    """User-selected policy: every city site must have valid rain >= RAIN_MM."""
    maps = {}
    all_dates = set()
    for code in codes:
        daily = {}
        for item in weather.get(code, []):
            day = source_date(item.get("date"))
            if day is None:
                continue
            rain = item.get("precipTotalMm")
            if (day in daily or item.get("siteCode") != code or not valid_number(rain)):
                daily[day] = None
            else:
                daily[day] = rain
        maps[code] = daily
        all_dates.update(daily)
    if not all_dates:
        calendar = []
    else:
        first, last = date.fromisoformat(min(all_dates)), date.fromisoformat(max(all_dates))
        calendar = [(first + timedelta(days=i)).isoformat() for i in range((last - first).days + 1)]
    # None is an unknown city date, including internal gaps. It is never zero rain.
    daily = {day: (min(maps[code][day] for code in codes)
                   if all(valid_number(maps[code].get(day)) for code in codes) else None)
             for day in calendar}
    runs = wet_runs(daily, config["RAIN_MM"])
    archive = {"valid_dates": [day for day, rain in daily.items() if valid_number(rain)],
               "unknown_dates": [day for day, rain in daily.items() if not valid_number(rain)],
               "policy": "Every city site must have valid rain at or above RAIN_MM on each wet day.",
               "heavy_rain_days": sum(valid_number(rain) and rain >= config["RAIN_MM"] for rain in daily.values())}
    if not runs:
        return {"weather_status": "unknown" if not archive["valid_dates"] else "no_replay_storm",
                "storm": None, "label": "REPLAY — no qualifying archived storm",
                "message": "No complete city-wide archived storm meets the threshold. Baseline visits only.",
                "archive": archive}
    storm = storm_event(runs[-1], daily, config)
    storm["rain_mm_by_site_by_date"] = {
        code: {day: maps[code][day] for day in runs[-1]} for code in codes}
    storm["rain_range_mm_by_date"] = {
        day: {"min": daily[day], "max": max(maps[code][day] for code in codes)} for day in runs[-1]}
    return {"weather_status": "storm", "storm": storm, "archive": archive,
            "label": f"REPLAY of real storm on {storm['anchor_date']}",
            "message": "Most recent archived wet-day run meeting the threshold at every city site; this is a past scenario."}


def source_ref(name, sources):
    metadata = sources.get(name, {})
    return {"file": "data/raw/" + name, "url": metadata.get("url"),
            "fetched_at": metadata.get("fetched_at"), "sha256": metadata.get("sha256")}


def city_plan(sites, labs, parameters, weather_plan, config, duplicates, sources, mode):
    storm = weather_plan["storm"]
    rows = []
    for site in sorted(sites, key=lambda item: site_sort_key(item["code"])):
        code = site["code"]
        health = labs.get(code)
        urban = parameters.get(code, {})
        raw_distance = urban.get("distanceToSewageStations")
        distance = raw_distance if valid_number(raw_distance) and code not in duplicates["urban"] else None
        distance_reason = (f"sewage works {distance:g} m" if distance is not None else
                           "missing sewage distance; ranked last among baseline sites when baseline ordering applies")
        health_day = source_date(health.get("samplingDate")) if health is not None else None
        invalid = []
        if code in duplicates["roster"]:
            invalid.append("duplicate roster code")
        if code in duplicates["health"]:
            invalid.append("duplicate lab records")
        if health is not None:
            invalid += [field for field, _ in CATEGORIES if not valid_number(health.get(field), high=1)]
            if health_day is None:
                invalid.append("missing or invalid sample date")
        profile = (sorted(CATEGORIES, key=lambda pair: -health[pair[0]])
                   if health is not None and not invalid else [])
        dominant = health[profile[0][0]] if profile else None
        row = {"code": code, "name": site.get("name", code), "city_id": site["city"]["id"],
               "position": ({"latitude": site["latitude"], "longitude": site["longitude"]}
                            if valid_position(site) else None),
               "map_note": "" if valid_position(site) else "No coordinates; no map pin. Visits remain possible.",
               "source_health": dict(health) if health is not None else None,
               "sample_date": health_day, "source_sewage_distance_m": raw_distance,
               "sewage_distance_m": distance, "dominant_value": dominant,
               "categories": [], "action": "none", "rank": None,
               "allocation": "not eligible", "window": None, "draft_notice": None,
               "provenance": {"roster": source_ref("sites.json", sources),
                              "health": source_ref("health-risks.json", sources),
                              "urban": source_ref("urban-parameters.json", sources),
                              "rain": source_ref(f"weather/{code}.json" if mode == "replay" else
                                                 f"forecasts/{site['city']['id']}.json", sources)}}
        if invalid:
            row.update(status="invalid source data", reason="Invalid source data: " + ", ".join(invalid))
        elif health is None:
            row.update(status="baseline needed", action="first baseline assessment",
                       categories=[label for _, label in CATEGORIES],
                       reason=f"No lab result; take a first baseline assessment in all three categories; {distance_reason}.",
                       window=storm["window"] if storm else None)
            row["reason"] += (f" {mode.upper()} storm anchor {storm['anchor_date']}; {WINDOW_LABEL}: "
                              f"{storm['window']['start_date']} to {storm['window']['end_date']} inclusive. "
                              + storm["boundary_note"] if storm else " Routine visit; no storm window.")
        elif not storm:
            row.update(status="no storm sampling needed" if weather_plan["weather_status"] == "no_storm"
                       else "no storm assessment scheduled",
                       reason=f"{weather_plan['message']} Existing {health_day[:4]} results are relative categories, not current concentrations.")
        elif dominant < config["TEST_MIN"]:
            row.update(status="low priority this storm",
                       reason=f"{health_day[:4]} result: all three relative categories are below TEST_MIN={config['TEST_MIN']:g}; no storm visit proposed.")
        else:
            categories = [label for field, label in profile[:2] if health[field] >= config["TEST_MIN"]]
            if mode == "replay":
                rain = storm["rain_mm_by_site_by_date"][code][storm["anchor_date"]]
                rain_text = f"{rain:g} mm archived rain at this site on {storm['anchor_date']}"
            else:
                rain = storm["rain_mm_by_date"][storm["anchor_date"]]
                rain_text = f"{rain:g} mm forecast on {storm['anchor_date']}; one city-centre forecast shared by every site"
            row.update(status="sample this storm", action="new category assessment", categories=categories,
                       window=storm["window"],
                       reason=f"{health_day[:4]} result: {highest_category_phrase(health)}; {distance_reason}; {rain_text}. New assessment in {', '.join(categories)}; {WINDOW_LABEL}: {storm['window']['start_date']} to {storm['window']['end_date']} inclusive. {storm['boundary_note']}")
        # Notice eligibility is independent of visit budget and TEST_MIN, but requires a storm and valid lab evidence.
        if storm and health is not None and not invalid and max(health["scaledFecalRisk"], health["scaledPathogenRisk"]) >= config["ADVISORY_MIN"]:
            row["draft_notice"] = {"code": code, "status": "draft",
                                   "label": "Draft — requires coordinator review",
                                   "text": "Precautionary: avoid water contact for people and pets after heavy rain until new results are reviewed.",
                                   "basis": f"Based on {health_day[:4]} relative faecal/pathogen categories and a {mode} storm scenario; current contamination is unknown.",
                                   "review": "The coordinator decides whether to issue the notice and when to lift it."}
        rows.append(row)
    # ponytail: greedy by dominant-risk, upgrade to value-of-information if real lab data arrives
    eligible = [row for row in rows if row["action"] != "none"]
    eligible.sort(key=lambda row: (row["action"] == "first baseline assessment",
                                  -(row["dominant_value"] or 0), row["sewage_distance_m"] is None,
                                  row["sewage_distance_m"] or 0, site_sort_key(row["code"])))
    for rank, row in enumerate(eligible, 1):
        row["rank"] = rank
        row["allocation"] = "allocated" if rank <= config["VISITS_PER_CITY"] else "if capacity allows"
    return {**weather_plan, "sites": rows, "ranking": [row["code"] for row in eligible],
            "allocated_codes": [row["code"] for row in eligible[:config["VISITS_PER_CITY"]]],
            "budget_unit": "1 site visit; all recommended categories collected on that visit",
            "notices": [row["draft_notice"] for row in rows if row["draft_notice"]],
            "excluded": [{"code": row["code"], "reason": row["reason"]} for row in rows
                         if row["status"] == "invalid source data"]}


def build_plan(sites, health, urban, weather, forecasts, config, sources=None):
    config = validate_config(config)
    sources = sources or {}
    roster, roster_duplicates = index_rows(sites, "code")
    labs, lab_duplicates = index_rows(health, "researchSiteCode")
    parameters, urban_duplicates = index_rows(urban, "researchSiteCode")
    duplicates = {"roster": roster_duplicates, "health": lab_duplicates, "urban": urban_duplicates}
    cities = {}
    for site in roster.values():
        city = site["city"]
        entry = cities.setdefault(city["id"], {"city": dict(city), "sites": []})
        if entry["city"] != city:
            raise ValueError(f"Conflicting first-party city metadata: {city['id']}")
        entry["sites"].append(site)
    output = {}
    for city_id, entry in sorted(cities.items()):
        city_sites = entry["sites"]
        codes = [site["code"] for site in city_sites]
        modes = {"live": live_weather(forecasts.get(city_id), config),
                 "replay": archive_weather(weather, codes, config)}
        output[city_id] = {**entry["city"], "modes": {
            mode: city_plan(city_sites, labs, parameters, event, config, duplicates, sources, mode)
            for mode, event in modes.items()}}
    return {"schema_version": 1, "config": config, "cities": output,
            "duplicate_codes": duplicates,
            "unmatched_codes": {"health": sorted(set(labs) - set(roster), key=site_sort_key),
                                "urban": sorted(set(parameters) - set(roster), key=site_sort_key)},
            "sources": sources,
            "limitations": ["Historical relative categories are not concentrations or current health ratings.",
                            "Rain triggers a sampling proposal, not a contamination prediction.",
                            WINDOW_REASON,
                            "Replay is a past scenario; LIVE uses the dated cached city-centre forecast.",
                            "Visit allocation is greedy; thresholds and sewage-distance ordering are prototype policy.",
                            "Notices require coordinator review; no field validation has been performed."]}


def print_summary(output):
    for city in output["cities"].values():
        for mode, value in city["modes"].items():
            print(f"\n{city['name']} | {value['label']}")
            print("  " + value["message"])
            if value["storm"]:
                print(f"  Storm anchor ({mode}): {value['storm']['anchor_date']}")
                print("  " + value["storm"]["boundary_note"])
            for code in value["allocated_codes"]:
                row = next(row for row in value["sites"] if row["code"] == code)
                window = row["window"]
                timing = (f"{window['start_date']} to {window['end_date']} inclusive ({WINDOW_LABEL})"
                          if window else "routine baseline; no storm window")
                print(f"  Visit {row['rank']}: {code} | {row['action']}: {', '.join(row['categories'])} | {timing}")
            print("  Draft notices (coordinator review): " + (", ".join(n["code"] for n in value["notices"]) or "none"))
            print("  Excluded: " + ("; ".join(f"{row['code']}: {row['reason']}" for row in value["excluded"]) or "none"))
            for row in value["sites"]:
                if row["action"] == "first baseline assessment" and row["sewage_distance_m"] is None:
                    print(f"  {row['code']}: {row['reason']}")
            if mode == "replay":
                print(f"  Archive unknown dates: {len(value['archive']['unknown_dates'])}; missing dates break wet-day runs.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config.json")
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data" / "raw")
    parser.add_argument("--output", type=Path, default=ROOT / "web" / "data" / "plan.json")
    args = parser.parse_args(argv)
    try:
        data, sources = load_cache(args.data_dir)
        output = build_plan(*data, load_config(args.config), sources=sources)
        output["generated_at"] = utc_now()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Cannot build plan: {exc}", file=sys.stderr)
        return 2
    print_summary(output)
    try:
        fhir_export.write_export(output, args.output, args.output.parent / "fhir-bundle.json")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Cannot export FHIR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
