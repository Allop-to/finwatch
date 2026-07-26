from typing import List
import numpy as np
import polars as pl
from pyod.models.iforest import IForest
from .base import BaseDetector, DetectionResult, DetectionContext
from ..features import extract_features


class StatisticalDetector(BaseDetector):
    detector_type = "statistical"
    version = "1.0.0"
    weight = 0.4

    async def detect(self, transactions: pl.DataFrame, context: DetectionContext) -> List[DetectionResult]:
        if transactions.is_empty() or len(transactions) < 5:
            return []

        featured = extract_features(transactions)
        feature_cols = ["amount_zscore", "day_of_week", "is_weekend", "hour_bucket"]
        X = featured.select(feature_cols).to_numpy().astype(np.float64)

        # Isolation Forest
        clf = IForest(contamination=0.1, random_state=42)
        clf.fit(X)
        scores = clf.decision_function(X)
        scores = -scores  # invert so higher = more anomalous
        s_min, s_max = scores.min(), scores.max()
        if s_max - s_min > 1e-8:
            scores = (scores - s_min) / (s_max - s_min)
        else:
            scores = np.zeros_like(scores)

        # IQR on amount
        amounts = featured["amount"].to_numpy()
        q1, q3 = np.percentile(amounts, [25, 75])
        iqr = q3 - q1
        upper = q3 + 1.5 * iqr
        iqr_flags = amounts > upper

        results = []
        for i in range(len(featured)):
            txn_id = int(featured[i, "id"])
            score = float(scores[i])
            reasons = []

            if float(scores[i]) > 0.7:
                reasons.append({
                    "detector": "statistical", "method": "isolation_forest",
                    "score": round(float(scores[i]), 3),
                    "detail": f"交易异常分数 {score:.3f}，超出正常模式",
                })
            if iqr_flags[i]:
                reasons.append({
                    "detector": "statistical", "method": "iqr",
                    "score": 1.0,
                    "detail": f"金额 {amounts[i]:.2f} 超出上四分位边界 {upper:.2f}",
                })

            if reasons:
                severity = "high" if score >= 0.8 else "medium" if score >= 0.5 else "low"
                results.append(DetectionResult(
                    transaction_id=txn_id, detector_type=self.detector_type,
                    severity=severity, anomaly_score=score, reason=reasons,
                ))
        return results
