"""
analytics/relatorios.py

Módulo de análise de dados do JobHunter usando SQL puro (sem ORM),
para demonstrar consultas reais sobre os dados que o robô já coletou.

Diferente do resto do projeto (que usa SQLAlchemy como ORM, uma camada
que evita escrever SQL na mão), este módulo conecta direto no banco
com `sqlite3` e escreve as consultas por extenso — SELECT, WHERE,
GROUP BY, JOIN, ORDER BY — para deixar claro o domínio da linguagem.

Uso:
    python analytics/relatorios.py
"""

import json
import os
import sqlite3
from pathlib import Path

CAMINHO_BANCO = os.path.join("database", "jobhunter.db")
CAMINHO_PERFIS = os.path.join("perfis", "perfis.json")


def conectar():
    """Abre uma conexão direta com o banco SQLite (sem ORM)."""
    if not os.path.exists(CAMINHO_BANCO):
        raise FileNotFoundError(
            f"Banco não encontrado em '{CAMINHO_BANCO}'. Rode 'python main.py' "
            "pelo menos uma vez antes, para o robô criar e popular o banco."
        )
    return sqlite3.connect(CAMINHO_BANCO)


def sincronizar_tabela_perfis(conexao: sqlite3.Connection) -> None:
    """
    Cria (se não existir) e atualiza a tabela `perfis_busca`, lendo os
    perfis salvos em perfis/perfis.json. Essa tabela existe só para
    permitir um JOIN de verdade com a tabela `vagas` — mostrando qual
    cargo e cidade cada perfil buscava, sem precisar duplicar essa
    informação em cada linha de vaga.
    """
    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS perfis_busca (
            nome   TEXT PRIMARY KEY,
            cargo  TEXT,
            cidade TEXT
        )
    """)

    if os.path.exists(CAMINHO_PERFIS):
        with open(CAMINHO_PERFIS, "r", encoding="utf-8") as arquivo:
            perfis = json.load(arquivo)

        for perfil in perfis:
            # INSERT OR REPLACE: insere se o nome ainda não existe na
            # tabela, ou substitui a linha inteira se já existir --
            # evita duplicar o mesmo perfil ao rodar de novo.
            cursor.execute(
                """
                INSERT OR REPLACE INTO perfis_busca (nome, cargo, cidade)
                VALUES (?, ?, ?)
                """,
                (perfil["nome"], perfil["cargo"], perfil["cidade"]),
            )

    conexao.commit()


def total_de_vagas(conexao: sqlite3.Connection) -> int:
    cursor = conexao.cursor()
    cursor.execute("SELECT COUNT(*) FROM vagas")
    return cursor.fetchone()[0]


def vagas_por_cidade(conexao: sqlite3.Connection, limite: int = 10) -> list:
    cursor = conexao.cursor()
    cursor.execute(
        """
        SELECT cidade, COUNT(*) AS total
        FROM vagas
        GROUP BY cidade
        ORDER BY total DESC
        LIMIT ?
        """,
        (limite,),
    )
    return cursor.fetchall()


def vagas_por_fonte(conexao: sqlite3.Connection) -> list:
    cursor = conexao.cursor()
    cursor.execute(
        """
        SELECT fonte, COUNT(*) AS total
        FROM vagas
        GROUP BY fonte
        ORDER BY total DESC
        """
    )
    return cursor.fetchall()


def vagas_por_status(conexao: sqlite3.Connection) -> list:
    cursor = conexao.cursor()
    cursor.execute(
        """
        SELECT status, COUNT(*) AS total
        FROM vagas
        GROUP BY status
        ORDER BY total DESC
        """
    )
    return cursor.fetchall()


def empresas_que_mais_aparecem(conexao: sqlite3.Connection, limite: int = 5) -> list:
    cursor = conexao.cursor()
    cursor.execute(
        """
        SELECT empresa, COUNT(*) AS total
        FROM vagas
        GROUP BY empresa
        ORDER BY total DESC
        LIMIT ?
        """,
        (limite,),
    )
    return cursor.fetchall()


def desempenho_por_perfil(conexao: sqlite3.Connection) -> list:
    """
    Usa JOIN de verdade: junta a tabela `perfis_busca` com a tabela
    `vagas`, casando pelo nome do perfil. LEFT JOIN garante que um
    perfil apareça no relatório mesmo que ainda não tenha encontrado
    nenhuma vaga (retornando 0, em vez de sumir da lista).
    """
    cursor = conexao.cursor()
    cursor.execute(
        """
        SELECT
            p.nome,
            p.cargo,
            p.cidade,
            COUNT(v.id) AS total_vagas_encontradas
        FROM perfis_busca AS p
        LEFT JOIN vagas AS v
            ON v.perfil_busca = p.nome
        GROUP BY p.nome
        ORDER BY total_vagas_encontradas DESC
        """
    )
    return cursor.fetchall()


def vagas_recentes(conexao: sqlite3.Connection, dias: int = 7) -> list:
    """Usa WHERE com função de data para filtrar só os últimos N dias."""
    cursor = conexao.cursor()
    cursor.execute(
        """
        SELECT titulo_vaga, empresa, cidade, data_descoberta
        FROM vagas
        WHERE data_descoberta >= date('now', ?)
        ORDER BY data_descoberta DESC
        """,
        (f"-{dias} day",),
    )
    return cursor.fetchall()


def imprimir_relatorio() -> None:
    conexao = conectar()
    try:
        sincronizar_tabela_perfis(conexao)

        print("=" * 60)
        print("JobHunter — Relatório de Dados (SQL)")
        print("=" * 60)

        print(f"\nTotal de vagas no banco: {total_de_vagas(conexao)}")

        print("\n-- Vagas por cidade --")
        for cidade, total in vagas_por_cidade(conexao):
            print(f"  {cidade or '(não informado)':30} {total}")

        print("\n-- Vagas por fonte (site) --")
        for fonte, total in vagas_por_fonte(conexao):
            print(f"  {fonte:30} {total}")

        print("\n-- Vagas por status --")
        for status, total in vagas_por_status(conexao):
            print(f"  {status:30} {total}")

        print("\n-- Top 5 empresas que mais aparecem --")
        for empresa, total in empresas_que_mais_aparecem(conexao):
            print(f"  {empresa:30} {total}")

        print("\n-- Desempenho por perfil de busca (JOIN) --")
        for nome, cargo, cidade, total in desempenho_por_perfil(conexao):
            print(f"  {nome:25} cargo='{cargo}' cidade='{cidade}' -> {total} vaga(s)")

        print("\n-- Vagas encontradas nos últimos 7 dias --")
        recentes = vagas_recentes(conexao, dias=7)
        if not recentes:
            print("  Nenhuma vaga encontrada nesse período.")
        for titulo, empresa, cidade, data in recentes:
            print(f"  [{data}] {titulo} — {empresa} ({cidade})")

        print("\n" + "=" * 60)

    finally:
        conexao.close()


if __name__ == "__main__":
    imprimir_relatorio()
