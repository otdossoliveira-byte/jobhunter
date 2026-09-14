"""
scrapers/catho_scraper.py

Implementação concreta (Adapter) do BaseScraper para o portal Catho
(https://www.catho.com.br). Segue o mesmo contrato dos outros
scrapers — o main.py trata todos de forma intercambiável (Strategy).

IMPORTANTE: os seletores CSS abaixo refletem a estrutura pública do
Catho no momento da escrita e podem precisar de ajuste se o site
mudar o layout. Se o robô parar de achar vagas aqui, rode com
HEADLESS=False no .env e confira os seletores atuais com o DevTools.
"""

import urllib.parse
from typing import List, Dict

from playwright.async_api import Page

from scrapers.base_scraper import BaseScraper


class CathoScraper(BaseScraper):
    NOME_FONTE = "Catho"

    BASE_URL = "https://www.catho.com.br/vagas/{termo}/"

    async def _extrair_vagas(self, page: Page) -> List[Dict]:
        termo_principal = self.termos_cargo[0] if self.termos_cargo else ""
        termo_slug = urllib.parse.quote(termo_principal.replace(" ", "-"))
        url = self.BASE_URL.format(termo=termo_slug)

        vagas_encontradas: List[Dict] = []

        await page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        await self._pausa_humanizada()

        await self._fechar_banner_cookies(page)

        cards = page.locator("[data-testid='job-item']")
        total_cards = await cards.count()

        for i in range(total_cards):
            card = cards.nth(i)
            try:
                titulo = await card.locator("h2").first.inner_text()
                empresa = await card.locator("[data-testid='job-item-company-name']").inner_text()
                cidade = await card.locator("[data-testid='job-item-location']").inner_text()
                link_relativo = await card.locator("a").first.get_attribute("href")
            except Exception:
                continue

            if not link_relativo:
                continue

            link_absoluto = urllib.parse.urljoin("https://www.catho.com.br", link_relativo)

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
