"""Fail-closed validation for researched true-crime episode dossiers.

A dossier is supplied by a human/research workflow; this module does not
invent cases, infer guilt, or treat an allegation as a conviction.
"""
from datetime import date
from urllib.parse import urlparse

ALLOWED_STATUSES = {
    "allegation", "investigation", "charged", "trial", "convicted",
    "acquitted", "appeal", "overturned", "unresolved", "unknown",
}
PRIMARY_TYPES = {"court_record", "official_statement", "official_document"}
REQUIRED = ("case_title", "jurisdiction", "case_status", "as_of_date",
            "timeline", "sources", "claims")


class DossierError(ValueError):
    pass


def validate_dossier(data):
    if not isinstance(data, dict):
        raise DossierError("case dossier must be a JSON object")
    missing = [key for key in REQUIRED if key not in data]
    if missing:
        raise DossierError("missing required dossier fields: " + ", ".join(missing))
    if not str(data["case_title"]).strip() or not str(data["jurisdiction"]).strip():
        raise DossierError("case_title and jurisdiction must be non-empty")
    if data["case_status"] not in ALLOWED_STATUSES:
        raise DossierError("case_status must distinguish legal status; allowed: " +
                           ", ".join(sorted(ALLOWED_STATUSES)))
    try:
        date.fromisoformat(str(data["as_of_date"]))
    except ValueError as exc:
        raise DossierError("as_of_date must be an ISO date (YYYY-MM-DD)") from exc

    timeline = data["timeline"]
    sources = data["sources"]
    claims = data["claims"]
    if not isinstance(timeline, list) or not timeline:
        raise DossierError("timeline must contain dated, sourced events")
    if not isinstance(sources, list) or len(sources) < 2:
        raise DossierError("at least two independent sources are required")
    if not isinstance(claims, list) or not claims:
        raise DossierError("claims must be explicit and source-linked")

    source_ids = set()
    source_types = {}
    for source in sources:
        if not isinstance(source, dict):
            raise DossierError("each source must be an object")
        sid = str(source.get("id", "")).strip()
        url = str(source.get("url", "")).strip()
        publisher = str(source.get("publisher", "")).strip()
        stype = str(source.get("type", "")).strip()
        parsed = urlparse(url)
        if not sid or sid in source_ids:
            raise DossierError("source IDs must be present and unique")
        if parsed.scheme != "https" or not parsed.netloc:
            raise DossierError(f"source {sid} must have a valid HTTPS URL")
        if not publisher or not stype:
            raise DossierError(f"source {sid} needs publisher and type")
        source_ids.add(sid)
        source_types[sid] = stype

    if not any(t in PRIMARY_TYPES for t in source_types.values()):
        raise DossierError("at least one primary source (court/official record) is required")

    for event in timeline:
        if not isinstance(event, dict) or not event.get("date") or not event.get("event"):
            raise DossierError("each timeline event needs date and event")
        refs = event.get("source_ids")
        if not isinstance(refs, list) or not refs or not set(refs) <= source_ids:
            raise DossierError("every timeline event must cite known source IDs")

    for claim in claims:
        if not isinstance(claim, dict) or not str(claim.get("text", "")).strip():
            raise DossierError("each claim needs non-empty text")
        refs = claim.get("source_ids")
        if not isinstance(refs, list) or len(set(refs)) < 2 or not set(refs) <= source_ids:
            raise DossierError("each material claim needs at least two independent source IDs")
        if claim.get("status") not in ALLOWED_STATUSES:
            raise DossierError("each claim must state its legal/evidentiary status")
        if claim.get("status") == "convicted" and not any(
                source_types[sid] in PRIMARY_TYPES for sid in refs):
            raise DossierError("a conviction claim must cite a primary legal source")

    if data.get("victim_safety_review") is not True:
        raise DossierError("victim_safety_review must be explicitly true")
    if data.get("editorial_approval") is not True:
        raise DossierError("editorial_approval must be explicitly true")
    return {"valid": True, "sources": len(sources), "claims": len(claims),
            "timeline_events": len(timeline), "case_status": data["case_status"]}
