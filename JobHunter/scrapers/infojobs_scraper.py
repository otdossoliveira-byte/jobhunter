"""
scrapers/infojobs_scraper.py

Implementação concreta (Adapter) do BaseScraper para o portal InfoJobs
(https://www.infojobs.com.br). Segue o mesmo contrato dos outros
scrapers — o main.py trata todos de forma intercambiável (Strategy).

IMPORTANTE: os seletores CSS abaixo refletem a estrutura pública do
InfoJobs no momento da escrita e podem precisar de ajuste se o site
mudar o layout. Se o robô parar de achar vagas aqui, rode com
HEADLESS=False no .env e confira os seletores atuais com o DevTools.
"""

import urllib.parse
from typing import List, Dict

from playwright.async_api import Page

from scrapers.base_scraper import BaseScraper


class InfoJobsScraper(BaseScraper):
    NOME_FONTE = "InfoJobs"

    BASE_URL = "https://www.infojobs.com.br/empregos.aspx?palabra={termo}"

    async def _extrair_vagas(self, page: Page) -> List[Dict]:
        termo_principal = self.termos_cargo[0] if self.termos_cargo else ""
        termo_codificado = urllib.parse.quote(termo_principal)
        url = self.BASE_URL.format(termo=termo_codificado)

        vagas_encontradas: List[Dict] = []

        await page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        await self._pausa_humanizada()

        await self._fechar_banner_cookies(page)

        cards = page.locator("div.js_vacancyLoad")
        total_cards = await cards.count()

        for i in range(total_cards):
            card = cards.nth(i)
            try:
                link_el = card.locator("a.js_vacancyLink").first
                titulo = await link_el.inner_text()
                empresa = await card.locator(".text-body-2").first.inner_text()
                cidade = await card.locator("[data-testid='vacancy-location']").inner_text()
                link_relativo = await link_el.get_attribute("href")
            except Exception:
                continue

            if not link_relativo:
                continue

            link_absoluto = urllib.parse.urljoin("https://www.infojobs.com.br", link_relativo)

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
