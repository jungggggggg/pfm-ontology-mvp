from __future__ import annotations

import re
from typing import List

from .schema import ParsedDocument, Chunk
from .utils import split_sentences


class SimpleChunker:
    def __init__(self, max_chars: int = 1800, overlap_sentences: int = 1):
        self.max_chars = max_chars
        self.overlap_sentences = overlap_sentences

    def chunk(self, doc: ParsedDocument) -> List[Chunk]:
        pages = self._split_by_pages(doc.text)
        chunks: List[Chunk] = []
        global_index = 0
        for page_no, page_text in pages:
            sentences = split_sentences(page_text)
            if not sentences:
                continue
            buffer: List[str] = []
            for sent in sentences:
                candidate = (" ".join(buffer + [sent])).strip()
                if candidate and len(candidate) > self.max_chars and buffer:
                    chunks.append(
                        Chunk(
                            paper_id=doc.paper_id,
                            chunk_id=f"{doc.paper_id}-chunk-{global_index:04d}",
                            text=" ".join(buffer).strip(),
                            source_pages=[page_no],
                        )
                    )
                    global_index += 1
                    buffer = buffer[-self.overlap_sentences :] if self.overlap_sentences else []
                buffer.append(sent)
            if buffer:
                chunks.append(
                    Chunk(
                        paper_id=doc.paper_id,
                        chunk_id=f"{doc.paper_id}-chunk-{global_index:04d}",
                        text=" ".join(buffer).strip(),
                        source_pages=[page_no],
                    )
                )
                global_index += 1
        return chunks

    @staticmethod
    def _split_by_pages(text: str):
        matches = re.split(r"--- PAGE (\d+) ---", text)
        result = []
        i = 1
        while i < len(matches):
            page_no = int(matches[i])
            page_text = matches[i + 1].strip()
            result.append((page_no, page_text))
            i += 2
        return result
