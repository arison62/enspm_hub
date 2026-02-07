# core/api/exceptions.py
class ErrorCode:    
    NOT_FOUND = "NOT_FOUND"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    BAD_REQUEST = "BAD_REQUEST"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    HTTP_ERROR = "HTTP_ERROR"
    UNAUTHORIZED = "UNAUTHORIZED"
    
class BaseAPIException(Exception):
    def __init__(self, message: str, status_code: int = 400, code: str | None = None):
        super().__init__(message)

        self.message = message
        self.status_code = status_code
        self.code = code or ErrorCode.INTERNAL_ERROR

class NotFoundAPIException(BaseAPIException):
    def __init__(self, message="La ressource demandée n'a pas été trouvée."):
        super().__init__(message, 404, ErrorCode.NOT_FOUND)


class PermissionDeniedAPIException(BaseAPIException):
    def __init__(self, message="Permission refusée."):
        super().__init__(message, 403, ErrorCode.PERMISSION_DENIED)


class BadRequestAPIException(BaseAPIException):
    def __init__(self, message="Requête invalide."):
        super().__init__(message, 400, ErrorCode.BAD_REQUEST)
        

class ValidationErrorAPIException(BaseAPIException):
    def __init__(self, message="Requête invalide."):
        super().__init__(message, 400, ErrorCode.VALIDATION_ERROR)
