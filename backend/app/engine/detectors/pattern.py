"""PatternDetector: behavioral pattern change detection (Phase 2)."""
import logging
from typing import List
import polars as pl
import numpy as np
from .base import BaseDetector, DetectionResult, DetectionContext

logger = logging.getLogger(__name__)


class PatternDetector(BaseDetector):
    detector_type = "pattern"
    version = "2.0.0"
    weight = 0.2

    FREQ_SPIKE_THRESHOLD = 2.5     # z-score for frequency spike
    MERCHANT_SHIFT_THRESHOLD = 0.6  # proportion of new merchants in period
    SUBSCRIPTION_MERCHANTS = ["订阅", "会员", "VIP", "续费", "月卡", "年卡"]

    async def detect(self, transactions: pl.DataFrame, context: DetectionContext) -> List[DetectionResult]:
        if transactions.is_empty() or len(transactions) < 10:
            return []

        results: List[DetectionResult] = []

        # Ensure datetime column
        if "hour_bucket" not in transactions.columns:
            transactions = transactions.with_columns(
                pl.col("transaction_date").dt.hour().alias("hour_bucket")
            )

        txns = transactions.sort("transaction_date")

        # 1. Category frequency spike detection
        freq_results = self._detect_frequency_spike(txns)
        results.extend(freq_results)

        # 2. New merchant detection
        merchant_results = self._detect_new_merchants(txns)
        results.extend(merchant_results)

        # 3. Subscription anomaly detection
        sub_results = self._detect_subscription_anomaly(txns)
        results.extend(sub_results)

        return results

    def _detect_frequency_spike(self, txns: pl.DataFrame) -> List[DetectionResult]:
        """Detect abnormal frequency increase in any category."""
        results = []
        try:
            # Group by category and 7-day windows
            txns = txns.with_columns(
                pl.col("transaction_date").cast(pl.Date).alias("tx_date")
            )
            max_date = txns["tx_date"].max()
            week_ago = max_date - pl.duration(days=7)
            two_weeks_ago = max_date - pl.duration(days=14)

            recent = txns.filter(pl.col("tx_date") >= week_ago)
            baseline = txns.filter(
                (pl.col("tx_date") >= two_weeks_ago) & (pl.col("tx_date") < week_ago)
            )

            if recent.is_empty() or baseline.is_empty():
                return results

            recent_counts = recent.group_by("category_id").len()
            baseline_counts = baseline.group_by("category_id").len()

            joined = recent_counts.join(baseline_counts, on="category_id", how="inner", suffix="_base")
            if joined.is_empty():
                return results

            # Calculate ratio
            joined = joined.with_columns(
                (pl.col("len") / pl.col("len_base")).alias("ratio")
            )
            spikes = joined.filter(pl.col("ratio") > 2.0)

            for row in spikes.iter_rows(named=True):
                results.append(DetectionResult(
                    transaction_id=None,
                    detector_type=self.detector_type,
                    severity="medium",
                    anomaly_score=min(row["ratio"] / 3.0, 1.0),
                    reason=[{
                        "detector": "pattern",
                        "method": "frequency_spike",
                        "detail": f"分类 {row['category_id']} 近7天消费频次飙升 {row['ratio']:.1f} 倍",
                        "ratio": round(row["ratio"], 1),
                    }],
                ))
        except Exception:
            logger.exception("pattern detection step failed")
        return results

    def _detect_new_merchants(self, txns: pl.DataFrame) -> List[DetectionResult]:
        """Detect transactions with merchants never seen before."""
        results = []
        try:
            if "merchant" not in txns.columns:
                return results

            txns = txns.with_columns(
                pl.col("transaction_date").cast(pl.Date).alias("tx_date")
            )
            max_date = txns["tx_date"].max()
            cutoff = max_date - pl.duration(days=7)

            recent = txns.filter(pl.col("tx_date") >= cutoff)
            historical = txns.filter(pl.col("tx_date") < cutoff)

            if recent.is_empty():
                return results

            known_merchants = set(
                historical.filter(pl.col("merchant").is_not_null())["merchant"].to_list()
            )

            for row in recent.iter_rows(named=True):
                merchant = row.get("merchant")
                if merchant and merchant not in known_merchants and len(known_merchants) > 5:
                    results.append(DetectionResult(
                        transaction_id=int(row["id"]),
                        detector_type=self.detector_type,
                        severity="low",
                        anomaly_score=0.4,
                        reason=[{
                            "detector": "pattern",
                            "method": "new_merchant",
                            "detail": f"首次在 '{merchant}' 消费，这是近7天新增的陌生商户",
                        }],
                    ))
        except Exception:
            logger.exception("pattern detection step failed")
        return results

    def _detect_subscription_anomaly(self, txns: pl.DataFrame) -> List[DetectionResult]:
        """Detect unusual subscription patterns."""
        results = []
        try:
            if "description" not in txns.columns:
                return results

            # Cast/fill nulls first: an all-null column has Null dtype, and
            # str.contains on it raises InvalidOperationError.
            description = pl.col("description").cast(pl.Utf8).fill_null("")
            merchant = (
                pl.col("merchant").cast(pl.Utf8).fill_null("")
                if "merchant" in txns.columns else None
            )

            for keyword in self.SUBSCRIPTION_MERCHANTS:
                match = description.str.contains(keyword)
                if merchant is not None:
                    match = match | merchant.str.contains(keyword)
                subs = txns.filter(match)
                if subs.is_empty():
                    continue

                amounts = subs["amount"].to_numpy()
                if len(amounts) < 2:
                    continue

                mean = np.mean(amounts)
                std = np.std(amounts) or 1.0
                z_scores = np.abs((amounts - mean) / std)

                for i, row in enumerate(subs.iter_rows(named=True)):
                    if z_scores[i] > 2.0:
                        results.append(DetectionResult(
                            transaction_id=int(row["id"]),
                            detector_type=self.detector_type,
                            severity="medium",
                            anomaly_score=min(float(z_scores[i]) / 3.0, 1.0),
                            reason=[{
                                "detector": "pattern",
                                "method": "subscription_spike",
                                "detail": f"订阅/续费类消费金额 ¥{row['amount']:.2f} 异常偏离均值 ¥{mean:.2f}",
                            }],
                        ))
        except Exception:
            logger.exception("pattern detection step failed")
        return results
