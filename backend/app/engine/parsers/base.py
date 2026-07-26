from typing import Optional, List, Dict, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ParsedTransaction:
    amount: float
    type: str
    transaction_date: datetime
    merchant: Optional[str]
    description: Optional[str]
    payment_method: Optional[str]
    raw_row: dict


class BaseParser(ABC):
    @property
    @abstractmethod
    def source_type(self) -> str: ...

    @abstractmethod
    def parse(self, content: str) -> List[ParsedTransaction]: ...
