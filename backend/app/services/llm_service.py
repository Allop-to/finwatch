"""LLM service: Pydantic AI + DeepSeek integration with offline fallback."""
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, field

from jinja2 import Environment, FileSystemLoader, Template
from pathlib import Path

from app.config import settings
from app.engine.preprocess import sanitizer


# --- Rate limiter ---
@dataclass
class RateLimiter:
    """Simple in-memory rate limiter."""
    auto_explain_limit: int = 10    # per hour
    chat_limit: int = 30            # per hour
    _auto_calls: List[float] = field(default_factory=list)
    _chat_calls: List[float] = field(default_factory=list)

    def _prune(self, calls: List[float], window: float = 3600):
        now = time.time()
        return [t for t in calls if now - t < window]

    def can_auto_explain(self) -> bool:
        self._auto_calls = self._prune(self._auto_calls)
        return len(self._auto_calls) < self.auto_explain_limit

    def can_chat(self) -> bool:
        self._chat_calls = self._prune(self._chat_calls)
        return len(self._chat_calls) < self.chat_limit

    def record_auto(self):
        self._auto_calls.append(time.time())

    def record_chat(self):
        self._chat_calls.append(time.time())

    @property
    def auto_used(self) -> int:
        return len(self._prune(self._auto_calls))

    @property
    def chat_used(self) -> int:
        return len(self._prune(self._chat_calls))


rate_limiter = RateLimiter()

# --- Jinja2 offline templates ---
_templates_dir = Path(__file__).parent.parent.parent / "templates" / "fallback"
_jinja_env = Environment(loader=FileSystemLoader(str(_templates_dir)))


def _render_fallback(template_name: str, **kwargs) -> str:
    """Render a Jinja2 fallback template."""
    try:
        tmpl = _jinja_env.get_template(template_name)
        return tmpl.render(**kwargs)
    except Exception:
        return _hardcoded_fallback(**kwargs)


def _hardcoded_fallback(**kwargs) -> str:
    """Absolute last-resort fallback."""
    severity = kwargs.get("severity", "medium")
    amount = kwargs.get("amount", 0)
    sev_text = {"high": "高危", "medium": "中危", "low": "低危"}.get(severity, "异常")
    emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(severity, "⚠️")

    return (
        f"{emoji} 检测到{sev_text}异常消费\\n\\n"
        f"该笔消费金额 ¥{amount:,.2f} 触发了异常检测规则。"
        f"建议核实该笔消费详情，关注近期类似支出模式。"
    )


# --- LLM Client ---
class LLMClient:
    """DeepSeek API client with sanitization and fallback."""

    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.base_url = settings.DEEPSEEK_BASE_URL
        self.enabled = settings.LLM_ENABLED and bool(self.api_key)

    async def chat(self, messages: List[dict], temperature: float = 0.7) -> str:
        """Send a chat request to DeepSeek. Returns response text or raises."""
        if not self.enabled:
            raise LLMNotAvailable("LLM not configured")

        import httpx
        async with httpx.AsyncClient(timeout=30, trust_env=False) as client:
            resp = await client.post(
                f"{self.base_url}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek-v4-flash",
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": 1024,
                },
            )
            if resp.status_code != 200:
                raise LLMNotAvailable(f"DeepSeek API error: {resp.status_code}")
            data = resp.json()
            return data["choices"][0]["message"]["content"]


class LLMNotAvailable(Exception):
    """Raised when LLM is unavailable — triggers offline fallback."""
    pass


