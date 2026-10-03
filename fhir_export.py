"""Build draft FHIR R4 ServiceRequests from plan.json. No network unless --post.

The OneAquaHealth IG (hl7-eu/oah, master, checked 2026-10-04) declares
GroupOah, LibraryOah, LocationOah, ObservationHealthMeasureOah,
ObservationIndicatorsOah, ObservationWithCompOah, and SpecimenOah.
None of its 61 FSH files mentions ServiceRequest or Task, so these resources
use base FHIR R4 ServiceRequest and do not claim an OneAquaHealth profile.
"""

import argparse
from copy import deepcopy
import json
import re
import sys
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from fetch import utc_now, write_json

ROOT = Path(__file__).resolve().parent
SITE_SYSTEM = "https://api.enora-oah.eu/api/sites"
CODE_SYSTEM = "urn:afterstorm:assessment-category"
EXPORT_SYSTEM = "urn:afterstorm:export"
PROFILE_SYSTEM = "urn:afterstorm:profile-choice"
SANDBOX = "https://sandbox.hl7europe.eu/oneaquahealth/fhir"
# Local namespace for stable proposal URNs. Not an HL7 identifier.
PROPOSAL_NAMESPACE = uuid.UUID("8f1c0a4e-6b2d-4c7a-9e15-3d6a7b8c9d01")
CATEGORY_CODES = {
    "faecal": "faecal",
    "pathogen": "pathogen",
    "antibiotic resistance": "antibiotic-resistance",
}
DATE_ONLY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
URN_UUID = re.compile(r"^urn:uuid:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
RATING_WORDS = re.compile(r"\b(Good|Moderate|Poor)\b")
PROFILE_NOTE = (
    "Checked hl7-eu/oah master input/fsh on 2026-10-04: 61 FSH files declare "
    "GroupOah, LibraryOah, LocationOah, ObservationHealthMeasureOah, "
    "ObservationIndicatorsOah, ObservationWithCompOah, and SpecimenOah. "
    "No line contained ServiceRequest or Task. Resources are base FHIR R4 "
    "ServiceRequest, not an OneAquaHealth profile, and are not sandbox-certified."
)
PROFILE_TAG = {
    "system": PROFILE_SYSTEM,
    "code": "base-r4-servicerequest",
    "display": "No OneAquaHealth ServiceRequest or Task profile in hl7-eu/oah; base FHIR R4 ServiceRequest",
}
NOT_CHECKED = (
    "HL7 validator jar was not downloaded and was not run.",
    "OneAquaHealth profile conformance was not claimed; the IG has no ServiceRequest or Task profile.",
    "sandbox $validate was not called and is not certification.",
)


def proposal_url(city_id, mode, code):
    return "urn:uuid:" + str(uuid.uuid5(PROPOSAL_NAMESPACE, f"{city_id}|{mode}|{code}"))


def note_text(site, mode):
    if site.get("sample_date"):
        lead = f"precautionary; based on {site['sample_date'][:4]} results; {mode}"
    else:
        lead = f"precautionary; no lab result on file; {mode}"
    parts = [lead, "Draft proposal only. A person approves it before any sampling."]
    notice = site.get("draft_notice")
    if notice:
        parts.extend((notice["label"], notice["text"], notice["basis"], notice["review"],
                      "The draft notice is not completed and has not been sent."))
    return " ".join(parts)


def codeable_concept(site):
    coding = []
    for label in site["categories"]:
        token = CATEGORY_CODES.get(label)
        if token is None:
            raise ValueError(f"No local assessment code for {label}")
        coding.append({"system": CODE_SYSTEM, "code": token, "display": label})
    if site["action"] == "first baseline assessment":
        text = "First baseline assessment: " + ", ".join(site["categories"])
    else:
        text = "New assessment: " + ", ".join(site["categories"])
    return {"text": text, "coding": coding}


def build_service_request(city_id, mode, site):
    resource = {
        "resourceType": "ServiceRequest",
        "status": "draft",
        "intent": "proposal",
        "subject": {"identifier": {"system": SITE_SYSTEM, "value": site["code"]},
                    "display": site.get("name") or site["code"]},
        "code": codeable_concept(site),
        "reasonCode": [{"text": site["reason"]}],
        "note": [{"text": note_text(site, mode)}],
    }
    window = site.get("window")
    if window:
        resource["occurrencePeriod"] = {"start": window["start_date"], "end": window["end_date"]}
    return proposal_url(city_id, mode, site["code"]), resource


def attach_requests(plan):
    """Store one ServiceRequest on every ranked site. Unranked sites stay without one."""
    for city_id, city in plan["cities"].items():
        for mode, mode_plan in city["modes"].items():
            by_code = {site["code"]: site for site in mode_plan["sites"]}
            for site in mode_plan["sites"]:
                site.pop("service_request", None)
                site.pop("service_request_full_url", None)
            for code in mode_plan["ranking"]:
                site = by_code[code]
                full_url, resource = build_service_request(city_id, mode, site)
                site["service_request_full_url"] = full_url
                site["service_request"] = resource
    plan["fhir"] = {
        "profile": "http://hl7.org/fhir/StructureDefinition/ServiceRequest",
        "profile_note": PROFILE_NOTE,
        "profile_tag": dict(PROFILE_TAG),
        "code_system": CODE_SYSTEM,
        "subject_identifier_system": SITE_SYSTEM,
        "built_by": "fhir_export.py",
        "reference_policy": (
            "Saved resources omit subject.reference. An approved --post may add "
            "Location/{id} only when the sandbox returns exactly one Location "
            "with this site identifier. Duplicate Locations are logged and not chosen."
        ),
    }
    return plan


def bundle_for(plan, city_id, mode, budget):
    if isinstance(budget, bool) or not isinstance(budget, int) or budget < 0:
        raise ValueError("budget must be an integer >= 0")
    mode_plan = plan["cities"][city_id]["modes"][mode]
    by_code = {site["code"]: site for site in mode_plan["sites"]}
    selected = []
    for code in mode_plan["ranking"][:budget]:
        site = by_code[code]
        if "service_request" not in site:
            raise ValueError(f"Ranked site {code} has no ServiceRequest; attach requests first")
        selected.append(site)
    return {
        "resourceType": "Bundle",
        "type": "transaction",
        "meta": {"tag": [
            {"system": EXPORT_SYSTEM, "code": f"{mode}-budget-{budget}",
             "display": f"mode={mode}; budget={budget}; city={city_id}"},
            dict(PROFILE_TAG),
        ]},
        "entry": [{
            "fullUrl": site["service_request_full_url"],
            "resource": site["service_request"],
            "request": {"method": "POST", "url": "ServiceRequest"},
        } for site in selected],
    }


def iter_ranked(plan):
    for city_id, city in plan["cities"].items():
        for mode, mode_plan in city["modes"].items():
            by_code = {site["code"]: site for site in mode_plan["sites"]}
            for code in mode_plan["ranking"]:
                site = by_code[code]
                yield city_id, mode, site, site.get("service_request")


def iter_unranked(plan):
    for city in plan["cities"].values():
        for mode_plan in city["modes"].values():
            ranked = set(mode_plan["ranking"])
            for site in mode_plan["sites"]:
                if site["code"] not in ranked:
                    yield site


def _where(city_id, mode, site):
    return f"{city_id}/{mode}/{site['code']}"


def _statuses(value, found):
    if isinstance(value, dict):
        if "resourceType" in value:
            found.append(("resourceType", value["resourceType"]))
        if "status" in value:
            found.append(("status", value["status"]))
        for child in value.values():
            _statuses(child, found)
    elif isinstance(value, list):
        for child in value:
            _statuses(child, found)


def _text_fields(resource):
    texts = [resource.get("code", {}).get("text", "")]
    texts.extend(item.get("text", "") for item in resource.get("reasonCode") or [])
    texts.extend(item.get("text", "") for item in resource.get("note") or [])
    return texts


def structural_report(plan, city_id, mode, budget):
    """Return (checks, failures, bundle). Each check records exactly what it compared."""
    bundle = bundle_for(plan, city_id, mode, budget)
    ranked = list(iter_ranked(plan))
    mode_plan = plan["cities"][city_id]["modes"][mode]
    expected_codes = mode_plan["ranking"][:budget]
    by_code = {site["code"]: site for site in mode_plan["sites"]}
    checks = []

    def add(name, bad, ok_detail):
        checks.append({"name": name, "passed": not bad,
                       "detail": ok_detail if not bad else "; ".join(bad[:8])})

    missing = [_where(c, m, s) for c, m, s, r in ranked
               if not isinstance(r, dict) or r.get("resourceType") != "ServiceRequest"]
    add("Every ranked site has resourceType ServiceRequest", missing,
        f"{len(ranked)} ranked sites")

    bad_status = [_where(c, m, s) for c, m, s, r in ranked
                  if not isinstance(r, dict) or r.get("status") != "draft"]
    add("Every ServiceRequest status is draft", bad_status, f"{len(ranked)} status fields")

    bad_intent = [_where(c, m, s) for c, m, s, r in ranked
                  if not isinstance(r, dict) or r.get("intent") != "proposal"]
    add("Every ServiceRequest intent is proposal", bad_intent, f"{len(ranked)} intent fields")

    bad_system = []
    bad_value = []
    bad_reference = []
    for c, m, s, r in ranked:
        subject = r.get("subject") if isinstance(r, dict) else None
        identifier = subject.get("identifier") if isinstance(subject, dict) else None
        if not isinstance(identifier, dict) or identifier.get("system") != SITE_SYSTEM:
            bad_system.append(_where(c, m, s))
        elif identifier.get("value") != s["code"]:
            bad_value.append(f"{_where(c, m, s)} value={identifier.get('value')!r}")
        if not isinstance(subject, dict) or "reference" in subject:
            bad_reference.append(_where(c, m, s))
    for index, entry in enumerate(bundle.get("entry") or []):
        subject = (entry.get("resource") or {}).get("subject") or {}
        if "reference" in subject:
            bad_reference.append(f"bundle entry {index}")
    add("subject.identifier.system is https://api.enora-oah.eu/api/sites", bad_system,
        f"{len(ranked)} identifiers")
    add("subject.identifier.value equals the site code", bad_value, f"{len(ranked)} site codes")
    add("Saved ServiceRequest.subject has no reference field", bad_reference,
        f"{len(ranked)} saved subjects and {len(bundle.get('entry') or [])} bundle entries")

    bad_code = []
    bad_text = []
    for c, m, s, r in ranked:
        concept = r.get("code") if isinstance(r, dict) else None
        expected = [{"system": CODE_SYSTEM, "code": CATEGORY_CODES[label], "display": label}
                    for label in s["categories"]]
        if not isinstance(concept, dict) or concept.get("coding") != expected:
            bad_code.append(_where(c, m, s))
        if not isinstance(concept, dict) or not isinstance(concept.get("text"), str) or not concept["text"].strip():
            bad_text.append(_where(c, m, s))
    add("code is one CodeableConcept; coding system is urn:afterstorm:assessment-category; "
        "codes and displays match the site categories in order", bad_code, f"{len(ranked)} code elements")
    add("code.text is a non-empty string", bad_text, f"{len(ranked)} code.text values")

    bad_period = []
    for c, m, s, r in ranked:
        period = r.get("occurrencePeriod") if isinstance(r, dict) else None
        window = s.get("window")
        if window is None:
            if period is not None:
                bad_period.append(f"{_where(c, m, s)} has a period without a window")
            continue
        start, end = (period or {}).get("start"), (period or {}).get("end")
        if (not isinstance(period, dict) or set(period) != {"start", "end"}
                or start != window["start_date"] or end != window["end_date"]
                or not DATE_ONLY.fullmatch(start or "") or not DATE_ONLY.fullmatch(end or "")):
            bad_period.append(f"{_where(c, m, s)} period={period!r}")
    add("occurrencePeriod is date-only and matches the site window, or is omitted when the site has no window",
        bad_period, f"{len(ranked)} windows compared")

    bad_reason = []
    for c, m, s, r in ranked:
        reasons = r.get("reasonCode") if isinstance(r, dict) else None
        if (not isinstance(reasons, list) or len(reasons) != 1 or reasons[0].get("text") != s["reason"]):
            bad_reason.append(_where(c, m, s))
    add("reasonCode has one text entry equal to the site reason", bad_reason,
        f"{len(ranked)} reason texts")

    bad_note = []
    for c, m, s, r in ranked:
        notes = r.get("note") if isinstance(r, dict) else None
        text = notes[0].get("text") if isinstance(notes, list) and len(notes) == 1 else ""
        if "precautionary" not in text or f"; {m}" not in text:
            bad_note.append(f"{_where(c, m, s)} missing precautionary or mode")
            continue
        if s.get("sample_date"):
            year = s["sample_date"][:4]
            if f"based on {year} results" not in text:
                bad_note.append(f"{_where(c, m, s)} missing {year}")
        elif "no lab result on file" not in text:
            bad_note.append(f"{_where(c, m, s)} missing baseline wording")
    add("note contains precautionary, the mode, and the sample year when a sample date exists; "
        "baselines say no lab result", bad_note, f"{len(ranked)} notes")

    bad_notice = []
    watched = [r for *_, r in ranked if isinstance(r, dict)]
    watched.extend(entry.get("resource") for entry in bundle.get("entry") or [])
    for c, m, s, r in ranked:
        notice = s.get("draft_notice")
        if not notice:
            continue
        text = ((r.get("note") or [{}])[0].get("text")) if isinstance(r, dict) else ""
        if notice["text"] not in text or notice["label"] not in text:
            bad_notice.append(f"{_where(c, m, s)} notice text missing from note")
    found = []
    for resource in watched:
        _statuses(resource, found)
    if any(kind == "resourceType" and value == "Communication" for kind, value in found):
        bad_notice.append("Communication resource present")
    other_status = sorted({value for kind, value in found if kind == "status" and value != "draft"})
    if other_status:
        bad_notice.append("status other than draft: " + ", ".join(other_status))
    add("A draft notice, when present, is copied into the note; no Communication resource exists; "
        "every status field is draft", bad_notice, f"{len(watched)} resources walked for status")

    bad_ratings = []
    for c, m, s, r in ranked:
        if not isinstance(r, dict):
            bad_ratings.append(_where(c, m, s))
            continue
        for text in _text_fields(r):
            hit = RATING_WORDS.search(text or "")
            if hit:
                bad_ratings.append(f"{_where(c, m, s)} contains {hit.group(0)}")
                break
    add("code.text, reasonCode text, and note text do not contain the whole words Good, Moderate, or Poor",
        bad_ratings, f"{len(ranked)} resources scanned")

    type_bad = []
    if bundle.get("resourceType") != "Bundle" or bundle.get("type") != "transaction":
        type_bad.append(f"resourceType={bundle.get('resourceType')!r} type={bundle.get('type')!r}")
    add("The export bundle resourceType is Bundle and type is transaction", type_bad,
        f"city={city_id} mode={mode} budget={budget}")

    displays = [tag.get("display", "") for tag in (bundle.get("meta") or {}).get("tag") or []]
    tag_needed = f"mode={mode}; budget={budget}; city={city_id}"
    tag_bad = [] if tag_needed in displays else [f"tags={displays!r}"]
    add("Bundle.meta.tag states the city, mode, and budget", tag_bad, tag_needed)

    entries = bundle.get("entry") or []
    count_bad = [] if len(entries) == len(expected_codes) else [
        f"entries={len(entries)} ranking slice={len(expected_codes)}"]
    add("Bundle entry count equals the ranked sites inside the budget", count_bad,
        f"{len(entries)} entries")

    actual_codes = [((entry.get("resource") or {}).get("subject") or {}).get("identifier", {}).get("value")
                    for entry in entries]
    order_bad = [] if actual_codes == expected_codes else [
        f"bundle={actual_codes} ranking={expected_codes}"]
    add("Bundle entry order matches ranking order", order_bad, " > ".join(expected_codes) or "(empty slice)")

    wrap_bad = []
    for code, entry in zip(expected_codes, entries):
        site = by_code[code]
        request = entry.get("request") or {}
        if request.get("method") != "POST" or request.get("url") != "ServiceRequest":
            wrap_bad.append(f"{code} request={request}")
        if entry.get("fullUrl") != site.get("service_request_full_url") or not URN_UUID.fullmatch(entry.get("fullUrl") or ""):
            wrap_bad.append(f"{code} fullUrl={entry.get('fullUrl')}")
    if len(entries) != len(expected_codes):
        wrap_bad.append("entry count disagrees with the slice")
    add("Each entry is a POST to ServiceRequest and its fullUrl is the site urn:uuid", wrap_bad,
        f"{len(expected_codes)} entries")

    equal_bad = []
    for code, entry in zip(expected_codes, entries):
        if entry.get("resource") != by_code[code].get("service_request"):
            equal_bad.append(code)
    add("Each entry resource equals the ServiceRequest stored on that ranked site", equal_bad,
        f"{len(expected_codes)} resources copied, not rebuilt")

    unranked_bad = [site["code"] for site in iter_unranked(plan)
                    if "service_request" in site or "service_request_full_url" in site]
    unranked_count = sum(1 for _ in iter_unranked(plan))
    add("Sites outside the ranking have no ServiceRequest", unranked_bad,
        f"{unranked_count} unranked sites")

    urls = [site.get("service_request_full_url") for *_, site, _resource in ranked]
    url_bad = []
    if len(urls) != len(set(urls)):
        url_bad.append("duplicate fullUrl")
    malformed = [url for url in urls if not isinstance(url, str) or not URN_UUID.fullmatch(url)]
    if malformed:
        url_bad.append(f"malformed {malformed[:3]}")
    add("fullUrl values are unique urn:uuid URNs", url_bad, f"{len(urls)} URNs")

    failures = [check["name"] for check in checks if not check["passed"]]
    return checks, failures, bundle


def print_report(checks, *, posted=False):
    print("Structural checks (Python, base FHIR R4 field shape):")
    for index, check in enumerate(checks, 1):
        mark = "pass" if check["passed"] else "FAIL"
        print(f"{index}. [{mark}] {check['name']} — {check['detail']}")
    print("Not checked:")
    for line in NOT_CHECKED:
        print(f"- {line}")
    if posted:
        print("- --post ran after these checks. Returned ids are sandbox assignments, not certification.")
    else:
        print("- --post was not run. The public sandbox was not modified.")


def location_ids_from_search(payload, code):
    ids = []
    for entry in (payload or {}).get("entry") or []:
        resource = entry.get("resource") or {}
        if resource.get("resourceType") != "Location" or not resource.get("id"):
            continue
        matched = any(item.get("system") == SITE_SYSTEM and item.get("value") == code
                      for item in resource.get("identifier") or [])
        if matched:
            ids.append(str(resource["id"]))
    return ids


def apply_location_references(bundle, ids_by_code):
    """Copy the bundle and add a reference only when exactly one sandbox id matches."""
    posted = deepcopy(bundle)
    notes = []
    for entry in posted["entry"]:
        code = entry["resource"]["subject"]["identifier"]["value"]
        ids = list(ids_by_code.get(code, []))
        if len(ids) == 1:
            entry["resource"]["subject"]["reference"] = f"Location/{ids[0]}"
            notes.append(f"Sandbox Location for {code}: {ids[0]}")
        elif len(ids) > 1:
            notes.append(f"Duplicate sandbox Locations for {code}: {', '.join(ids)}. subject.reference not set.")
        else:
            notes.append(f"No sandbox Location with identifier {SITE_SYSTEM}|{code}. Posting identifier only.")
    return posted, notes


def search_location_ids(code, timeout=30):
    identifier = quote(f"{SITE_SYSTEM}|{code}", safe="")
    url = f"{SANDBOX}/Location?identifier={identifier}&_count=50"
    request = Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/fhir+json"},
                      method="GET")
    with urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return location_ids_from_search(payload, code)


