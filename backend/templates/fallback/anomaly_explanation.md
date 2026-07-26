{{ severity_emoji }} 检测到{{ severity_text }}异常消费

{% if detector_type == "rule" %}
**规则命中：**{% for r in reasons %}{% if r.rule_id == "single_large_txn" %}
- 单笔消费 ¥{{ "%.2f"|format(amount) }} 超过了大额交易阈值。请确认该笔消费是否为本人操作，如非本人操作请及时联系银行。{% endif %}{% if r.rule_id == "night_txn" %}
- 该消费发生在深夜时段（{{ time_context }}），请注意夜间消费安全，核实是否为本人操作。{% endif %}{% endfor %}
{% elif detector_type == "statistical" %}
**统计异常：**
- 该笔消费金额 ¥{{ "%.2f"|format(amount) }} 在您的同类消费历史中处于异常高位。
- 建议回顾该笔消费的必要性，考虑是否属于冲动消费。
{% else %}
**综合异常检测：**
- 系统检测到该笔消费存在异常模式，建议核实消费详情。
{% endif %}

{% if suggestions %}
**建议：**
{% for s in suggestions %}
- {{ s }}
{% endfor %}
{% else %}
**建议：**
- 定期检查账单，关注异常支出
- 为常用分类设置预算上限，控制消费
- 大额消费前三思，避免冲动购物
{% endif %}
