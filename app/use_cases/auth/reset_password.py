from app.use_cases.ports import EmailSender, PasswordHasher, UnitOfWork


class ResetPassword:
    """Handles password reset."""

    def __init__(self, uow: UnitOfWork, hasher: PasswordHasher, mail: EmailSender):
        self.uow, self.hasher, self.mail = uow, hasher, mail

    async def execute(self, token: str, new_password: str):
        """Reset the user's password."""
        async with self.uow:
            et = await self.uow.email_token_repo.get_valid(token, "reset_password")
            if not et:
                raise ValueError("Token inválido o expirado")
            user = await self.uow.user_repo.get_by_id(et.user_id)
            user.password_hash = self.hasher.hash(new_password)
            await self.uow.user_repo.update(user)
            # Security: revoke all refresh tokens
            await self.uow.refresh_repo.revoke_all_for_user(user.id)
            await self.uow.email_token_repo.mark_used(et.id)
            await self.uow.commit()
        await self.mail.send(
            user.email, "Tu contraseña fue cambiada", "<p>Se cambió correctamente.</p>"
        )
        return True
