import pytest
from pydantic import ValidationError
from src.models import BaseUser, User, AdminUser


# ---------- BaseUser tests ----------

@pytest.mark.parametrize(
    "first_name_input, expected",
    [
        ("петя", "Петя"),
        ("Петя", "Петя"),
        ("  петя  ", "Петя"),
        ("ВаСЯ", "Вася"),
        ("john", "John"),
        ("JOHN", "John"),
    ],
)
def test_first_name_normalization(first_name_input: str, expected: str) -> None:
    u = BaseUser(email="a@b.com", first_name=first_name_input, last_name="иванов")
    assert u.first_name == expected


@pytest.mark.parametrize(
    "last_name_input, expected",
    [
        ("иванов", "Иванов"),
        ("ИВАНОВ", "Иванов"),
        ("  сидоров  ", "Сидоров"),
        ("doe", "Doe"),
    ],
)
def test_last_name_normalization(last_name_input: str, expected: str) -> None:
    u = BaseUser(email="a@b.com", first_name="петя", last_name=last_name_input)
    assert u.last_name == expected


@pytest.mark.parametrize("bad_email", ["not-an-email", "a@b", "a@b.", "@domain.com", "user@"])
def test_invalid_email_raises(bad_email: str) -> None:
    with pytest.raises(ValidationError):
        BaseUser(email=bad_email, first_name="Петя", last_name="Иванов")


@pytest.mark.parametrize("empty_name_field", ["", "   "])
def test_empty_first_or_last_name_raises(empty_name_field: str) -> None:
    with pytest.raises(ValidationError):
        BaseUser(email="a@b.com", first_name=empty_name_field, last_name="Иванов")
    with pytest.raises(ValidationError):
        BaseUser(email="a@b.com", first_name="Петя", last_name=empty_name_field)


def test_assignment_validation_normalizes_and_validates() -> None:
    u = BaseUser(email="a@b.com", first_name="петя", last_name="иванов")
    assert u.first_name == "Петя"
    u.first_name = "вася"
    assert u.first_name == "Вася"
    with pytest.raises(ValidationError):
        u.last_name = "   "


# ---------- User tests ----------

@pytest.mark.parametrize(
    "password",
    [
        "Abcdef1!",
        "p@ssw0rd!",
        "Qwerty9#",
    ],
)
def test_valid_passwords(password: str) -> None:
    u = User(email="a@b.com", first_name="Иван", last_name="Петров", password=password, age=18)
    assert u.password == password


@pytest.mark.parametrize(
    "password, err_msg_part",
    [
        ("short1!", "at least 8"),
        ("longbutnospecial1", "special"),
        ("!!!!@@@@", "digit"),
        ("NoDigit!", "digit"),
        ("NoSpecial1", "special"),
    ],
)
def test_invalid_passwords(password: str, err_msg_part: str) -> None:
    with pytest.raises(ValidationError) as ei:
        User(email="a@b.com", first_name="Иван", last_name="Петров", password=password, age=25)
    assert err_msg_part.lower() in str(ei.value).lower()


@pytest.mark.parametrize("age", [18, 30, 99])
def test_age_min_boundary_ok(age: int) -> None:
    u = User(email="a@b.com", first_name="Иван", last_name="Петров", password="Abcdef1!", age=age)
    assert u.age == age


@pytest.mark.parametrize("age", [0, 17, -1])
def test_age_below_min_raises(age: int) -> None:
    with pytest.raises(ValidationError):
        User(email="a@b.com", first_name="Иван", last_name="Петров", password="Abcdef1!", age=age)


def test_user_assignment_validation() -> None:
    u = User(email="a@b.com", first_name="Иван", last_name="Петров", password="Abcdef1!", age=20)
    u.first_name = "ваСЯ"
    assert u.first_name == "Вася"
    with pytest.raises(ValidationError):
        u.age = 17


# ---------- AdminUser tests ----------

@pytest.mark.parametrize("role", ["admin", "superadmin"])
def test_admin_role_valid(role: str) -> None:
    admin = AdminUser(
        email="a@b.com",
        first_name="Иван",
        last_name="Петров",
        password="Abcdef1!",
        age=33,
        role=role,
    )
    assert admin.role == role


@pytest.mark.parametrize("role", ["administrator", "root", "", "user"])
def test_admin_role_invalid(role: str) -> None:
    with pytest.raises(ValidationError):
        AdminUser(
            email="a@b.com",
            first_name="Иван",
            last_name="Петров",
            password="Abcdef1!",
            age=33,
            role=role,
        )


def test_admin_permissions_superadmin_allows_any() -> None:
    admin = AdminUser(
        email="a@b.com",
        first_name="Иван",
        last_name="Петров",
        password="Abcdef1!",
        age=33,
        role="superadmin",
    )
    for perm in ["read", "write", "delete", "manage_users", "view_reports", "anything_custom"]:
        assert admin.has_permission(perm) is True


@pytest.mark.parametrize(
    "permission, expected",
    [
        ("read", True),
        ("write", True),
        ("delete", True),
        ("view_reports", True),
        ("manage_users", True),
        ("manage_roles", False),
        ("system_shutdown", False),
    ],
)
def test_admin_permissions_admin_subset(permission: str, expected: bool) -> None:
    admin = AdminUser(
        email="a@b.com",
        first_name="Иван",
        last_name="Петров",
        password="Abcdef1!",
        age=33,
        role="admin",
    )
    assert admin.has_permission(permission) is expected
