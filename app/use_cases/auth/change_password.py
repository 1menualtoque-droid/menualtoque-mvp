from app.domain.errors import InvalidCredentialsError, SamePasswordError


class ChangePassword:
    """Handles password change."""

    def __init__(self, uow, hasher, mail):
        self.uow, self.hasher, self.mail = uow, hasher, mail

    async def execute(self, user_id: int, current_pwd: str, new_pwd: str):
        """Change the user's password."""
        async with self.uow:
            user = await self.uow.user_repo.get_by_id(user_id)
            if (
                not user
                or not user.password_hash
                or not self.hasher.verify(current_pwd, user.password_hash)
            ):
                raise InvalidCredentialsError("Credenciales inválidas")
            if self.hasher.verify(new_pwd, user.password_hash):
                raise SamePasswordError("La nueva contraseña no puede ser igual a la anterior")
            user.password_hash = self.hasher.hash(new_pwd)
            await self.uow.user_repo.update(user)
            await self.uow.commit()
        await self.mail.send(
            user.email, "Contraseña actualizada", "<p>Se actualizó con éxito.</p>"
        )
