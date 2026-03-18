from __future__ import annotations

from abc import ABC, abstractmethod
from ..schema import Chunk, CandidateBundle


class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, chunk: Chunk) -> CandidateBundle:
        raise NotImplementedError
