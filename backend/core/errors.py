"""Application errors. main.py turns each one into the JSON error body from the SRS:
{"error_code": "...", "message": "..."}"""


class AppError(Exception):
    status_code = 400
    error_code = "BAD_REQUEST"
    message = "Bad request"

    @property
    def headers(self) -> dict[str, str] | None:
        # A 401 must tell the client which auth scheme is expected.
        if self.status_code == 401:
            return {"WWW-Authenticate": "Bearer"}
        return None


class UsernameTakenError(AppError):
    status_code = 409
    error_code = "USERNAME_TAKEN"
    message = "Username is already taken"


class EmailTakenError(AppError):
    status_code = 409
    error_code = "EMAIL_TAKEN"
    message = "Email is already registered"


class InvalidCredentialsError(AppError):
    status_code = 401
    error_code = "INVALID_CREDENTIALS"
    message = "Invalid username or password"


class NotAuthenticatedError(AppError):
    status_code = 401
    error_code = "NOT_AUTHENTICATED"
    message = "Authentication required"


class TokenInvalidError(AppError):
    status_code = 401
    error_code = "TOKEN_INVALID"
    message = "Invalid token"


class TokenExpiredError(AppError):
    status_code = 401
    error_code = "TOKEN_EXPIRED"
    message = "Token has expired"


class UserBannedError(AppError):
    status_code = 403
    error_code = "USER_BANNED"
    message = "This account is banned"


class ForbiddenError(AppError):
    status_code = 403
    error_code = "FORBIDDEN"
    message = "You do not have permission to do this"


class UserNotFoundError(AppError):
    status_code = 404
    error_code = "USER_NOT_FOUND"
    message = "User not found"


class CannotModifySelfError(AppError):
    status_code = 403
    error_code = "CANNOT_MODIFY_SELF"
    message = "You cannot do this to your own account"


class CannotModifyAdminError(AppError):
    status_code = 403
    error_code = "CANNOT_MODIFY_ADMIN"
    message = "You cannot ban another admin"
