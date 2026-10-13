from dataclasses import dataclass


@dataclass
class ApiKey:
    """Representa o estado e o ciclo de vida de uma chave de API.

    A entidade não conhece o pool nem o lock do gerenciador. Ela apenas
    valida e aplica as transições de uma locação individual.
    """

    key_id: str
    value: str
    in_use: bool = False
    last_used_at: float = 0.0
    next_available_at: float = 0.0
    lease_token: str | None = None

    def is_available(self, now: float) -> bool:
        """Indica se a chave pode receber uma nova locação neste instante."""
        return not self.in_use and self.next_available_at <= now

    def acquire(
        self,
        now: float,
        lease_token: str,
        cooldown_seconds: float,
    ) -> bool:
        """Registra uma locação, respeitando o cooldown da chave.

        O retorno ``False`` permite que o gerenciador avance para a próxima
        chave caso o estado tenha mudado antes da tentativa.
        """
        if not lease_token or not self.is_available(now):
            return False

        self.in_use = True
        self.lease_token = lease_token
        self.last_used_at = now
        self.next_available_at = now + cooldown_seconds
        return True

    def release(self, lease_token: str) -> bool:
        """Libera a locação somente se o token ainda for o proprietário."""
        if not lease_token or self.lease_token != lease_token:
            return False

        self.in_use = False
        self.lease_token = None
        return True
