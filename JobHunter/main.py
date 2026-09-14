"""
main.py

Ponto de entrada do JobHunter.

Fluxo:
    1. Garante que o banco de dados SQLite existe (init_db).
    2. Mostra o menu de perfis de busca salvos (perfis/perfil_manager.py)
       — a pessoa escolhe rodar um, vários, todos, criar um novo perfil,
       ou fazer uma busca avulsa sem salvar.
    3. Para cada perfil escolhido, instancia todos os scrapers ativos
       (padrão Strategy) já configurados com o cargo e a cidade daquele
       perfil.
    4. Para cada vaga encontrada: salva no banco (ignorando duplicatas
       pelo link) e, se for realmente nova, dispara notificação no
       Telegram.

Uso:
    python main.py

Para adicionar uma nova plataforma no futuro (LinkedIn, Indeed etc.):
crie uma classe em /scrapers herdando de BaseScraper e adicione-a à
lista SCRAPERS_DISPONIVEIS abaixo. Nada mais precisa mudar.
"""

import asyncio

from database.db import init_db, get_session, salvar_vaga, atualizar_status
from database.models import StatusVaga
from notifications.telegram_notifier import enviar_notificacao
from perfis.perfil_manager import escolher_perfis_para_rodar
from scrapers.gupy_scraper import GupyScraper
from scrapers.vagas_scraper import VagasScraper
from scrapers.infojobs_scraper import InfoJobsScraper
from scrapers.catho_scraper import CathoScraper

# Classes de scraper disponíveis (não instanciadas ainda — cada perfil
# gera suas próprias instâncias, já que cargo/cidade mudam por perfil).
SCRAPERS_DISPONIVEIS = [
    GupyScraper,
    VagasScraper,
    InfoJobsScraper,
    CathoScraper,
]


async def executar_scraper(scraper_classe, cargo: str, cidade: str) -> list:
    scraper = scraper_classe(cargo=cargo, cidade=cidade)
    nome = scraper.NOME_FONTE
    print(f"  [{nome}] buscando...")
    try:
        vagas = await scraper.buscar_vagas()
        print(f"  [{nome}] {len(vagas)} vaga(s) relevante(s) encontrada(s).")
        return vagas
    except Exception as erro:
        print(f"  [{nome}] ERRO durante a busca: {erro}")
        return []


async def rodar_perfil(perfil: dict) -> list:
    print(f"\n>>> Perfil: {perfil['nome']}  (cargo: {perfil['cargo']} | cidade: {perfil['cidade']})")

    resultados_por_scraper = await asyncio.gather(
        *(
            executar_scraper(scraper_classe, perfil["cargo"], perfil["cidade"])
            for scraper_classe in SCRAPERS_DISPONIVEIS
        )
    )
    vagas = [vaga for lista in resultados_por_scraper for vaga in lista]

    # Marca de qual perfil cada vaga veio, para rastreabilidade no banco
    for vaga in vagas:
        vaga["perfil_busca"] = perfil["nome"]

    return vagas


async def rodar_jobhunter() -> None:
    print("=" * 60)
    print("JobHunter — Monitor de vagas personalizável")
    print("=" * 60)

    init_db()

    perfis_escolhidos = escolher_perfis_para_rodar()
    if not perfis_escolhidos:
        print("Nenhum perfil selecionado. Encerrando.")
        return

    todas_as_vagas = []
    for perfil in perfis_escolhidos:
        vagas_do_perfil = await rodar_perfil(perfil)
        todas_as_vagas.extend(vagas_do_perfil)

    novas_vagas_salvas = 0
    duplicatas_ignoradas = 0

    with get_session() as session:
        for dados_vaga in todas_as_vagas:
            vaga_criada = salvar_vaga(session, dados_vaga)

            if vaga_criada is None:
                duplicatas_ignoradas += 1
                continue

            novas_vagas_salvas += 1

            enviado_com_sucesso = enviar_notificacao(vaga_criada)
            if enviado_com_sucesso:
                atualizar_status(session, vaga_criada.id, StatusVaga.NOTIFICADA)

    print("\n" + "-" * 60)
    print("Resumo da execução:")
    print(f"  Vagas novas salvas no banco : {novas_vagas_salvas}")
    print(f"  Duplicatas ignoradas        : {duplicatas_ignoradas}")
    print("-" * 60)


if __name__ == "__main__":
    asyncio.run(rodar_jobhunter())
