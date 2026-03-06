"""Contract section detection for targeted extraction."""

import re
from dataclasses import dataclass


@dataclass
class ContractSection:
    heading: str
    content: str
    section_number: str | None = None


# Headings that typically contain extractable obligations
OBLIGATION_RELEVANT_HEADINGS = {
    "term", "payment", "fees", "obligations", "responsibilities", "duties",
    "sla", "service level", "service levels", "performance",
    "confidentiality", "data protection", "privacy", "security",
    "reporting", "audit", "compliance", "insurance",
    "indemnification", "indemnity", "liability",
    "termination", "notice", "renewal", "expiration",
    "deliverables", "milestones", "acceptance",
    "intellectual property", "ip", "license",
    "representations", "warranties", "covenants",
    "data processing", "sub-processor", "breach notification",
    "maintenance", "support",
}

# Patterns for detecting section headings
HEADING_PATTERNS = [
    # "## Heading" (from docx parser)
    re.compile(r"^##\s+(.+)$", re.MULTILINE),
    # "ARTICLE I - HEADING" or "ARTICLE 1 - HEADING"
    re.compile(r"^ARTICLE\s+[IVX\d]+[\s.:\-]+(.+)$", re.MULTILINE | re.IGNORECASE),
    # "1. Heading" or "1.1 Heading" or "1.1.1 Heading"
    re.compile(r"^(\d+(?:\.\d+)*)[.\s]+([A-Z][^\n]{2,})$", re.MULTILINE),
    # "Section 1: Heading" or "Section 1 - Heading"
    re.compile(r"^Section\s+\d+[\s.:\-]+(.+)$", re.MULTILINE | re.IGNORECASE),
    # ALL-CAPS lines (likely headings), at least 3 chars, no periods at end
    re.compile(r"^([A-Z][A-Z\s]{2,}[A-Z])$", re.MULTILINE),
]


def detect_sections(text: str) -> list[ContractSection]:
    """Split contract text into sections by heading detection.

    Falls back to chunking if no headings are detected.
    """
    # Find all heading positions
    headings: list[tuple[int, str, str | None]] = []  # (position, heading_text, section_number)

    for pattern in HEADING_PATTERNS:
        for match in pattern.finditer(text):
            groups = match.groups()
            if len(groups) == 2:
                # Pattern with section number + heading
                section_num, heading_text = groups
                headings.append((match.start(), heading_text.strip(), section_num.strip()))
            else:
                heading_text = groups[0].strip()
                headings.append((match.start(), heading_text, None))

    # Deduplicate headings at the same position
    seen_positions: set[int] = set()
    unique_headings = []
    for pos, text_h, num in sorted(headings, key=lambda x: x[0]):
        if pos not in seen_positions:
            seen_positions.add(pos)
            unique_headings.append((pos, text_h, num))

    if not unique_headings:
        return _fallback_chunking(text)

    # Build sections from headings
    sections = []
    for i, (pos, heading_text, section_num) in enumerate(unique_headings):
        if i + 1 < len(unique_headings):
            end = unique_headings[i + 1][0]
        else:
            end = len(text)

        content = text[pos:end].strip()
        sections.append(ContractSection(
            heading=heading_text,
            content=content,
            section_number=section_num,
        ))

    return sections


def filter_obligation_sections(sections: list[ContractSection]) -> list[ContractSection]:
    """Filter to sections likely to contain obligations."""
    relevant = []
    for section in sections:
        heading_lower = section.heading.lower()
        if any(keyword in heading_lower for keyword in OBLIGATION_RELEVANT_HEADINGS):
            relevant.append(section)

    # If nothing matched, return all sections (let the AI decide)
    return relevant if relevant else sections


def _fallback_chunking(text: str, chunk_size: int = 3000, overlap: int = 500) -> list[ContractSection]:
    """Split text into overlapping chunks when no headings detected."""
    chunks = []
    start = 0
    chunk_num = 1
    while start < len(text):
        end = min(start + chunk_size, len(text))

        # Try to break at a paragraph boundary
        if end < len(text):
            newline_pos = text.rfind("\n\n", start + chunk_size // 2, end)
            if newline_pos > start:
                end = newline_pos

        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append(ContractSection(
                heading=f"Section chunk {chunk_num}",
                content=chunk_text,
                section_number=str(chunk_num),
            ))
            chunk_num += 1

        start = end - overlap if end < len(text) else end

    return chunks
