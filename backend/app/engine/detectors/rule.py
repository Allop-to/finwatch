from typing import List, Optional
import polars as pl
from .base import BaseDetector, DetectionResult, DetectionContext


class RuleDetector(BaseDetector):
    detector_type = "rule"
    version = "1.1.0"
    weight = 0.4

    HARD_RULES = [
        {
            "name": "single_large_txn", "threshold": 10000, "is_hard": True,
            "desc": "单笔大额消费超过 10,000",
        },
        {
            "name": "night_txn", "hour_start": 23, "hour_end": 5, "is_hard": False,
            "desc": "深夜时段 (23:00-05:00) 消费",
        },
    ]

    async def detect(self, transactions: pl.DataFrame, context: DetectionContext) -> List[DetectionResult]:
        if transactions.is_empty():
            return []

        results = []
        for rule in self.HARD_RULES:
            if rule["name"] == "single_large_txn":
                hits = transactions.filter(
                    (pl.col("amount") > rule["threshold"]) & (pl.col("type") == "expense")
                )
                for row in hits.iter_rows(named=True):
                    results.append(DetectionResult(
                        transaction_id=int(row["id"]), detector_type=self.detector_type,
                        severity="high", anomaly_score=1.0,
                        reason=[{
                            "detector": "rule", "rule_id": rule["name"],
                            "is_hard": True,
                            "severity": "high",
                            "detail": f"单笔消费 {row['amount']:.2f} 超过阈值 {rule['threshold']}",
                        }],
                    ))
            elif rule["name"] == "night_txn":
                hits = transactions.filter(
                    (pl.col("hour_bucket") >= rule["hour_start"]) |
                    (pl.col("hour_bucket") < rule["hour_end"])
                )
                for row in hits.iter_rows(named=True):
                    results.append(DetectionResult(
                        transaction_id=int(row["id"]), detector_type=self.detector_type,
                        severity="medium", anomaly_score=0.7,
                        reason=[{
                            "detector": "rule", "rule_id": rule["name"],
                            "is_hard": False,
                            "severity": "medium",
                            "detail": rule["desc"],
                        }],
                    ))

        # User-defined rules from the detection_rules table (enabled only).
        for rule in getattr(context, "rules", None) or []:
            condition = rule.get("condition") or {}
            if self._is_builtin_duplicate(condition):
                continue
            hits = self._apply_condition(transactions, condition)
            if hits is None:
                continue

            is_hard = bool(rule.get("is_hard_rule"))
            severity = "high" if is_hard else "medium"
            score = 1.0 if is_hard else 0.6
            rule_id = "rule_%s" % rule.get("id", rule.get("name", "custom"))
            for row in hits.iter_rows(named=True):
                results.append(DetectionResult(
                    transaction_id=int(row["id"]), detector_type=self.detector_type,
                    severity=severity, anomaly_score=score,
                    reason=[{
                        "detector": "rule", "rule_id": rule_id,
                        "name": rule.get("name"),
                        "is_hard": is_hard,
                        "severity": severity,
                        "detail": f"命中自定义规则「{rule.get('name', rule_id)}」",
                    }],
                ))
        return results

    def _apply_condition(self, transactions: pl.DataFrame, condition: dict) -> Optional[pl.DataFrame]:
        """Translate a stored rule condition into a Polars filter."""
        field = condition.get("field")
        operator = condition.get("operator")
        value = condition.get("value")

        if field == "amount":
            col = pl.col("amount")
        elif field == "hour":
            if "hour_bucket" in transactions.columns:
                col = pl.col("hour_bucket")
            else:
                col = pl.col("transaction_date").dt.hour()
        elif field == "daily_count":
            txns = transactions.with_columns(
                pl.col("transaction_date").dt.date().alias("_rule_date")
            )
            counts = txns.group_by("_rule_date").len().rename({"len": "daily_count"})
            transactions = txns.join(counts, on="_rule_date", how="left")
            col = pl.col("daily_count")
        else:
            return None

        if operator in ("in", "not in"):
            values = value if isinstance(value, list) else [value]
            expr = col.is_in(values)
            if operator == "not in":
                expr = ~expr
        elif operator == ">":
            expr = col > value
        elif operator == ">=":
            expr = col >= value
        elif operator == "<":
            expr = col < value
        elif operator == "<=":
            expr = col <= value
        elif operator == "==":
            expr = col == value
        elif operator == "!=":
            expr = col != value
        else:
            return None

        return transactions.filter(expr)

    def _is_builtin_duplicate(self, condition: dict) -> bool:
        """Skip seeded defaults that duplicate a built-in rule."""
        field = condition.get("field")
        operator = condition.get("operator")
        value = condition.get("value")
        if field == "amount" and operator in (">", ">=") and value == 10000:
            return True
        if field == "hour" and operator == "in" and set(value or []) == {23, 0, 1, 2, 3, 4, 5}:
            return True
        return False
