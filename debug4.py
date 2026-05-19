# -*- coding: utf-8 -*-
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r"C:\Users\User\Desktop\@@logos\simulador-cef")

from playwright.sync_api import sync_playwright
import re

URL = "https://www.portaldeempreendimentos.caixa.gov.br/simulador/"

def dumpall(page, label, shot):
    page.wait_for_load_state("networkidle")
    page.screenshot(path=shot)
    print(f"\n{'='*55}  {label}\n  URL: {page.url}")
    for s in page.locator("select").all():
        try:
            opts = [o.inner_text().strip() for o in s.locator("option").all()]
            print(f"  SEL name='{s.get_attribute('name')}' id='{s.get_attribute('id')}' val='{s.input_value()}' opts={opts[:4]}")
        except: pass
    for inp in page.locator("input").all():
        try:
            t = inp.get_attribute("type") or "text"
            if t in ("hidden","submit","button"): continue
            print(f"  INP type='{t}' name='{inp.get_attribute('name')}' id='{inp.get_attribute('id')}'")
        except: pass
    for a in page.locator("a").filter(has_text=re.compile(r"AVAN|VOLTAR|CONTIN|CALCU", re.I)).all():
        try: print(f"  LINK txt='{a.inner_text().strip()}' href='{a.get_attribute('href')}'")
        except: pass

def go(page):
    page.locator("a").filter(has_text=re.compile(r"AVAN", re.I)).last.click()
    page.wait_for_load_state("networkidle")

def run():
    with sync_playwright() as p:
        b   = p.chromium.launch(headless=True)
        ctx = b.new_context(viewport={"width":1280,"height":900}, locale="pt-BR")
        page = ctx.new_page()
        page.set_default_timeout(30000)

        # P1
        page.goto(URL, wait_until="networkidle")
        page.select_option("#origemRecurso", label="FGTS - FUNDO DE GARANTIA POR TEMPO DE SERVICO")
        go(page)
        dumpall(page, "P2-CATEGORIA", "dbg4_p2.png")

        # P2 - fill all fields
        page.select_option("#categoriaImovel", label="CONSTRUCAO/AQ TER CONST - IM. PLANTA E COLETIVAS")

        # cidade - type and check for autocomplete
        page.fill("input[name='cidade']", "Sinop")
        page.wait_for_timeout(2000)
        # screenshot to see if autocomplete appeared
        page.screenshot(path="dbg4_cidade_autocomplete.png")
        print("\n  [CIDADE] Screenshot autocomplete salvo: dbg4_cidade_autocomplete.png")

        # Check for autocomplete suggestions
        sugs = page.locator("ul li, div.autocomplete li, .ui-autocomplete li, .dropdown-menu li").all()
        print(f"  [CIDADE] {len(sugs)} sugestoes encontradas")
        for sg in sugs:
            try: print(f"    sug: '{sg.inner_text().strip()}'")
            except: pass

        # Try clicking first suggestion or just Tab
        if sugs:
            sugs[0].click()
            print("  [CIDADE] clicou primeira sugestao")
        else:
            page.keyboard.press("Tab")
            print("  [CIDADE] pressionou Tab (sem autocomplete)")

        page.fill("input[name='valorImovel']", "235000")
        page.fill("input[name='renda']", "2500")
        # FGTS 3 anos - checkbox id='checkbox'
        page.check("#checkbox")
        print("  [P2] campos preenchidos")
        go(page)
        dumpall(page, "P3-LEGISLACAO", "dbg4_p3.png")

        go(page)
        dumpall(page, "P4-PARTICIPANTE", "dbg4_p4.png")

        # Data nascimento
        for inp in page.locator("input").all():
            try:
                t = inp.get_attribute("type") or "text"
                n = inp.get_attribute("name") or ""
                i = inp.get_attribute("id") or ""
                print(f"  [P4-INP] type='{t}' name='{n}' id='{i}'")
            except: pass

        browser = b
        browser.close()
        print("\nDone.")

if __name__ == "__main__":
    run()
