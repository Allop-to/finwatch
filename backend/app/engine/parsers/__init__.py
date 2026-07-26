from typing import Dict, Type
from .base import BaseParser, ParsedTransaction
from .alipay import AlipayParser
from .wechat import WechatParser

PARSER_REGISTRY: Dict[str, Type[BaseParser]] = {
    "alipay": AlipayParser,
    "wechat": WechatParser,
}


def get_parser(source_type: str) -> BaseParser:
    parser_cls = PARSER_REGISTRY.get(source_type)
    if not parser_cls:
        raise ValueError(f"Unsupported source type: {source_type}")
    return parser_cls()
