# -*- coding: utf-8 -*-
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r"C:\Users\User\Desktop\@@logos\simulador-cef")

from playwright.sync_api import sync_playwright

URL = "https://www.portaldeempreendimentos.caixa.gov.br/simulador/"

def snap(page, name):
    page.wait_for_load_state("networkidle")
    page.screenshot(path=f"d7_{name}.png")
    print(f"\n=== [{name}]  {page.url}")

def avancar(page):
    page.locator("a").filter(has_text="AVANÇAR").click()
    page.wait_for_load_state("networkidle")

def run():
    with sync_playwright() as p:
        b    = p.chromium.launch(headless=True)
        ctx  = b.new_context(viewport={"width":1280,"height":900}, locale="pt-BR")
        page = ctx.new_page()
        page.set_default_timeout(40000)

        # P1
        page.goto(URL, wait_until="networkidle")
        page.select_option("#origemRecurso", label="FGTS - FUNDO DE GARANTIA POR TEMPO DE SERVICO")
        avancar(page)

        # P2
        page.select_option("#categoriaImovel", label="CONSTRUCAO/AQ TER CONST - IM. PLANTA E COLETIVAS")
        page.locator("#cidade").type("Sinop", delay=80)
        page.wait_for_timeout(2500)
        page.keyboard.press("ArrowDown")
        page.wait_for_timeout(400)
        page.keyboard.press("Enter")
        print(f"  cidade = '{page.locator('#cidade').input_value()}'")
        page.fill("#valorImovel", "235.000,00")
        page.fill("#renda", "2.500,00")
        page.check("#checkbox")
        avancar(page)

        # P3
        page.select_option("#codLegislacao", value="528")
        avancar(page)

        # P4
        page.fill("#dataNascimento", "07/01/1998")
        avancar(page)
        page.wait_for_timeout(1500)
        snap(page, "p5_enquadramentos_ajaxwait")

        # Dump HTML to find 3280
        print("\n  [P5] Procurando 3280 no HTML...")
        html = page.content()
        idx = html.find("3280")
        if idx >= 0:
            print(f"  Encontrado '3280' em pos {idx}: ...{html[max(0,idx-100):idx+200]}...")
        else:
            print("  '3280' NAO encontrado no HTML")

        # Click 3280
        page.get_by_text("3280").first.click()
        page.wait_for_load_state("networkidle")
        snap(page, "p6_apolice")

        # P6 - Amortização
        # Verifica checkboxes disponiveis
        print("\n  [P6] Checkboxes:")
        for cb in page.locator("input[type='checkbox']").all():
            try:
                n  = cb.get_attribute("name") or ""
                i  = cb.get_attribute("id") or ""
                # tenta achar label
                lbl = ""
                try:
                    parent = cb.locator("xpath=..")
                    lbl = parent.inner_text().strip()[:80]
                except: pass
                print(f"    name='{n}' id='{i}' label='{lbl}'")
            except: pass

        page.select_option("#rcrRge", value="894")       # PRICE
        page.select_option("#tipologia", value="1")       # Apartamento
        page.fill("#areaUtil", "48,29")
        print(f"  areaUtil = '{page.locator('#areaUtil').input_value()}'")

        avancar(page)
        snap(page, "p7_cronograma")

        print("\n  [P7] Inputs:")
        for inp in page.locator("input").all():
            try:
                t = inp.get_attribute("type") or ""
                if t == "hidden": continue
                print(f"    type='{t}' name='{inp.get_attribute('name')}' id='{inp.get_attribute('id')}'")
            except: pass

        # Preenche meses
        for sel in ["#qtdMeses","input[name='qtdMeses']","input[name*='meses' i]","input[name*='prazo' i]","input[id*='meses' i]"]:
            try:
                el = page.locator(sel).first
                if el.is_visible():
                    el.fill("30")
                    print(f"  meses=30 via '{sel}'")
                    break
            except: pass

        avancar(page)
        snap(page, "p8_pos_cronograma")
        print(f"  URL: {page.url}")

        # segundo AVANÇAR se ainda nao chegou no resultado
        try:
            avancar(page)
            snap(page, "p9_resultado")
            print(f"  URL final: {page.url}")
        except Exception as e:
            print(f"  Segundo avancar erro: {e}")

        b.close()
        print("\nDone.")

if __name__ == "__main__":
    run()
