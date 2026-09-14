"""
scrapers/vagas_scraper.py

Implementação concreta (Adapter) do BaseScraper para o portal Vagas.com
(https://www.vagas.com.br). Segue exatamente o mesmo contrato do
BaseScraper — por isso o main.py trata Gupy e Vagas.com de forma
intercambiável (padrão Strategy).

IMPORTANTE: assim como no Gupy, os seletores CSS abaixo refletem a
estrutura pública do site no momento da escrita e podem precisar de
ajuste se o Vagas.com alterar o layout.
"""

import urllib.parse
from typing import List, Dict

from playwright.async_api import Page

from scrapers.base_scraper import BaseScraper


class VagasScraper(BaseScraper):
    NOME_FONTE = "Vagas.com"

    BASE_URL = "https://www.vagas.com.br/vagas-de-{termo}"

    async def _extrair_vagas(self, page: Page) -> List[Dict]:
        termo_principal = self.termos_cargo[0] if self.termos_cargo else ""
        termo_slug = urllib.parse.quote(termo_principal.replace(" ", "-"))
        url = self.BASE_URL.format(termo=termo_slug)

        vagas_encontradas: List[Dict] = []

        await page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        await self._pausa_humanizada()

        await self._fechar_banner_cookies(page)

        cards = page.locator("li.vaga")
        total_cards = await cards.count()

        for i in range(total_cards):
            card = cards.nth(i)
            try:
                link_el = card.locator("a.link-detalhes-vaga").first
                titulo = (await link_el.get_attribute("title")) or await link_el.inner_text()
                empresa = await card.locator(".emprVaga").inner_text()
                cidade = await card.locator(".vaga-local").inner_text()
                link_relativo = await link_el.get_attribute("href")
            except Exception:
                continue

            if not link_relativo:
                continue

            link_absoluto = urllib.parse.urljoin("https://www.vagas.com.br", link_relativo)

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
