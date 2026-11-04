from datetime import timedelta
from uuid import uuid4

import pytest

from app.core.security import (
    TokenExpiredError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.domain.access import Role


def test_password_hash_never_contains_plaintext_and_verifies() -> None:
    """把密码原文直接保存或使用不可验证散列时必须失败。"""
    password = "Career!2026"

    encoded = hash_password(password)

    assert encoded != password
    assert password not in encoded
    assert verify_password(password, encoded) is True
    assert verify_password("wrong-password", encoded) is False


def test_expired_access_token_is_rejected() -> None:
    """删除过期校验时必须失败，过期令牌不能访问受保护资源。"""
    token = create_access_token(
        user_id=uuid4(),
        role=Role.student,
        secret="s" * 32,
        expires_delta=timedelta(seconds=-1),
    )

    with pytest.raises(TokenExpiredError):
        decode_access_token(token, secret="s" * 32)
