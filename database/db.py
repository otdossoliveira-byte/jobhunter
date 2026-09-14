"""
database/db.py

Camada de persistência. Cria a engine SQLAlchemy, a fábrica de sessões
e expõe funções utilitárias de alto nível (salvar vaga, checar duplicata,
atualizar status) para que o resto do sistema nunca precise escrever SQL
ou manipular a Session diretamente.
"""

from contextlib import contextmanager
from typing import Optional

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session

from config import settings
from database.models import Base, Vaga, StatusVaga

# `check_same_thread=False` é necessário porque o Playwright roda em loop
# assíncrono e pode acessar o banco a partir de contextos diferentes.
engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db() -> None:
    """Cria as tabelas no banco caso ainda não existam."""
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_session():
    """Context manager simples para abrir/fechar sessões com segurança."""
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def vaga_ja_existe(session: Session, link_vaga: str) -> bool:
    """Verifica duplicidade pelo link da vaga (campo UNIQUE)."""
    stmt = select(Vaga.id).where(Vaga.link_vaga == link_vaga)
    return session.execute(stmt).first() is not None


def salvar_vaga(session: Session, dados: dict) -> Optional[Vaga]:
    """
    Salva uma nova vaga no banco caso ela ainda não exista.
    Retorna o objeto Vaga criado, ou None se já era duplicata.

    `dados` deve conter: titulo_vaga, empresa, cidade, link_vaga, fonte
    """
    if vaga_ja_existe(session, dados["link_vaga"]):
        return None

    nova_vaga = Vaga(
        titulo_vaga=dados["titulo_vaga"],
        empresa=dados["empresa"],
        cidade=dados["cidade"],
        link_vaga=dados["link_vaga"],
        fonte=dados.get("fonte", "desconhecida"),
        perfil_busca=dados.get("perfil_busca", ""),
        status=StatusVaga.NOVA,
    )
    session.add(nova_vaga)
    session.flush()  # garante que o ID já esteja disponível antes do commit externo
    return nova_vaga


def atualizar_status(session: Session, vaga_id: int, novo_status: StatusVaga) -> None:
    vaga = session.get(Vaga, vaga_id)
    if vaga:
        vaga.status = novo_status
