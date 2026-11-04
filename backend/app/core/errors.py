class DomainError(Exception):
    """可安全映射为 API 响应的业务异常。"""

    status_code = 400
    code = "DOMAIN_ERROR"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ForbiddenError(DomainError):
    status_code = 403
    code = "FORBIDDEN"


class UnauthorizedError(DomainError):
    status_code = 401
    code = "UNAUTHORIZED"


class InvalidCredentialsError(UnauthorizedError):
    code = "INVALID_CREDENTIALS"

    def __init__(self) -> None:
        super().__init__("账号或密码错误")


class InvalidRefreshTokenError(UnauthorizedError):
    code = "INVALID_REFRESH_TOKEN"

    def __init__(self) -> None:
        super().__init__("刷新令牌无效或已失效")


class AccountLockedError(DomainError):
    status_code = 423
    code = "ACCOUNT_LOCKED"

    def __init__(self) -> None:
        super().__init__("账号已临时锁定，请稍后重试")

