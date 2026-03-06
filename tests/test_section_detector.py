"""Tests for contract section detection."""

from ot_app.utils.section_detector import detect_sections, filter_obligation_sections


def test_detect_numbered_headings():
    text = """1. Term
This agreement is effective for 12 months.

2. Payment Terms
Client shall pay within 30 days.

3. Confidentiality
Both parties agree to maintain confidentiality."""

    sections = detect_sections(text)
    assert len(sections) >= 3
    headings = [s.heading for s in sections]
    assert any("Term" in h for h in headings)
    assert any("Payment" in h for h in headings)


def test_detect_markdown_headings():
    text = """## Term
This agreement is effective for 12 months.

## Payment Terms
Client shall pay within 30 days.

## Deliverables
Consultant shall deliver monthly reports."""

    sections = detect_sections(text)
    assert len(sections) >= 3


def test_filter_obligation_sections():
    text = """## Definitions
Terms used herein...

## Payment Terms
Client shall pay within 30 days.

## General Provisions
This agreement governed by Delaware law.

## Termination
Either party may terminate with 30 days notice."""

    sections = detect_sections(text)
    relevant = filter_obligation_sections(sections)
    headings = [s.heading for s in relevant]
    assert any("Payment" in h for h in headings)
    assert any("Termination" in h for h in headings)


def test_fallback_chunking():
    # Long text with no headings
    text = "This is a contract paragraph. " * 200
    sections = detect_sections(text)
    assert len(sections) >= 1
    assert "chunk" in sections[0].heading.lower()


def test_empty_text():
    sections = detect_sections("")
    assert sections == [] or all(not s.content for s in sections)
