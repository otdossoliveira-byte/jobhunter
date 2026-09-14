"""
perfis/perfil_manager.py

Gerencia os perfis de busca salvos pela pessoa (ex: "Admin em Salvador",
"Dev Júnior em São Paulo") e o menu interativo no terminal. Um perfil é
apenas um dicionário simples salvo em JSON — nada de banco de dados
aqui, então a pessoa pode até editar o arquivo `perfis/perfis.json` na
mão se quiser, sem precisar rodar nada.

Formato de cada perfil:
    {
        "nome": "Admin em Salvador",
        "cargo": "assistente administrativo, auxiliar administrativo",
        "cidade": "Salvador, Camaçari"
    }

Tanto `cargo` quanto `cidade` aceitam múltiplos valores separados por
vírgula. Deixar `cidade` em branco (ou "qualquer") remove o filtro de
cidade — a vaga passa a ser aceita em qualquer lugar do Brasil.
"""

import json
import os
from typing import List, Dict, Optional

from config import settings


def _garantir_pasta() -> None:
    pasta = os.path.dirname(settings.PERFIS_FILE)
    if pasta and not os.path.exists(pasta):
        os.makedirs(pasta, exist_ok=True)


def carregar_perfis() -> List[Dict]:
    """Lê os perfis salvos em disco. Retorna lista vazia se o arquivo não existir."""
    if not os.path.exists(settings.PERFIS_FILE):
        return []
    with open(settings.PERFIS_FILE, "r", encoding="utf-8") as arquivo:
        try:
            return json.load(arquivo)
        except json.JSONDecodeError:
            print("[AVISO] perfis.json está corrompido ou vazio — começando do zero.")
            return []


def salvar_perfis(perfis: List[Dict]) -> None:
    _garantir_pasta()
    with open(settings.PERFIS_FILE, "w", encoding="utf-8") as arquivo:
        json.dump(perfis, arquivo, ensure_ascii=False, indent=2)


def criar_novo_perfil() -> Dict:
    """Pergunta os dados de um novo perfil de busca no terminal."""
    print("\n--- Novo perfil de busca ---")
    nome = input("Dê um nome para esse perfil (ex: 'Dev em Salvador'): ").strip()

    cargo = input(
        f"Cargo(s) desejado(s), separados por vírgula [padrão: {settings.DEFAULT_CARGO}]: "
    ).strip()
    if not cargo:
        cargo = settings.DEFAULT_CARGO

    cidade = input(
        f"Cidade(s), separadas por vírgula, ou deixe em branco para 'qualquer cidade' "
        f"[padrão: {settings.DEFAULT_CIDADE}]: "
    ).strip()
    if not cidade:
        cidade = settings.DEFAULT_CIDADE

    return {"nome": nome or cargo, "cargo": cargo, "cidade": cidade}


def escolher_perfis_para_rodar() -> List[Dict]:
    """
    Menu principal exibido ao iniciar o programa. Retorna a lista de
    perfis (dicts) que devem ser efetivamente buscados nessa execução.
    """
    perfis_salvos = carregar_perfis()

    if not perfis_salvos:
        print("Nenhum perfil de busca salvo ainda. Vamos criar o primeiro.")
        perfil = criar_novo_perfil()
        perfis_salvos.append(perfil)
        salvar_perfis(perfis_salvos)
        return perfis_salvos

    print("\n=== JobHunter ===")
    print("Perfis de busca salvos:")
    for indice, perfil in enumerate(perfis_salvos, start=1):
        print(f"  {indice}) {perfil['nome']}  —  cargo: {perfil['cargo']}  |  cidade: {perfil['cidade']}")

    print("\nOpções:")
    print("  [Enter]  Rodar todos os perfis salvos")
    print("  N        Criar um novo perfil e salvá-lo")
    print("  A        Fazer uma busca avulsa agora (não salva perfil)")
    print("  Números  Rodar só perfis específicos (ex: 1,3)")

    escolha = input("\nO que deseja fazer? ").strip().lower()

    if escolha == "":
        return perfis_salvos

    if escolha == "n":
        novo = criar_novo_perfil()
        perfis_salvos.append(novo)
        salvar_perfis(perfis_salvos)
        return [novo]

    if escolha == "a":
        cargo = input(f"Cargo(s) desejado(s) [padrão: {settings.DEFAULT_CARGO}]: ").strip() or settings.DEFAULT_CARGO
        cidade = input(f"Cidade(s) [padrão: {settings.DEFAULT_CIDADE}]: ").strip() or settings.DEFAULT_CIDADE
        return [{"nome": "Busca avulsa", "cargo": cargo, "cidade": cidade}]

    # Tenta interpretar como lista de números (ex: "1,3")
    try:
        indices = [int(n.strip()) - 1 for n in escolha.split(",")]
        return [perfis_salvos[i] for i in indices if 0 <= i < len(perfis_salvos)]
    except ValueError:
        print("Entrada não reconhecida — rodando todos os perfis salvos por segurança.")
        return perfis_salvos
