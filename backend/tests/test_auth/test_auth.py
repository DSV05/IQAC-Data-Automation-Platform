"""
Auth module tests.

Run: docker compose exec backend pytest tests/ -v
"""
import pytest
from httpx import AsyncClient

from app.core.security import hash_password
from app.models.user import User, UserRole


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_user_data():
    return {
        "email": "test@ganpat.ac.in",
        "full_name": "Test User",
        "password": "Test@1234",
        "role": "viewer",
    }


@pytest.fixture
def admin_user_data():
    return {
        "email": "admin@ganpat.ac.in",
        "full_name": "Admin User",
        "password": "Admin@1234",
        "role": "super_admin",
    }


# ── Unit Tests: RBAC ──────────────────────────────────────────────────────────

class TestRBACPermissions:
    def test_viewer_has_read_permissions(self):
        from app.core.permissions import get_all_permissions
        perms = get_all_permissions(UserRole.VIEWER)
        assert "dashboard:read" in perms
        assert "faculty:read" in perms

    def test_viewer_cannot_create(self):
        from app.core.permissions import get_all_permissions
        perms = get_all_permissions(UserRole.VIEWER)
        assert "faculty:create" not in perms
        assert "users:create" not in perms

    def test_iqac_admin_can_manage_users(self):
        from app.core.permissions import get_all_permissions
        perms = get_all_permissions(UserRole.IQAC_ADMIN)
        assert "users:read" in perms
        assert "users:create" in perms
        assert "users:update" in perms

    def test_iqac_admin_cannot_delete_users(self):
        from app.core.permissions import get_all_permissions
        perms = get_all_permissions(UserRole.IQAC_ADMIN)
        assert "users:delete" not in perms

    def test_super_admin_has_all_permissions(self):
        from app.core.permissions import get_all_permissions
        perms = get_all_permissions(UserRole.SUPER_ADMIN)
        assert "users:delete" in perms
        assert "system:configure" in perms
        assert "audit:manage" in perms

    def test_role_hierarchy(self):
        from app.core.permissions import has_minimum_role

        class FakeUser:
            role = UserRole.IQAC_ADMIN

        user = FakeUser()
        assert has_minimum_role(user, UserRole.VIEWER) is True
        assert has_minimum_role(user, UserRole.IQAC_ADMIN) is True
        assert has_minimum_role(user, UserRole.SUPER_ADMIN) is False

    def test_data_entry_inherits_viewer_perms(self):
        from app.core.permissions import get_all_permissions
        perms = get_all_permissions(UserRole.DATA_ENTRY_OPERATOR)
        # Inherited from viewer
        assert "dashboard:read" in perms
        # Own permissions
        assert "faculty:create" in perms
        # Cannot do admin things
        assert "users:create" not in perms


# ── Unit Tests: Security ──────────────────────────────────────────────────────

class TestSecurity:
    def test_password_hashing_roundtrip(self):
        from app.core.security import hash_password, verify_password
        pw = "SecurePass@123"
        hashed = hash_password(pw)
        assert hashed != pw
        assert verify_password(pw, hashed) is True
        assert verify_password("wrong", hashed) is False

    def test_access_token_creation_and_decode(self):
        import uuid
        from app.core.security import create_access_token, decode_token
        user_id = uuid.uuid4()
        token = create_access_token(user_id)
        payload = decode_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "access"

    def test_refresh_token_has_different_type(self):
        import uuid
        from app.core.security import create_refresh_token, decode_token
        user_id = uuid.uuid4()
        token = create_refresh_token(user_id)
        payload = decode_token(token)
        assert payload["type"] == "refresh"

    def test_tokens_are_different(self):
        import uuid
        from app.core.security import create_access_token, create_refresh_token
        user_id = uuid.uuid4()
        assert create_access_token(user_id) != create_refresh_token(user_id)


# ── Schema Validation Tests ───────────────────────────────────────────────────

class TestSchemas:
    def test_user_create_rejects_weak_password(self):
        from pydantic import ValidationError
        from app.schemas.auth import UserCreate
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@test.com",
                full_name="Test",
                password="weakpassword",  # no uppercase, no digit
            )

    def test_user_create_accepts_strong_password(self):
        from app.schemas.auth import UserCreate
        user = UserCreate(
            email="test@test.com",
            full_name="Test User",
            password="Strong@1234",
        )
        assert user.email == "test@test.com"

    def test_login_requires_email_format(self):
        from pydantic import ValidationError
        from app.schemas.auth import LoginRequest
        with pytest.raises(ValidationError):
            LoginRequest(email="not-an-email", password="pass")
