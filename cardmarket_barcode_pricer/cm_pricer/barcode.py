from __future__ import annotations
import re


def normalize_barcode(raw: str) -> str:
    """Return digit-only barcode. 1D scanners usually type digits + Enter."""
    return re.sub(r"\D+", "", raw or "")


def ean13_check_digit(first12: str) -> int:
    if len(first12) != 12 or not first12.isdigit():
        raise ValueError("EAN-13 check digit requires first 12 digits")
    digits = [int(d) for d in first12]
    total = sum(digits[0::2]) + 3 * sum(digits[1::2])
    return (10 - (total % 10)) % 10


def is_valid_ean13(code: str) -> bool:
    code = normalize_barcode(code)
    return len(code) == 13 and code.isdigit() and ean13_check_digit(code[:12]) == int(code[-1])


def is_valid_upca(code: str) -> bool:
    code = normalize_barcode(code)
    if len(code) != 12 or not code.isdigit():
        return False
    # UPC-A check: odd positions (from left, excluding check) *3 + even positions.
    digits = [int(d) for d in code]
    total = 3 * sum(digits[:11:2]) + sum(digits[1:11:2])
    return (10 - (total % 10)) % 10 == digits[-1]


def upca_to_ean13(code: str) -> str:
    code = normalize_barcode(code)
    if len(code) == 12:
        return "0" + code
    return code


def validate_any(code: str) -> dict:
    code = normalize_barcode(code)
    return {
        "raw": code,
        "normalized": upca_to_ean13(code) if len(code) == 12 else code,
        "is_ean13": is_valid_ean13(code),
        "is_upca": is_valid_upca(code),
        "valid": is_valid_ean13(code) or is_valid_upca(code),
    }
