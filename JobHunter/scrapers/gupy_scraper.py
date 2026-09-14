"""
scrapers/gupy_scraper.py

Implementação concreta (Adapter) do BaseScraper para o portal Gupy
(https://portal.gupy.io). Gupy é um SPA (Single Page Application) que
carrega as vagas via JavaScript, por isso o uso do Playwright é
essencial — uma requisição HTTP simples não veria as vagas.

O termo de busca enviado ao site é o primeiro cargo informado no
perfil; os demais termos (e a cidade) são usados como filtro adicional
sobre os resultados, em `_cargo_no_alvo` / `_cidade_no_alvo` (herdados
do BaseScraper).

IMPORTANTE: sites de vaga mudam o HTML com frequência. Os seletores
abaixo refletem a estrutura pública do Gupy no momento da escrita.
Se o robô parar de encontrar vagas, rode com HEADLESS=False no .env
e confira os seletores atuais com o DevTools do navegador.
"""

import urllib.parse
from typing import List, Dict

from playwright.async_api import Page

from scrapers.base_scraper import BaseScraper


class GupyScraper(BaseScraper):
    NOME_FONTE = "Gupy"

    BASE_URL = "https://portal.gupy.io/job-search/term={termo}"

    async def _extrair_vagas(self, page: Page) -> List[Dict]:
        termo_principal = self.termos_cargo[0] if self.termos_cargo else ""
        termo_codificado = urllib.parse.quote(termo_principal)
        url = self.BASE_URL.format(termo=termo_codificado)

        vagas_encontradas: List[Dict] = []

        await page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        await self._pausa_humanizada()

        await self._fechar_banner_cookies(page)
        await self._rolar_para_carregar_mais(page)

        cards = page.locator('[data-testid="job-list__item"]')
        total_cards = await cards.count()

        for i in range(total_cards):
            card = cards.nth(i)
            try:
                titulo = await card.locator('[data-testid="job-list__item-title"]').inner_text()
                empresa = await card.locator('[data-testid="job-list__item-company"]').inner_text()
                cidade = await card.locator('[data-testid="job-list__item-location"]').inner_text()
                link_relativo = await card.locator("a").first.get_attribute("href")
            except Exception:
                continue

            if not link_relativo:
                continue

            link_absoluto = urllib.parse.urljoin("https://portal.gupy.io", link_relativo)

            if not self._cargo_no_alvo(titulo) or not self._cidade_no_alvo(cidade):
                continue

            vagas_encontradas.append(
                {
                    "titulo_vaga": titulo.strip(),
                    "empresa": empresa.strip(),
                    "cidade": cidade.strip(),
                    "link_vaga": link_absoluto,
                    "fonte": self.NOME_FONTE,
                }
            )

        return vagas_encontradas

    async def _fechar_banner_cookies(self, page: Page) -> None:
        try:
            botao = page.locator("button", has_text="Aceitar")
            if await botao.count() > 0:
                await botao.first.click(timeout=3000)
        except Exception:
            pass

    async def _rolar_para_carregar_mais(self, page: Page, vezes: int = 5) -> None:
        for _ in range(vezes):
            await page.mouse.wheel(0, 2000)
            await self._pausa_humanizada()
