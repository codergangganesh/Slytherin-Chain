"""Custom domain exceptions for SentinelChain.

All business and validation errors inherit from SentinelChainException.
"""

from __future__ import annotations


class SentinelChainException(Exception):
    """Base exception for all domain and operational errors."""

    def __init__(self, message: str, code: str = "INTERNAL_ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class EntityNotFoundError(SentinelChainException):
    """Raised when a requested domain entity cannot be located."""

    def __init__(self, entity_type: str, identifier: str) -> None:
        super().__init__(
            f"{entity_type} with identifier '{identifier}' not found.",
            code="ENTITY_NOT_FOUND",
        )


class DuplicateEntityError(SentinelChainException):
    """Raised when an entity with duplicate unique attributes is created."""

    def __init__(self, entity_type: str, identifier: str) -> None:
        super().__init__(
            f"{entity_type} with identifier '{identifier}' already exists.",
            code="DUPLICATE_ENTITY",
        )


class AuthenticationError(SentinelChainException):
    """Raised when user credentials or tokens are invalid or expired."""

    def __init__(self, message: str = "Invalid authentication credentials.") -> None:
        super().__init__(message, code="AUTHENTICATION_FAILED")


class AuthorizationError(SentinelChainException):
    """Raised when a user lacks the required role or permission."""

    def __init__(self, message: str = "Insufficient permissions for this operation.") -> None:
        super().__init__(message, code="PERMISSION_DENIED")


class InvalidStateTransitionError(SentinelChainException):
    """Raised when an incident or action state transition is illegal."""

    def __init__(self, from_state: str, to_state: str, reason: str = "") -> None:
        detail = f": {reason}" if reason else ""
        super().__init__(
            f"Cannot transition from state '{from_state}' to '{to_state}'{detail}.",
            code="INVALID_STATE_TRANSITION",
        )


class GuardrailViolationError(SentinelChainException):
    """Raised when an autonomous response action violates a safety guardrail."""

    def __init__(self, guardrail_name: str, reason: str) -> None:
        super().__init__(
            f"Action blocked by guardrail '{guardrail_name}': {reason}",
            code="GUARDRAIL_VIOLATION",
        )


class RuleValidationError(SentinelChainException):
    """Raised when a detection rule definition is invalid."""

    def __init__(self, rule_id: str, reason: str) -> None:
        super().__init__(
            f"Detection rule '{rule_id}' is invalid: {reason}",
            code="INVALID_RULE_DEFINITION",
        )


class PlaybookValidationError(SentinelChainException):
    """Raised when a response playbook definition is invalid."""

    def __init__(self, playbook_id: str, reason: str) -> None:
        super().__init__(
            f"Response playbook '{playbook_id}' is invalid: {reason}",
            code="INVALID_PLAYBOOK_DEFINITION",
        )


class LedgerIntegrityError(SentinelChainException):
    """Raised when hash chain or Merkle tree integrity verification fails."""

    def __init__(self, sequence_number: int, reason: str) -> None:
        super().__init__(
            f"Ledger tampering detected at sequence #{sequence_number}: {reason}",
            code="LEDGER_TAMPERED",
        )


class BlockchainClientError(SentinelChainException):
    """Raised when communicating with the blockchain node fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="BLOCKCHAIN_ERROR")
