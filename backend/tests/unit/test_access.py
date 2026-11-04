from uuid import uuid4

import pytest

from app.core.errors import ForbiddenError
from app.domain.access import AccessContext, Role, ensure_roles


def test_student_cannot_satisfy_admin_role_requirement() -> None:
    """移除服务端角色检查时必须失败，前端隐藏菜单不能替代鉴权。"""
    context = AccessContext(user_id=uuid4(), role=Role.student)

    with pytest.raises(ForbiddenError):
        ensure_roles(context, {Role.admin})


def test_admin_satisfies_admin_role_requirement() -> None:
    context = AccessContext(user_id=uuid4(), role=Role.admin)

    ensure_roles(context, {Role.admin})
