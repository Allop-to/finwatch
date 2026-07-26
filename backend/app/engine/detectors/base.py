from typing import Optional, List, Dict, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import polars as pl


@dataclass
class DetectionResult:
    transaction_id: Optional[int]
    detector_type: str
    severity: str
    anomaly_score: float
    reason: List[dict] = field(default_factory=list)


@dataclass
class DetectionContext:
    user_id: int
    transactions: pl.DataFrame
    budgets: List[dict]
    global_baselines: dict


class BaseDetector(ABC):
    @abstractmethod
    async def detect(self, transactions: pl.DataFrame, context: DetectionContext) -> List[DetectionResult]: ...

    @property
    @abstractmethod
    def detector_type(self) -> str: ...

    @property
    @abstractmethod
    def version(self) -> str: ...

    @property
    @abstractmethod
    def weight(self) -> float: ...
