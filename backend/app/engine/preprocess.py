"""
Data sanitizer for LLM API calls.
All data leaving the local machine to DeepSeek MUST pass through this module.
"""
import re
from typing import List, Dict, Optional


class DataSanitizer:
    """Three-level merchant generalization + PII removal."""

    # Level 1: Prefix dictionary for exact matching
    PREFIX_MAP: Dict[str, str] = {
        # Food delivery
        "美团外卖": "外卖平台-餐饮商户",
        "饿了么": "外卖平台-餐饮商户",
        "美团": "本地生活平台",
        # Ride hailing
        "滴滴出行": "出行平台-打车",
        "滴滴": "出行平台-打车",
        "T3出行": "出行平台-打车",
        "曹操出行": "出行平台-打车",
        # Payment / transfer
        "支付宝-转账": "转账",
        "微信转账": "转账",
        "支付宝红包": "红包/转账",
        # Shopping
        "淘宝": "电商平台",
        "天猫": "电商平台",
        "京东": "电商平台",
        "拼多多": "电商平台",
        # Convenience / supermarket
        "全家": "连锁便利店",
        "罗森": "连锁便利店",
        "7-Eleven": "连锁便利店",
        "便利蜂": "连锁便利店",
        # Coffee / tea
        "星巴克": "咖啡连锁",
        "瑞幸": "咖啡连锁",
        "Manner": "咖啡连锁",
        "喜茶": "茶饮连锁",
        "奈雪": "茶饮连锁",
        "蜜雪冰城": "茶饮连锁",
    }

    # Level 2: Keyword-based industry classification
    KEYWORD_RULES: List[tuple] = [
        (["饭店", "酒楼", "餐厅", "大排档", "小吃", "拉面", "麻辣烫", "火锅", "烧烤", "面馆"], "某餐饮商户"),
        (["超市", "便利店", "小卖部", "百货"], "某零售商户"),
        (["酒店", "宾馆", "民宿", "旅馆"], "某住宿商户"),
        (["加油站", "充电站", "加气站"], "加油站/充电站"),
        (["医院", "门诊", "药房", "药店", "诊所"], "医疗机构"),
        (["电影", "影院", "影城"], "电影院"),
        (["KTV", "酒吧", "网吧", "桌游"], "娱乐场所"),
        (["理发", "美发", "美容", "美甲"], "美容美发"),
        (["健身房", "游泳", "瑜伽"], "健身运动"),
        (["快递", "物流", "顺丰", "中通", "圆通", "韵达"], "快递物流"),
        (["保险", "理财", "基金"], "金融服务"),
    ]

    # Level 3: Regex fallback patterns
    FALLBACK_PATTERNS: List[tuple] = [
        (r"外卖", "外卖平台-餐饮商户"),
        (r"出行|打车|快车|专车|顺风车", "出行服务"),
        (r"超市|便利|商店|百货", "零售商户"),
        (r"转账|红包", "转账"),
        (r"缴费|充值|话费|水电|燃气", "生活缴费"),
        (r"订阅|会员|续费", "订阅服务"),
    ]

    PII_FIELDS = {"bank_card", "id_number", "real_name", "phone", "email", "address", "balance"}
    ALWAYS_REMOVE = {"bank_card", "id_number", "real_name", "balance"}

    def __init__(self):
        pass

    def generalize_merchant(self, name: Optional[str]) -> str:
        """Three-level merchant name generalization."""
        if not name or not name.strip():
            return "未知商户"

        name = name.strip()

        # Level 1: Prefix dictionary
        for prefix, generalized in self.PREFIX_MAP.items():
            if name.startswith(prefix):
                return generalized

        # Level 2: Keyword industry classification
        for keywords, label in self.KEYWORD_RULES:
            if any(kw in name for kw in keywords):
                return label

        # Level 3: Regex fallback
        for pattern, label in self.FALLBACK_PATTERNS:
            if re.search(pattern, name):
                return label

        return "未知商户(已脱敏)"

    def sanitize_transaction(self, txn: dict) -> dict:
        """Sanitize a single transaction for LLM context."""
        safe = {}
        for key, value in txn.items():
            if key in self.ALWAYS_REMOVE:
                continue
            if key == "merchant":
                safe[key] = self.generalize_merchant(value)
            elif key == "description":
                safe[key] = self._sanitize_text(value or "")
            elif key == "address":
                safe[key] = self._fuzzy_location(value or "")
            elif key == "real_name":
                continue
            elif key == "transaction_date":
                safe[key] = self._humanize_datetime(value)
            else:
                safe[key] = value
        return safe

    def sanitize_transactions(self, transactions: List[dict]) -> List[dict]:
        """Sanitize a batch of transactions."""
        return [self.sanitize_transaction(t) for t in transactions]

    def sanitize_for_llm(self, context: dict) -> str:
        """Build a sanitized text block for the LLM prompt."""
        txns = context.get("transactions", [])
        stats = context.get("statistics", {})
        budget = context.get("budget", {})

        lines = ["以下为用户近期消费数据（已脱敏）：", ""]

        if stats:
            lines.append("## 消费统计")
            if "total_expense" in stats:
                lines.append(f"- 总支出: ¥{stats['total_expense']:,.2f}")
            if "top_categories" in stats:
                lines.append("- 主要分类:")
                for cat in stats["top_categories"]:
                    lines.append(f"  - {cat['name']}: ¥{cat['amount']:,.2f}")

        if budget:
            lines.append("")
            lines.append("## 预算情况")
            lines.append(f"- 预算额度: ¥{budget.get('limit', 0):,.2f}")
            lines.append(f"- 已使用: ¥{budget.get('spent', 0):,.2f}")
            lines.append(f"- 使用率: {budget.get('pct', 0)}%")

        if txns:
            lines.append("")
            lines.append("## 相关交易")
            for t in txns[:20]:
                safe = self.sanitize_transaction(t)
                date_str = safe.get("transaction_date", "")
                merchant = safe.get("merchant", "未知")
                amount = safe.get("amount", 0)
                lines.append(f"- {date_str} | {merchant} | ¥{amount:,.2f}")

        return "\n".join(lines)

    def sanitize_aggregated_for_tool(self, rows: List[dict]) -> List[dict]:
        """Double defense: tool output must be aggregated and sanitized."""
        sanitized = []
        for row in rows:
            safe = {}
            for key, value in row.items():
                if key in self.ALWAYS_REMOVE:
                    continue
                if key == "merchant":
                    safe[key] = self.generalize_merchant(value)
                elif key in ("description", "address"):
                    safe[key] = self._sanitize_text(str(value)) if value else None
                else:
                    safe[key] = value
            sanitized.append(safe)
        return sanitized

    def _sanitize_text(self, text: str) -> str:
        """Remove potential PII from free text."""
        # Phone numbers
        text = re.sub(r"1[3-9]\d{9}", "[手机号已隐藏]", text)
        # ID card numbers
        text = re.sub(r"\d{6}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]", "[身份证已隐藏]", text)
        # Email
        text = re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[邮箱已隐藏]", text)
        return text

    def _fuzzy_location(self, address: str) -> str:
        """Reduce address precision to city/district level."""
        if not address:
            return "未知"
        parts = address.split("市", 1)
        if len(parts) > 1:
            return f"{parts[0]}市"
        parts = address.split("区", 1)
        if len(parts) > 1:
            return f"{parts[0]}区"
        return address[:3] + "..." if len(address) > 6 else address

    def _humanize_datetime(self, dt_str: Optional[str]) -> str:
        """Convert ISO datetime to human-readable time pattern."""
        if not dt_str:
            return "未知时间"
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            hour = dt.hour
            month = dt.month
            day = dt.day
            if hour >= 23 or hour < 5:
                period = "深夜"
            elif hour < 8:
                period = "清晨"
            elif hour < 12:
                period = "上午"
            elif hour < 14:
                period = "中午"
            elif hour < 18:
                period = "下午"
            else:
                period = "晚上"
            return f"{month}月{day}日{period}"
        except (ValueError, TypeError):
            return str(dt_str)[:10]


# Singleton
sanitizer = DataSanitizer()
