"""
scrapers/base_scraper.py

Define o contrato comum (padrão Strategy) que todo scraper de vagas
deve seguir. Cada site (Gupy, Vagas.com, e futuramente LinkedIn/Indeed)
implementa sua própria subclasse (padrão Adapter), traduzindo o HTML
específico daquele site para uma lista de dicionários no formato
padronizado usado pelo restante do sistema:

    {
        "titulo_vaga": str,
        "empresa": str,
        "cidade": str,
        "link_vaga": str,
        "fonte": str,
    }

Diferente da versão anterior, o cargo e a cidade buscados NÃO são mais
fixos em config/settings.py — cada scraper recebe esses critérios no
construtor, vindos do perfil de busca escolhido pela pessoa em tempo
de execução. Isso é o que torna o JobHunter genérico: o mesmo código
serve para procurar "assistente administrativo em Salvador" ou
"desenvolvedor júnior em São Paulo", sem alterar uma linha sequer.
"""

import asyncio
import random
from abc import ABC, abstractmethod
from typing import List, Dict

from playwright.async_api import async_playwright, BrowserContext, Page

from config import settings


class BaseScraper(ABC):
    """Classe abstrata que todo scraper concreto deve herdar."""

    NOME_FONTE: str = "desconhecida"

    def __init__(self, cargo: str, cidade: str):
        """
        cargo:  termos de cargo desejados, separados por vírgula
                (ex: "assistente administrativo, auxiliar administrativo")
        cidade: termos de cidade desejados, separados por vírgula, ou
                vazio/"qualquer" para não filtrar por cidade
        """
        self.cargo_bruto = cargo
        self.cidade_bruta = cidade
        self.termos_cargo = [t.strip() for t in cargo.split(",") if t.strip()]
        self.termos_cidade = [
            t.strip() for t in cidade.split(",")
            if t.strip() and t.strip().lower() not in ("qualquer", "brasil", "qualquer cidade")
        ]

    async def buscar_vagas(self) -> List[Dict]:
        """
        Ponto de entrada público. Cuida do ciclo de vida do navegador
        (abrir/fechar) e delega a lógica específica do site para
        `_extrair_vagas`, que cada subclasse implementa.
        """
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=settings.HEADLESS)
            context = await self._criar_contexto_stealth(browser)
            page = await context.new_page()

            try:
                vagas = await self._extrair_vagas(page)
            finally:
                await context.close()
                await browser.close()

        return vagas

    @abstractmethod
    async def _extrair_vagas(self, page: Page) -> List[Dict]:
        """Lógica específica de cada site. Implementada nas subclasses."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Utilitários compartilhados de "anti-bloqueio"
    # ------------------------------------------------------------------
    async def _criar_contexto_stealth(self, browser) -> BrowserContext:
        context = await browser.new_context(
            user_agent=settings.USER_AGENT,
            viewport=settings.VIEWPORT,
            locale=settings.LOCALE,
            timezone_id=settings.TIMEZONE_ID,
        )
        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )
        return context

    async def _pausa_humanizada(self) -> None:
        tempo = random.uniform(settings.DELAY_MIN, settings.DELAY_MAX)
        await asyncio.sleep(tempo)

    def _cidade_no_alvo(self, texto_cidade: str) -> bool:
        """Se nenhuma cidade foi especificada no perfil, aceita qualquer uma."""
        if not self.termos_cidade:
            return True
        texto = self._normalizar(texto_cidade)
        return any(self._normalizar(c) in texto for c in self.termos_cidade)

    def _cargo_no_alvo(self, titulo: str) -> bool:
        if not self.termos_cargo:
            return True
        texto = self._normalizar(titulo)
        return any(self._normalizar(c) in texto for c in self.termos_cargo)

    @staticmethod
    def _normalizar(texto: str) -> str:
        import unicodedata

        texto = texto.strip().lower()
        texto = unicodedata.normalize("NFKD", texto)
        texto = "".join(c for c in texto if not unicodedata.combining(c))
        return texto
