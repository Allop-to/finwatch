"""Detection service: orchestrates all detectors, fusion, and optional LLM explanation."""
from typing import List, Dict
import polars as pl
from sqlalchemy.orm import Session
from app.models.transaction import Transaction
from app.models.detection_result import DetectionResult as DRModel
from app.models.detection_rule import DetectionRule
from app.engine.detectors import (
    StatisticalDetector, RuleDetector, PatternDetector, DetectionContext,
)


async def run_detection(
    db: Session, user_id: int = 1, explain: bool = False,
) -> List[DRModel]:
    """Run all detectors and save results. Optionally generate LLM explanations."""
    txn_rows = db.query(Transaction).filter(Transaction.user_id == user_id).all()
    if not txn_rows:
        return []

    df = pl.DataFrame([{
        "id": t.id, "user_id": t.user_id, "amount": abs(t.amount), "type": t.type,
        "category_id": t.category_id, "transaction_date": t.transaction_date,
        "merchant": t.merchant, "description": t.description,
    } for t in txn_rows])

    df = df.with_columns(
        pl.col("transaction_date").dt.hour().alias("hour_bucket")
    )

    db_rules = db.query(DetectionRule).filter(
        DetectionRule.user_id == user_id,
        DetectionRule.is_enabled.is_(True),
    ).all()
    custom_rules = [
        {
            "id": r.id,
            "name": r.name,
            "condition": r.condition or {},
            "is_hard_rule": r.is_hard_rule,
        }
        for r in db_rules
    ]

    context = DetectionContext(
        user_id=user_id, transactions=df, budgets=[], global_baselines={},
        rules=custom_rules,
    )

    detectors = [StatisticalDetector(), RuleDetector(), PatternDetector()]
    all_results: list = []

    for det in detectors:
        try:
            results = await det.detect(df, context)
            all_results.extend(results)
        except Exception:
            pass  # Individual detector failure shouldn't block others

    # Fusion: group by transaction, max(hard_rules, weighted_avg)
    results_by_txn: Dict[int, list] = {}
    for r in all_results:
        if r.transaction_id is not None:
            results_by_txn.setdefault(r.transaction_id, []).append(r)

    txn_rows_by_id = _build_txn_map(txn_rows)

    saved = []
    for txn_id, det_results in results_by_txn.items():
        hard_max = max((
            r.anomaly_score for r in det_results
            if any(
                reason.get("is_hard") or reason.get("rule_id") == "single_large_txn"
                for reason in r.reason
            )
        ), default=0.0)

        weighted_sum = 0.0
        total_weight = 0.0
        for r in det_results:
            w = (
                StatisticalDetector.weight if r.detector_type == "statistical"
                else RuleDetector.weight if r.detector_type == "rule"
                else PatternDetector.weight
            )
            weighted_sum += r.anomaly_score * w
            total_weight += w

        weighted_avg = weighted_sum / total_weight if total_weight > 0 else 0
        final_score = max(hard_max, weighted_avg)
        severity = (
            "high" if final_score >= 0.8 else "medium" if final_score >= 0.5 else "low"
        )

        combined_reasons = []
        for r in det_results:
            combined_reasons.extend(r.reason)

        # Generate LLM explanation if requested
        suggestion = None
        if explain and severity in ("high", "medium"):
            try:
                from app.services.llm_service import explainer
                # Build minimal context for the explainer
                txn_row = txn_rows_by_id.get(txn_id, {})
                suggestion = await explainer.explain(
                    detection_result={
                        "severity": severity,
                        "detector_type": ", ".join(
                            set(r.detector_type for r in det_results)
                        ),
                        "reason": combined_reasons,
                    },
                    transaction_context=txn_row,
                    statistics={},
                )
            except Exception:
                pass

        detector_type = ", ".join(set(r.detector_type for r in det_results))
        # One result per (user, transaction): reruns update in place instead of
        # appending duplicates, which the 30-minute scheduler would otherwise pile up.
        existing = db.query(DRModel).filter(
            DRModel.user_id == user_id,
            DRModel.transaction_id == txn_id,
        ).order_by(DRModel.id).first()

        if existing:
            existing.detector_type = detector_type
            existing.severity = severity
            existing.anomaly_score = round(final_score, 3)
            existing.reason = combined_reasons
            if suggestion is not None:
                existing.suggestion = suggestion
            saved.append(existing)
        else:
            dr = DRModel(
                user_id=user_id, transaction_id=txn_id,
                detector_type=detector_type,
                severity=severity, anomaly_score=round(final_score, 3),
                reason=combined_reasons, suggestion=suggestion,
            )
            db.add(dr)
            saved.append(dr)

    db.commit()
    return saved


def _build_txn_map(txn_rows) -> dict:
    """Build a lookup dict for transaction context."""
    return {
        t.id: {
            "amount": t.amount,
            "merchant": t.merchant,
            "description": t.description,
            "transaction_date": str(t.transaction_date),
        }
        for t in txn_rows
    }
