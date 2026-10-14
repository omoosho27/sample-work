import re
from typing import Any, Dict, List

WARNING_PATTERN = re.compile(r"GOVERNMENT\s*WARNING[:.]?", re.IGNORECASE)


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = value.replace("’", "'").replace("‘", "'")
    value = value.replace("–", "-").replace("—", "-")
    value = value.replace("﻿", "")
    value = value.replace(" ", " ")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def _is_probable_field_line(line: str, *, allow_short: bool = False) -> bool:
    if not line or len(line) > 120:
        return False
    if re.search(
        r"(?:^|\s)(?:WARNING|ALC|ABV|PROOF|BOTTLED|IMPORTER|ORIGIN|COUNTRY|CONTENTS|ADDRESS|STATE|ZIP|CITY)\b",
        line,
        re.I,
    ):
        return False
    if re.search(r"\d+\s*(?:%|mL|L|oz|fl\.?\s*oz)", line, re.I):
        return False
    if not re.search(r"[A-Za-z]", line):
        return False
    words = re.findall(r"[A-Za-z']+", line)
    if not words:
        return False
    if not allow_short and len(words) < 2:
        return False
    return True


def _extract_warning(full_text: str) -> str:
    match = WARNING_PATTERN.search(full_text)
    if not match:
        return ""
    # Capture from the warning heading through the end of that paragraph.
    rest = full_text[match.start():]
    end = rest.find("\n\n")
    return (rest if end == -1 else rest[:end]).strip()


def extract_label_fields(text: Any) -> Dict[str, str]:
    full_text = normalize_text(text)
    lines = [line.strip() for line in full_text.split("\n") if line.strip()]

    brand_name = ""
    class_type = ""
    alcohol_content = ""
    net_contents = ""
    warning_statement = _extract_warning(full_text)

    for line in lines:
        if WARNING_PATTERN.search(line):
            break

        if not brand_name and _is_probable_field_line(line, allow_short=True):
            brand_name = line
            continue

        if not class_type and line != brand_name and _is_probable_field_line(line):
            class_type = line
            continue

        if not alcohol_content:
            match = re.search(
                r"\d+(?:\.\d+)?\s*%\s*(?:Alc\.?\s*/\s*Vol\.?|Alc\.?\s*Vol\.?|ABV)\s*(?:\(\s*\d+(?:\.\d+)?\s*Proof\s*\))?"
                r"|\d+(?:\.\d+)?\s*%\s*(?:alc\.|abv)",
                line,
                re.I,
            )
            if match:
                alcohol_content = match.group(0)
                continue
            match = re.search(r"\d+(?:\.\d+)?\s*proof", line, re.I)
            if match and "alcohol" not in line.lower():
                alcohol_content = line
                continue

        if not net_contents:
            match = re.search(r"\d+(?:\.\d+)?\s*(?:mL|L|oz|fl\.?\s*oz)\b", line, re.I)
            if match:
                net_contents = match.group(0)
                continue

    # Fallbacks never pull from the warning text.
    candidate_lines = [line for line in lines if not WARNING_PATTERN.search(line)]

    if not brand_name and candidate_lines:
        brand_name = candidate_lines[0]
    if not class_type and len(candidate_lines) > 1:
        class_type = candidate_lines[1]

    if not alcohol_content:
        for line in candidate_lines:
            if re.search(r"\d+(?:\.\d+)?\s*%", line):
                alcohol_content = line
                break

    if not net_contents:
        for line in candidate_lines:
            match = re.search(r"\d+(?:\.\d+)?\s*(?:mL|L|oz|fl\.?\s*oz)\b", line, re.I)
            if match:
                net_contents = match.group(0)
                break

    return {
        "brand_name": brand_name,
        "class_type": class_type,
        "alcohol_content": alcohol_content,
        "net_contents": net_contents,
        "warning_statement": warning_statement,
    }


def validate_label(fields: Dict[str, Any]) -> Dict[str, object]:
    findings: List[str] = []
    normalized = {
        key: ("" if value is None else str(value)).strip()
        for key, value in (fields or {}).items()
    }

    if not normalized.get("brand_name"):
        findings.append("Brand name is missing or unreadable.")
    if not normalized.get("class_type"):
        findings.append("Class/type designation is missing or unreadable.")
    if not normalized.get("alcohol_content"):
        findings.append("Alcohol content is missing or unreadable.")
    if not normalized.get("net_contents"):
        findings.append("Net contents are missing or unreadable.")

    warning = normalized.get("warning_statement", "")
    if not warning or not WARNING_PATTERN.search(warning):
        findings.append("Government warning statement is missing or not recognized.")

    return {
        "passed": not findings,
        "issues": findings,
        "summary": (
            "Label meets the minimum inspection checks."
            if not findings
            else "Label needs manual review."
        ),
    }
