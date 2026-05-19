# -*- coding: utf-8 -*-
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r"C:\Users\User\Desktop\@@logos\simulador-cef")

from playwright.sync_api import sync_playwright
import re

URL = "https://www.portaldeempreendimentos.caixa.gov.br/simulador/"

def dump_page(page, label, shot):
    page.wait_for_load_state("networkidle")
    page.screenshot(path=shot)
    print(f"\n{'='*60}")
    print(f"{label}  |  {page.url}")

    # selects
    for s in page.locator("select").all():
        try:
            opts = [o.inner_text().strip() for o in s.locator("option").all()]
            print(f"  SEL name='{s.get_attribute('name')}' id='{s.get_attribute('id')}'  opts={opts[:5]}")
        except Exception: pass

    # inputs
    for inp in page.locator("input:visible").all():
        try:
            print(f"  INP type='{inp.get_attribute('type')}' name='{inp.get_attribute('name')}' id='{inp.get_attribute('id')}' placeholder='{inp.get_attribute('placeholder')}'")
        except Exception: pass

    # checkboxes/radios (all, not just visible)
    for inp in page.locator("input[type='checkbox'], input[type='radio']").all():
        try:
            print(f"  CHKRAD type='{inp.get_attribute('type')}' name='{inp.get_attribute('name')}' id='{inp.get_attribute('id')}' value='{inp.get_attribute('value')}'")
        except Exception: pass

    # links que parecem botoes avancar
    for a in page.locator("a, button, input[type='submit'], input[type='button']").all():
        try:
            val = a.get_attribute("value") or ""
            try:
                txt = a.inner_text().strip()
            except Exception:
                txt = val
            if txt or val:
                print(f"  BTN txt='{txt[:40]}' val='{val[:40]}' id='{a.get_attribute('id')}' href='{a.get_attribute('href') or ''}'")
        except Exception: pass

def click_avancar(page):
    for sel in [
        "input[value='AVANÇAR']", "input[value='Avan&#231;ar']",
        "input[value='AVANCAR']", "input[type='submit'][value*='VAN']",
        "input[type='button'][value*='VAN']",
        "button:has-text('AVANÇAR')", "button:has-text('Avançar')",
        "a:has-text('AVANÇAR')", "a:has-text('Avançar')",
        "[onclick*='avancar' i]", "[onclick*='avancar' i]",
    ]:
        try:
            el = page.locator(sel).first
            if el.is_visible():
                print(f"  [AVANCAR] clicando via '{sel}'")
                el.click()
                return True
        except Exception:
            pass
    # fallback: qualquer coisa com texto AVAN
    for el in page.locator("input, button, a").all():
        try:
            val = (el.get_attribute("value") or "") + (el.get_attribute("onclick") or "")
            txt = ""
            try: txt = el.inner_text()
            except Exception: pass
            combined = (val + txt).upper()
            if "AVAN" in combined and el.is_visible():
                print(f"  [AVANCAR fallback] clicando texto='{txt[:30]}' val='{val[:30]}'")
                el.click()
                return True
        except Exception:
            pass
    print("  [AVANCAR] NAO ENCONTRADO")
    return False

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx  = browser.new_context(viewport={"width":1280,"height":900}, locale="pt-BR")
        page = ctx.new_page()
        page.set_default_timeout(30000)

        page.goto(URL, wait_until="networkidle")
        dump_page(page, "PAGE 1", "dbg_p1.png")

        # P1: selecionar FGTS
        page.select_option("#origemRecurso", label="FGTS - FUNDO DE GARANTIA POR TEMPO DE SERVICO")
        print("  [P1] origemRecurso = FGTS selecionado")
        page.wait_for_timeout(500)

        click_avancar(page)
        page.wait_for_load_state("networkidle")
        dump_page(page, "PAGE 2", "dbg_p2.png")

        # P2: tentar preencher e avancar
        # category
        try:
            page.select_option("select[name*='categoria' i], select[id*='categoria' i]",
                               label=re.compile(r"CONSTRU.*PLANTA", re.I))
            print("  [P2] categoria selecionada")
        except Exception as e:
            print(f"  [P2] categoria ERRO: {e}")

        click_avancar(page)
        page.wait_for_load_state("networkidle")
        dump_page(page, "PAGE 3 (pos categoria)", "dbg_p3.png")

        browser.close()
        print("\nScreenshots: dbg_p1.png dbg_p2.png dbg_p3.png")

if __name__ == "__main__":
    run()
