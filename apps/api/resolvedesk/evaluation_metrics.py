"""Finite-set metrics with explicit denominators; no model self-score is treated as truth."""

import math
import statistics

from sqlalchemy import select

from .evaluation_dataset import SupportCase
from .models import EvaluationCase, GenerationRun


def ratio(numerator, denominator):
    return {
        "numerator": numerator,
        "denominator": denominator,
        "value": numerator / denominator if denominator else None,
    }


def timing(cases, key):
    values = sorted(
        c.metrics[key]
        for c in cases
        if isinstance(c.metrics.get(key), (int, float)) and math.isfinite(c.metrics[key])
    )
    return {
        "count": len(values),
        "median_ms": statistics.median(values) if values else None,
        "p95_ms": values[math.ceil(len(values) * 0.95) - 1] if values else None,
    }


def allocation(db, run):
    rows = db.scalars(
        select(GenerationRun)
        .join(
            EvaluationCase,
            (EvaluationCase.generation_id == GenerationRun.id)
            & (EvaluationCase.workspace_id == GenerationRun.workspace_id)
            & (EvaluationCase.ticket_id == GenerationRun.ticket_id),
        )
        .where(EvaluationCase.workspace_id == run.workspace_id, EvaluationCase.run_id == run.id)
    ).all()
    return {
        "conservative_micros": sum(r.charge_micros for r in rows),
        "generation_attempts": len(rows),
        "measured_completions": sum(
            "input_tokens" in r.usage and "output_tokens" in r.usage for r in rows
        ),
        "input_tokens": sum(r.usage.get("input_tokens", 0) for r in rows),
        "output_tokens": sum(r.usage.get("output_tokens", 0) for r in rows),
        "price_versions": sorted(
            {r.usage["price_version"] for r in rows if "price_version" in r.usage}
        ),
        "note": "Conservative app allocation, including unresolved reservations; not a provider invoice.",
    }


def summarize(db, run):
    cases = db.scalars(
        select(EvaluationCase).where(
            EvaluationCase.workspace_id == run.workspace_id, EvaluationCase.run_id == run.id
        )
    ).all()
    definitions = [SupportCase.model_validate(c.definition) for c in cases]
    by_key = {c.case_key: c for c in cases}
    answerable = [c for c in definitions if c.expected_sources and not c.expected_abstention]
    expected = sum(len(set(c.expected_sources)) for c in answerable)
    hits = sum(
        len(
            set(c.expected_sources) & set((by_key[c.id].retrieval or {}).get("ranked_articles", []))
        )
        for c in answerable
        if c.id in by_key
    )
    live_expected = [
        c
        for c in definitions
        if run.mode == "deepseek_sample" and c.id in run.summary.get("live_case_ids", [])
    ]
    fixture_outputs = [c for c in cases if c.fixture_output]
    provider_outputs = [c for c in cases if c.provider_output]
    fixture_refs = [
        (ref, c)
        for c in fixture_outputs
        for ref in (c.fixture_output or {}).get("citation_ids", [])
    ]
    provider_refs = [
        (ref, c)
        for c in provider_outputs
        for ref in (c.provider_output or {}).get("citation_ids", [])
    ]

    def valid_refs(rows):
        return sum(ref in (case.retrieval or {}).get("citation_ids", []) for ref, case in rows)

    def workflow(rows, kind):
        return sum(
            (getattr(c, kind)["outcome"] == "escalation") == c.definition["expected_abstention"]
            for c in rows
        )

    def abstentions(rows, kind):
        return {
            "expected_and_escalated": sum(
                c.definition["expected_abstention"] and getattr(c, kind)["outcome"] == "escalation"
                for c in rows
            ),
            "unexpected_escalation": sum(
                not c.definition["expected_abstention"]
                and getattr(c, kind)["outcome"] == "escalation"
                for c in rows
            ),
            "expected_but_answered": sum(
                c.definition["expected_abstention"] and getattr(c, kind)["outcome"] == "answer"
                for c in rows
            ),
            "completed_outputs": len(rows),
        }

    split_recall = {}
    for split in ("tuning", "held_out"):
        labels = [c for c in answerable if c.split == split]
        denominator = sum(len(set(c.expected_sources)) for c in labels)
        numerator = sum(
            len(
                set(c.expected_sources)
                & set((by_key[c.id].retrieval or {}).get("ranked_articles", []))
            )
            for c in labels
            if c.id in by_key
        )
        split_recall[split] = {**ratio(numerator, denominator), "answerable_cases": len(labels)}
    return {
        "planned_cases": len(definitions),
        "live_case_ids": run.summary.get("live_case_ids", []),
        "completed_cases": sum(c.status == "completed" for c in cases),
        "split_source_recall_at_5": split_recall,
        "failed_cases": sum(c.status == "failed" for c in cases),
        "tuning_cases": sum(c.split == "tuning" for c in definitions),
        "held_out_cases": sum(c.split == "held_out" for c in definitions),
        "source_recall_at_5": {
            **ratio(hits, expected),
            "answerable_cases": len(answerable),
            "definition": "Retrieved expected source labels / all expected source labels in planned answerable cases. Unfinished cases contribute zero hits.",
        },
        "fixture": {
            "outputs": len(fixture_outputs),
            "citation_validity": ratio(valid_refs(fixture_refs), len(fixture_refs)),
            "workflow_match": ratio(workflow(fixture_outputs, "fixture_output"), len(definitions)),
            "abstention": abstentions(fixture_outputs, "fixture_output"),
            "is_ai_quality": False,
        },
        "provider": {
            "planned_outputs": len(live_expected),
            "outputs": len(provider_outputs),
            "citation_validity": ratio(valid_refs(provider_refs), len(provider_refs)),
            "workflow_match": ratio(
                workflow(provider_outputs, "provider_output"), len(live_expected)
            ),
            "abstention": abstentions(provider_outputs, "provider_output"),
            "application_escalations": sum(
                bool((c.provider_output or {}).get("usage", {}).get("escalation_template_applied"))
                for c in provider_outputs
            ),
        },
        "critical": {
            "workspace_disclosures": sum(
                bool(c.metrics.get("workspace_disclosure")) for c in cases
            ),
            "unapproved_actions": sum(bool(c.metrics.get("unapproved_action")) for c in cases),
            "fixture_observed_cases": len(fixture_outputs),
            "provider_observed_cases": len(provider_outputs),
            "observed_cases": sum(bool(c.metrics.get("critical_checked")) for c in cases),
            "dedicated_isolation_cases": sum(c.private_probe for c in definitions),
            "note": "Observed finite synthetic set only; not a universal safety guarantee.",
        },
        "timing": {
            "retrieval": timing(cases, "retrieval_ms"),
            "fixture": timing(cases, "fixture_ms"),
            "provider_preparation": timing(cases, "provider_ms"),
            "scope": "Worker/domain processing including PostgreSQL; excludes browser rendering. Missing interrupted measurements are not invented.",
        },
        "allocation": allocation(db, run),
        "answer_quality_release_threshold": None,
        "labels": "Author-supplied synthetic expectations, not independent human ground truth.",
    }
