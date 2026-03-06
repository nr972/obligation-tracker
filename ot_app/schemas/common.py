"""Shared enums used across schemas and models."""

from enum import StrEnum


class ContractStatus(StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"


class ContractType(StrEnum):
    SAAS = "saas"
    VENDOR = "vendor"
    DPA = "dpa"
    CONSULTING = "consulting"
    LICENSE = "license"
    MSA = "msa"
    CONTRACTOR = "contractor"
    LEASE = "lease"
    OTHER = "other"


class ExtractionStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    MANUAL = "manual"


class ObligationStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    WAIVED = "waived"
    ESCALATED = "escalated"


class ObligationType(StrEnum):
    PAYMENT = "payment"
    DELIVERY = "delivery"
    REPORTING = "reporting"
    COMPLIANCE = "compliance"
    NOTIFICATION = "notification"
    RENEWAL = "renewal"
    SLA = "sla"
    CONFIDENTIALITY = "confidentiality"
    DATA_PROTECTION = "data_protection"
    OTHER = "other"


class RiskLevel(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ResponsibleParty(StrEnum):
    US = "us"
    COUNTERPARTY = "counterparty"
    BOTH = "both"


class DeadlineType(StrEnum):
    FIXED = "fixed"
    RECURRING = "recurring"
    ONGOING = "ongoing"
    EVENT_TRIGGERED = "event_triggered"


class RecurrencePattern(StrEnum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"


class ExtractionSource(StrEnum):
    AI = "ai"
    MANUAL = "manual"
    SAMPLE = "sample"


class RenewalType(StrEnum):
    AUTO = "auto"
    MANUAL = "manual"
    NONE = "none"