# --- Anomaly Explainer ---
class AnomalyExplainer:
    """Generate human-readable anomaly explanations using LLM or fallback."""

    SYSTEM_PROMPT = (
        "你是个人财务分析助手 FinWatch AI。"
        "你的任务是用通俗易懂的语言向用户解释检测到的异常消费。"
        "你必须基于提供的数据进行分析，不要编造信息。"
        "输出结构：先一句话总结，再列出1-3条可能原因，最后给出2-3条可行建议。"
        "使用友好、不评判的语气。"
    )

    async def explain(
        self,
        detection_result: dict,
        transaction_context: dict,
        statistics: dict,
    ) -> str:
        """Generate explanation for an anomaly. Falls back to template if LLM unavailable."""
        severity_text = {"high": "高危", "medium": "中危", "low": "低危"}.get(
            detection_result.get("severity", "medium"), "异常"
        )

        try:
            if not rate_limiter.can_auto_explain():
                return _render_fallback(
                    "anomaly_explanation.md",
                    severity_emoji="🔴",
                    severity_text=severity_text,
                    detector_type=detection_result.get("detector_type", ""),
                    reasons=detection_result.get("reason", []),
                    amount=transaction_context.get("amount", 0),
                    time_context=transaction_context.get("time_context", ""),
                    suggestions=[],
                )

            client = LLMClient()
            context_block = sanitizer.sanitize_for_llm({
                "transactions": [transaction_context],
                "statistics": statistics,
            })

            messages = [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": (
                    f"以下是一笔被标记为{severity_text}的异常消费：\n\n"
                    f"{context_block}\n\n"
                    f"检测详情：{json.dumps(detection_result.get('reason', []), ensure_ascii=False)}\n\n"
                    f"请帮我解读这笔异常消费。"
                )},
            ]

            response = await client.chat(messages)
            rate_limiter.record_auto()
            return response

        except LLMNotAvailable:
            return _render_fallback(
                "anomaly_explanation.md",
                severity_emoji={"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                    detection_result.get("severity", ""), "⚠️"
                ),
                severity_text=severity_text,
                detector_type=detection_result.get("detector_type", ""),
                reasons=detection_result.get("reason", []),
                amount=transaction_context.get("amount", 0),
                time_context=transaction_context.get("time_context", ""),
                suggestions=[],
            )


# --- Chat Manager ---
class ChatManager:
    """Manage interactive LLM conversations with data context."""

    SYSTEM_PROMPT = (
        "你是 FinWatch AI，个人财务数据分析师。"
        "你只能基于提供的消费数据进行分析和回答。"
        "如果数据不足以回答某个问题，请诚实说明。"
        "不要编造数据或做出无依据的推测。"
        "使用友好、专业的语气。"
        "回答简洁，除非用户要求详细分析。"
    )

    def __init__(self):
        self.explainer = AnomalyExplainer()

    async def chat(
        self,
        user_message: str,
        conversation_history: List[dict],
        data_context: dict,
    ) -> str:
        """Handle a chat turn. Returns AI response or fallback message."""
        if not rate_limiter.can_chat():
            return "您本小时的对话次数已达上限（30次/小时），请稍后再试或查看 Reports 页面获取数据报表。"

        try:
            client = LLMClient()
            context_block = sanitizer.sanitize_for_llm(data_context)

            messages = [
                {"role": "system", "content": self.SYSTEM_PROMPT},
            ]
            # Add recent history (last 10 turns)
            for msg in conversation_history[-20:]:
                messages.append(msg)
            messages.append({"role": "user", "content": (
                f"用户问题：{user_message}\n\n"
                f"可用的消费数据上下文：\n{context_block}"
            )})

            response = await client.chat(messages)
            rate_limiter.record_chat()
            return response

        except LLMNotAvailable:
            return (
                "AI 分析服务暂时不可用，请稍后重试。\n\n"
                "您可以先查看 Reports 页面获取数据报表，"
                "或前往 Detection 页面查看最近的异常检测结果。"
            )

    def get_usage_stats(self) -> dict:
        """Return current rate limit usage."""
        return {
            "auto_explain": {
                "used": rate_limiter.auto_used,
                "limit": rate_limiter.auto_explain_limit,
            },
            "chat": {
                "used": rate_limiter.chat_used,
                "limit": rate_limiter.chat_limit,
            },
            "llm_enabled": settings.LLM_ENABLED and bool(settings.DEEPSEEK_API_KEY),
        }


# Singleton
explainer = AnomalyExplainer()
chat_manager = ChatManager()
