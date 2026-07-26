import polars as pl


def extract_features(transactions: pl.DataFrame) -> pl.DataFrame:
    if transactions.is_empty():
        return transactions.with_columns([
            pl.lit(0.0).alias("amount_zscore"),
            pl.lit(0).alias("day_of_week"),
            pl.lit(False).alias("is_weekend"),
            pl.lit(0).alias("hour_bucket"),
            pl.lit(0.0).alias("txn_count_7d"),
        ])

    # Amount z-score per category with cold start protection
    cat_stats = transactions.group_by("category_id").agg([
        pl.col("amount").mean().alias("cat_mean"),
        pl.col("amount").std().alias("cat_std"),
        pl.col("amount").count().alias("cat_count"),
    ])
    txn = transactions.join(cat_stats, on="category_id", how="left")
    txn = txn.with_columns([
        pl.when(pl.col("cat_count") >= 5)
          .then((pl.col("amount") - pl.col("cat_mean")) / pl.col("cat_std"))
          .otherwise(0.0)
          .fill_nan(0.0)
          .alias("amount_zscore"),
    ])

    # Time features
    txn = txn.with_columns([
        pl.col("transaction_date").dt.weekday().alias("day_of_week"),
        pl.col("transaction_date").dt.weekday().is_in([5, 6]).alias("is_weekend"),
        pl.col("transaction_date").dt.hour().alias("hour_bucket"),
    ])

    return txn.drop(["cat_mean", "cat_std", "cat_count"])