def post_bundle(bundle, timeout=60):
    ids_by_code = {}
    for entry in bundle["entry"]:
        code = entry["resource"]["subject"]["identifier"]["value"]
        ids_by_code[code] = search_location_ids(code, timeout=timeout)
    posted, notes = apply_location_references(bundle, ids_by_code)
    for line in notes:
        print(line)
    body = json.dumps(posted, ensure_ascii=False).encode("utf-8")
    request = Request(SANDBOX, data=body, method="POST", headers={
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/fhir+json",
        "Content-Type": "application/fhir+json",
    })
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            print(f"Sandbox HTTP {response.status}")
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        print(f"Sandbox HTTP {exc.code}", file=sys.stderr)
        print(raw[:4000], file=sys.stderr)
        return 2
    result = json.loads(raw)
    for entry in result.get("entry") or []:
        response = entry.get("response") or {}
        print(f"Posted {response.get('status')} {response.get('location')}")
    return 0 if result.get("resourceType") == "Bundle" else 2


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=ROOT / "web" / "data" / "plan.json")
    parser.add_argument("--bundle", type=Path, default=ROOT / "web" / "data" / "fhir-bundle.json")
    parser.add_argument("--city", default="OS")
    parser.add_argument("--mode", default="live", choices=("live", "replay"))
    parser.add_argument("--budget", type=int, default=None)
    parser.add_argument("--post", action="store_true",
                        help="POST the bundle to the public sandbox. Requires explicit approval.")
    args = parser.parse_args(argv)
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        attach_requests(plan)
        budget = plan["config"]["VISITS_PER_CITY"] if args.budget is None else args.budget
        checks, failures, bundle = structural_report(plan, args.city, args.mode, budget)
        print_report(checks, posted=False)
        if failures:
            print(f"{len(failures)} structural checks failed", file=sys.stderr)
            return 2
        plan["fhir"]["built_at"] = utc_now()
        plan["fhir"]["default_bundle"] = {"city": args.city, "mode": args.mode, "budget": budget,
                                           "file": "web/data/fhir-bundle.json"}
        write_json(args.plan, plan)
        write_json(args.bundle, bundle)
        print(f"Saved {args.plan}")
        print(f"Saved {args.bundle} ({len(bundle['entry'])} ServiceRequests; mode={args.mode}; budget={budget}; city={args.city})")
        if not args.post:
            print("Did not post. Run python fhir_export.py --post only after explicit approval.")
            return 0
        print(f"Posting to {SANDBOX}")
        return post_bundle(bundle)
    except (OSError, ValueError, KeyError, TypeError, URLError, json.JSONDecodeError) as exc:
        print(f"Cannot export FHIR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
