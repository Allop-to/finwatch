from typing import List
import polars as pl
from .base import BaseDetector, DetectionResult, DetectionContext


class RuleDetector(BaseDetector):
    detector_type = "rule"
    version = "1.0.0"
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
                hits = transactions.filter(pl.col("amount") > rule["threshold"])
                for row in hits.iter_rows(named=True):
                    results.append(DetectionResult(
                        transaction_id=int(row["id"]), detector_type=self.detector_type,
                        severity="high", anomaly_score=1.0,
                        reason=[{
                            "detector": "rule", "rule_id": rule["name"],
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
                            "severity": "medium",
                            "detail": rule["desc"],
                        }],
                    ))
        return results
