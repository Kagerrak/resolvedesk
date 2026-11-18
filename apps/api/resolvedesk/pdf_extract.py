"""Isolated, bounded text extraction. Never renders PDF actions or performs OCR."""

import io
import json
import resource
import sys

from pypdf import PdfReader, apply_configuration
from pypdf.errors import PdfReadError


class UnsupportedPDF(ValueError):
    """A safe, user-facing document limitation."""


def extract(raw: bytes) -> list[str]:
    with apply_configuration(
        maximum_declared_stream_length=2_000_000,
        array_based_stream_maximum_output_length=2_000_000,
        zlib_maximum_output_length=2_000_000,
        lzw_maximum_output_length=2_000_000,
        run_length_maximum_output_length=2_000_000,
        brotli_maximum_output_length=2_000_000,
        stream_decoding_work_maximum_length=8_000_000,
        stream_parsing_work_maximum_count=250_000,
        page_tree_maximum_entries=1000,
        page_tree_maximum_depth=20,
        xform_maximum_invocations_per_extraction=100,
        jbig2dec_binary=None,
    ):
        reader = PdfReader(io.BytesIO(raw), strict=True)
        if reader.is_encrypted:
            raise UnsupportedPDF(
                "Encrypted PDFs are not supported. Export an unencrypted text PDF."
            )
        if not 1 <= len(reader.pages) <= 20:
            raise UnsupportedPDF("Use a PDF with 1 to 20 pages.")
        pages, total = [], 0
        for number, page in enumerate(reader.pages, 1):
            text = page.extract_text().strip()
            if not text:
                raise UnsupportedPDF(
                    f"Page {number} has no extractable text. Scanned or empty PDF pages are not supported; OCR is not available. Export a text-based PDF."
                )
            total += len(text)
            if total > 100_000:
                raise UnsupportedPDF(
                    "This PDF has too much extracted text. Split it into smaller documents."
                )
            pages.append(text)
        return pages


if __name__ == "__main__":
    resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
    memory_limit = 512 * 1024 * 1024
    # macOS does not support lowering these process memory limits reliably.
    # Production Linux enforces the address-space cap in addition to parser bounds.
    if sys.platform == "linux":
        resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))
    raw = sys.stdin.buffer.read(2 * 1024 * 1024 + 1)
    try:
        if len(raw) > 2 * 1024 * 1024:
            raise UnsupportedPDF("Keep PDF uploads under 2 MB.")
        result = {"pages": extract(raw)}
    except UnsupportedPDF as error:
        result = {"error": str(error)}
    except (
        PdfReadError,
        ValueError,
        TypeError,
        KeyError,
        IndexError,
        RecursionError,
        MemoryError,
        OverflowError,
    ):
        result = {
            "error": "This PDF could not be safely read. Export a new text-based PDF and upload it again."
        }
    print(json.dumps(result))
