import uuid

import sqlmodel


class VaultBase(sqlmodel.SQLModel):
    id: uuid.UUID = sqlmodel.Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    apr: float | None = None
    monthly_apy: float | None = None
    weekly_apy: float | None = None
    max_drawdown: float | None = None
    vault_capacity: int | None = None
    vault_currency: str | None = None


# Database model, database table inferred from class name
class Vault(VaultBase, table=True):
    __tablename__ = "vaults"
