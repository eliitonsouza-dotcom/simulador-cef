# -*- coding: utf-8 -*-
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r"C:\Users\User\Desktop\@@logos\simulador-cef")

from playwright.sync_api import sync_playwright

URL = "https://www.portaldeempreendimentos.caixa.gov.br/simulador/"

def run():
    with sync_playwright() as p:
        b    = p.chromium.launch(headless=False, slow_mo=300)
        ctx  = b.new_context(viewport={"width":1280,"height":900}, locale="pt-BR")
        page = ctx.new_page()
        page.set_default_timeout(30000)

        page.goto(URL, wait_until="networkidle")
        page.select_option("#origemRecurso", label="FGTS - FUNDO DE GARANTIA POR TEMPO DE SERVICO")
        page.locator("a").filter(has_text="AVANÇAR").click()
        page.wait_for_load_state("networkidle")

        page.select_option("#categoriaImovel", label="CONSTRUCAO/AQ TER CONST - IM. PLANTA E COLETIVAS")

        # Clica no campo cidade e digita
        cidade_input = page.locator("input[name='cidade']")
        cidade_input.click()
        cidade_input.fill("")
        cidade_input.type("Sinop", delay=100)
        page.wait_for_timeout(3000)  # aguarda AJAX

        page.screenshot(path="dbg5_autocomplete.png")
        print("Screenshot autocomplete: dbg5_autocomplete.png")

        # Mostrar tudo que apareceu na pagina apos digitar
        print("\n=== HTML do campo cidade e vizinhanca ===")
        html = page.locator("input[name='cidade']").evaluate(
            "el => el.parentElement.parentElement.innerHTML"
        )
        print(html[:3000])

        print("\n=== Todos elementos visiveis que contem 'Sinop' ===")
        for el in page.locator("*").all():
            try:
                txt = el.inner_text().strip()
                if "sinop" in txt.lower() and len(txt) < 80 and el.is_visible():
                    tag = el.evaluate("el => el.tagName")
                    cls = el.get_attribute("class") or ""
                    eid = el.get_attribute("id") or ""
                    print(f"  <{tag}> class='{cls}' id='{eid}' text='{txt}'")
            except: pass

        print("\n=== Tentando pressionar ArrowDown + Enter ===")
        cidade_input.press("ArrowDown")
        page.wait_for_timeout(500)
        page.screenshot(path="dbg5_arrowdown.png")
        print("Screenshot arrowdown: dbg5_arrowdown.png")

        cidade_input.press("Enter")
        page.wait_for_timeout(500)
        val = cidade_input.input_value()
        print(f"  Valor do campo cidade apos Enter: '{val}'")

        # Preenche resto e tenta avancar
        page.fill("input[name='valorImovel']", "235.000,00")
        page.wait_for_timeout(300)
        page.fill("input[name='renda']", "2.500,00")
        page.wait_for_timeout(300)
        page.check("#checkbox")  # FGTS 3 anos

        page.screenshot(path="dbg5_preenchido.png")
        print("Screenshot preenchido: dbg5_preenchido.png")

        # Clicar AVANÇAR
        page.locator("a").filter(has_text="AVANÇAR").click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        print(f"\n  URL apos AVANCAR: {page.url}")
        page.screenshot(path="dbg5_pos_avancar.png")
        print("Screenshot pos-avancar: dbg5_pos_avancar.png")

        b.close()
        print("Done.")

if __name__ == "__main__":
    run()
