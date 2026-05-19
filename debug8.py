# -*- coding: utf-8 -*-
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r"C:\Users\User\Desktop\@@logos\simulador-cef")

from playwright.sync_api import sync_playwright

URL = "https://www.portaldeempreendimentos.caixa.gov.br/simulador/"

def snap(page, name):
    page.wait_for_load_state("networkidle")
    page.screenshot(path=f"d8_{name}.png")
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
        page.fill("#valorImovel", "235.000,00")
        page.fill("#renda", "2.500,00")
        page.check("#checkbox")  # FGTS 3 anos
        avancar(page)

        # P3 - Legislação: deixa VAZIO, só avança
        snap(page, "p3_legislacao")
        print("  codLegislacao: deixando VAZIO")
        avancar(page)

        # P4 - Participante
        snap(page, "p4_participante")
        page.fill("#dataNascimento", "07/01/1998")
        avancar(page)

        # P5 - Enquadramentos
        snap(page, "p5_enquadramentos")

        # Mostra o HTML para encontrar 3280
        txt = page.inner_text("body")
        if "3280" in txt:
            print("  '3280' ENCONTRADO no texto da pagina!")
            # Acha linhas com 3280
            for line in txt.split("\n"):
                if "3280" in line:
                    print(f"    linha: '{line.strip()[:120]}'")
        else:
            print("  '3280' NAO encontrado. Texto da pagina:")
            print(txt[:800])

        # Tenta clicar em 3280
        try:
            page.get_by_text("3280").first.click()
            print("  Clicou em 3280!")
            page.wait_for_load_state("networkidle")
        except Exception as e:
            print(f"  Erro ao clicar 3280: {e}")
            # Tenta qualquer link/row com 3280
            for el in page.locator("a, tr, td, span").all():
                try:
                    t = el.inner_text().strip()
                    if "3280" in t and len(t) < 200:
                        el.click()
                        print(f"  Clicou via fallback: '{t[:60]}'")
                        page.wait_for_load_state("networkidle")
                        break
                except: pass

        snap(page, "p6_apolice")

        # P6 - Amortização
        print("\n  [P6] checkboxes e labels:")
        for cb in page.locator("input[type='checkbox']").all():
            try:
                n = cb.get_attribute("name") or ""
                i = cb.get_attribute("id") or ""
                parent_html = cb.evaluate("el => el.parentElement ? el.parentElement.innerText : ''")
                print(f"    name='{n}' id='{i}' parent='{parent_html[:80]}'")
            except: pass

        page.select_option("#rcrRge", value="894")   # PRICE FGTS
        page.select_option("#tipologia", value="1")   # Apartamento
        page.fill("#areaUtil", "48,29")

        # Dependente - encontra o checkbox correto
        for cb in page.locator("input[type='checkbox']").all():
            try:
                parent = cb.evaluate("el => el.parentElement ? el.parentElement.innerText : ''")
                if "dependente" in parent.lower() or "depend" in parent.lower():
                    print(f"  [DEP] checkbox encontrado: '{parent[:60]}'")
                    # nao marca por enquanto
                    break
            except: pass

        avancar(page)
        snap(page, "p7_cronograma")

        print("\n  [P7] Inputs:")
        for inp in page.locator("input").all():
            try:
                t = inp.get_attribute("type") or ""
                if t in ("hidden","submit"): continue
                print(f"    type='{t}' name='{inp.get_attribute('name')}' id='{inp.get_attribute('id')}'")
            except: pass

        # Preenche meses
        for sel in ["#qtdMeses","input[name='qtdMeses']","input[name*='mes' i]","input[name*='prazo' i]","input[id*='mes' i]","input[id*='prazo' i]"]:
            try:
                el = page.locator(sel).first
                if el.is_visible():
                    el.fill("30")
                    print(f"  meses=30 via '{sel}'")
                    break
            except: pass

        avancar(page)
        snap(page, "p8_pos_cronograma1")
        print(f"  URL: {page.url}")

        # Segundo AVANÇAR
        try:
            avancar(page)
            snap(page, "p9_resultado")
            print(f"  URL final: {page.url}")
            # Extrai texto do resultado
            result_txt = page.inner_text("body")
            print("\n  RESULTADO (primeiros 800 chars):")
            print(result_txt[:800])
        except Exception as e:
            print(f"  Erro segundo avancar: {e}")
            page.screenshot(path="d8_erro_final.png")

        b.close()
        print("\nDone.")

if __name__ == "__main__":
    run()
