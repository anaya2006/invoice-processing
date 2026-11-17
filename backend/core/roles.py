# backend/core/roles.py
"""Role constants used throughout the application."""
from enum import StrEnum

class Role(StrEnum):
    AP_OPERATOR = "AP_OPERATOR"
    FINANCE_REVIEWER = "FINANCE_REVIEWER"
    ADMIN = "ADMIN"
    AUDITOR = "AUDITOR"
    SYSTEM = "SYSTEM"  # internal, never logs in
