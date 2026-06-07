class DomainException(Exception):
    """Base class for all domain exceptions."""

    pass


class NotFoundError(DomainException):
    def __init__(self, detail: str = "Resource not found"):
        self.detail = detail
        super().__init__(self.detail)


class AuthError(DomainException):
    def __init__(self, detail: str = "Authentication failed"):
        self.detail = detail
        super().__init__(self.detail)


class ValidationError(DomainException):
    def __init__(self, detail: str = "Validation error"):
        self.detail = detail
        super().__init__(self.detail)


class PermissionError(DomainException):
    def __init__(self, detail: str = "Permission denied"):
        self.detail = detail
        super().__init__(self.detail)
