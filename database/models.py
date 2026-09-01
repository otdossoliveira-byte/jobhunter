"""
database/models.py

Define o modelo ORM (SQLAlchemy) que representa a tabela `vagas`
no banco SQLite. Substitui completamente o antigo armazenamento em CSV.
"""

import enum
from datetime import datetime

from sqlalchemy import String, DateTime, Enum, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class StatusVaga(str, enum.Enum):
    NOVA = "Nova"
    NOTIFICADA = "Notificada"
    CANDIDATADO = "Candidatado"
    IGNORADA = "Ignorada"


class Vaga(Base):
    __tablename__ = "vagas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    titulo_vaga: Mapped[str] = mapped_column(String(255), nullable=False)
    empresa: Mapped[str] = mapped_column(String(255), nullable=False)
    cidade: Mapped[str] = mapped_column(String(120), nullable=False)
    link_vaga: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    data_descoberta: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[StatusVaga] = mapped_column(
        Enum(StatusVaga), default=StatusVaga.NOVA, nullable=False
    )
    fonte: Mapped[str] = mapped_column(String(50), nullable=False, default="desconhecida")
    perfil_busca: Mapped[str] = mapped_column(String(120), nullable=False, default="")

    def __repr__(self) -> str:
        return f"<Vaga id={self.id} titulo='{self.titulo_vaga}' empresa='{self.empresa}' status={self.status}>"
