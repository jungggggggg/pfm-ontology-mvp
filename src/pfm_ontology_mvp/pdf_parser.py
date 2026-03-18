from __future__ import annotations

from pathlib import Path
import fitz

from .schema import ParsedDocument
from .utils import write_json
from .settings import PARSED_DIR


class PDFParser:
    def parse(self, pdf_path: Path) -> ParsedDocument:
        doc = fitz.open(pdf_path)
        pages = []
        title = None
        for page_index, page in enumerate(doc, start=1):
            blocks = page.get_text("blocks")
            blocks = sorted(blocks, key=lambda b: (round(b[1], 1), round(b[0], 1)))
            block_texts = []
            for block in blocks:
                text = block[4].strip()
                if text:
                    block_texts.append(text)
            page_text = "\n".join(block_texts).strip()
            if page_index == 1 and block_texts:
                title = block_texts[0][:300]
            pages.append(f"--- PAGE {page_index} ---\n{page_text}")
        return ParsedDocument(
            paper_id=pdf_path.stem,
            source_file=str(pdf_path),
            title=title,
            text="\n\n".join(pages),
        )

    def save(self, parsed: ParsedDocument) -> Path:
        out_path = PARSED_DIR / f"{parsed.paper_id}.json"
        write_json(out_path, parsed.model_dump())
        return out_path
