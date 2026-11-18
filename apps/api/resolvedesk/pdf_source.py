"""Run untrusted PDF parsing outside the API and worker process."""

import json
import subprocess
import sys


def extract_pages(raw: bytes) -> list[str]:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "resolvedesk.pdf_extract"],
            input=raw,
            capture_output=True,
            timeout=15,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError):
        raise ValueError(
            "PDF processing exceeded its limits. Export a smaller text-based PDF and upload it again."
        ) from None
    if result.returncode:
        raise ValueError(
            "PDF processing stopped safely. Export a simpler text-based PDF and upload it again."
        )
    try:
        output = json.loads(result.stdout)
        if "error" in output:
            raise ValueError(output["error"])
        pages = output["pages"]
        if (
            not isinstance(pages, list)
            or not pages
            or not all(isinstance(p, str) and p.strip() for p in pages)
        ):
            raise ValueError("PDF contains no usable text. OCR is not supported.")
        return pages
    except (json.JSONDecodeError, KeyError):
        raise ValueError("PDF extraction could not finish. Export a new text-based PDF.") from None
