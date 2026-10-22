from typing import List
import csv
import io
from datetime import datetime
from .base import BaseParser, ParsedTransaction


class AlipayParser(BaseParser):
    source_type = "alipay"

    def parse(self, content: str) -> List[ParsedTransaction]:
        reader = csv.DictReader(io.StringIO(content))
        results = []
        for row in reader:
            amount_str = row.get("金额", row.get("金额（元）", "0")).replace(",", "").strip()
            try:
                amount = abs(float(amount_str)) if amount_str else 0.0
            except ValueError:
                amount = 0.0
            income_outcome = row.get("收/支", "")
            # 支付宝账单金额恒为正，方向只能由「收/支」列决定
            txn_type = "income" if "收入" in income_outcome else "expense"
            date_str = row.get("交易时间", row.get("交易创建时间", ""))
            try:
                txn_date = datetime.strptime(date_str.strip(), "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    txn_date = datetime.strptime(date_str.strip(), "%Y-%m-%d %H:%M")
                except ValueError:
                    txn_date = datetime.now()

            merchant = row.get("交易对方", "") or None
            description = row.get("商品说明", row.get("商品名称", "")) or None
            payment_method = row.get("收/支", "") or None

            results.append(ParsedTransaction(
                amount=amount, type=txn_type, transaction_date=txn_date,
                merchant=merchant, description=description,
                payment_method=payment_method, raw_row=dict(row),
            ))
        return results
