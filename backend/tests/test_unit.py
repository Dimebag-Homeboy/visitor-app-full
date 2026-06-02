from utils import get_password_hash, verify_password, create_access_token
from config import SECRET_KEY, ALGORITHM
from jose import jwt
from .test_config import ADMIN_PASSWORD

def test_password_hashing():
    password = ADMIN_PASSWORD  # используем пароль из конфига
    hashed = get_password_hash(password)
    assert verify_password(password, hashed)
    assert not verify_password("wrong", hashed)

def test_access_token_creation():
    data = {"sub": "testuser"}
    token = create_access_token(data)
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded["sub"] == "testuser"
    assert "exp" in decoded