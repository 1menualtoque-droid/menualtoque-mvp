# app/interfaces/security/password_hasher.py
from passlib.context import CryptContext


class PasswordHasherImpl:
    def __init__(self):
        self.ctx = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

    def hash(self, password: str) -> str:
        return self.ctx.hash(password)

    def verify(self, password: str, password_hash: str) -> bool:
        return self.ctx.verify(password, password_hash)
