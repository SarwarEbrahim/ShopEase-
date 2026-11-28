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


class WrongPasswordError(AppError):
    status_code = 400
    error_code = "WRONG_PASSWORD"
    message = "Current password is incorrect"


class PasswordUnchangedError(AppError):
    status_code = 400
    error_code = "PASSWORD_UNCHANGED"
    message = "The new password must be different from the current one"


class TooManyAttemptsError(AppError):
    status_code = 429
    error_code = "TOO_MANY_ATTEMPTS"
    message = "Too many failed attempts. Try again in 15 minutes"


class GroupNotFoundError(AppError):
    status_code = 404
    error_code = "GROUP_NOT_FOUND"
    message = "Group not found"


class NotGroupOwnerError(AppError):
    status_code = 403
    error_code = "NOT_GROUP_OWNER"
    message = "Only the group owner can do this"


class GroupPermissionError(AppError):
    status_code = 403
    error_code = "GROUP_PERMISSION_DENIED"
    message = "You do not have this permission in the group"


class AlreadyMemberError(AppError):
    status_code = 409
    error_code = "ALREADY_MEMBER"
    message = "This user is already in the group"


class NotAMemberError(AppError):
    status_code = 400
    error_code = "NOT_A_MEMBER"
    message = "This user is not a member of the group"
