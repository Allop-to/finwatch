"""Data sanitizer: everything sent to the LLM must be de-identified."""
from app.engine.preprocess import sanitizer


def test_prefix_dict_merchant_is_generalized():
    assert sanitizer.generalize_merchant("美团外卖-川味麻辣烫") == "外卖平台-餐饮商户"
    assert sanitizer.generalize_merchant("滴滴出行-行程单") == "出行平台-打车"


def test_keyword_merchant_is_generalized():
    assert sanitizer.generalize_merchant("老王川菜饭店") == "某餐饮商户"
    assert sanitizer.generalize_merchant("永辉超市") == "某零售商户"


def test_unknown_merchant_is_masked():
    assert sanitizer.generalize_merchant("Zeus Trading Ltd") == "未知商户(已脱敏)"
    assert sanitizer.generalize_merchant(None) == "未知商户"


def test_pii_in_free_text_is_redacted():
    text = "联系我 13800138000 或 test@example.com，身份证 110101199001011234"
    safe = sanitizer._sanitize_text(text)
    assert "13800138000" not in safe
    assert "test@example.com" not in safe
    assert "110101199001011234" not in safe


def test_bank_and_balance_fields_are_removed():
    safe = sanitizer.sanitize_transaction(
        {"amount": 10, "bank_card": "6222021234567890123", "balance": 88888, "id_number": "110101199001011234"}
    )
    assert "bank_card" not in safe
    assert "balance" not in safe
    assert "id_number" not in safe


def test_phone_field_is_removed():
    """PII_FIELDS 声明 phone 属于敏感字段，必须处理。"""
    safe = sanitizer.sanitize_transaction({"amount": 10, "phone": "13800138000"})
    assert "13800138000" not in str(safe), "手机号字段被原样传给 LLM"


def test_email_field_is_removed():
    safe = sanitizer.sanitize_transaction({"amount": 10, "email": "user@example.com"})
    assert "user@example.com" not in str(safe), "邮箱字段被原样传给 LLM"


def test_address_is_fuzzy_matched():
    assert sanitizer._fuzzy_location("北京市朝阳区建国路88号") == "北京市"
    assert sanitizer._fuzzy_location("深圳南山区科技园") == "深圳南山区"


def test_datetime_is_humanized():
    assert sanitizer._humanize_datetime("2026-07-20T02:30:00") == "7月20日深夜"
    assert sanitizer._humanize_datetime("2026-07-20T12:30:00") == "7月20日中午"


def test_sanitize_for_llm_contains_no_raw_merchant():
    block = sanitizer.sanitize_for_llm(
        {
            "transactions": [
                {
                    "amount": 42.5,
                    "merchant": "美团外卖-川味麻辣烫",
                    "description": "午餐",
                    "transaction_date": "2026-07-20T12:30:00",
                }
            ],
            "statistics": {"total_expense": 42.5},
        }
    )
    assert "川味麻辣烫" not in block
    assert "外卖平台-餐饮商户" in block
    assert "42.50" in block


def test_aggregated_tool_output_is_sanitized():
    rows = [{"category": "餐饮", "total": 100, "bank_card": "6222"}]
    safe = sanitizer.sanitize_aggregated_for_tool(rows)
    assert safe == [{"category": "餐饮", "total": 100}]
