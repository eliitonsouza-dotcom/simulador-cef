# -*- coding: utf-8 -*-
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r"C:\Users\User\Desktop\@@logos\simulador-cef")

from playwright.sync_api import sync_playwright

URL = "https://www.portaldeempreendimentos.caixa.gov.br/simulador/"

def snap(page, name):
    page.wait_for_load_state("networkidle")
    page.screenshot(path=f"d6_{name}.png")
    print(f"\n{'='*55}")
    print(f"[{name}]  {page.url}")
    for s in page.locator("select").all():
        try:
            opts = [(o.get_attribute("value"), o.inner_text().strip()) for o in s.locator("option").all()]
            print(f"  SEL name='{s.get_attribute('name')}' id='{s.get_attribute('id')}' current='{s.input_value()}'")
            for v,t in opts[:8]: print(f"    val='{v}' text='{t}'")
        except: pass
    for inp in page.locator("input:visible").all():
        try:
            t = inp.get_attribute("type") or "text"
            if t in ("hidden",): continue
            print(f"  INP type='{t}' name='{inp.get_attribute('name')}' id='{inp.get_attribute('id')}' value='{inp.get_attribute('value') or inp.input_value()}'")
        except: pass
    # links/buttons de navegação
    for a in page.locator("a").all():
        try:
            txt = a.inner_text().strip()
            if txt: print(f"  LINK '{txt}' href='{a.get_attribute('href')}'")
        except: pass

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
        page.locator("input[name='cidade']").type("Sinop", delay=80)
        page.wait_for_timeout(2500)
        page.keyboard.press("ArrowDown")
        page.wait_for_timeout(300)
        page.keyboard.press("Enter")
        page.fill("input[name='valorImovel']", "235.000,00")
        page.fill("input[name='renda']", "2.500,00")
        page.check("#checkbox")
        avancar(page)

        # P3 - Código de Legislação
        snap(page, "p3_legislacao")
        # Pega opcoes do select de codigo legislacao
        sels = page.locator("select").all()
        for s in sels:
            opts = [(o.get_attribute("value"), o.inner_text().strip()) for o in s.locator("option").all()]
            print(f"\n  [P3] Opcoes de legislacao (name={s.get_attribute('name')}):")
            for v,t in opts: print(f"    val='{v}' text='{t}'")
        # Avança sem selecionar (default)
        avancar(page)

        # P4
        snap(page, "p4_participante")

        # Preenche data de nascimento
        for inp in page.locator("input").all():
            try:
                t = inp.get_attribute("type") or ""
                n = inp.get_attribute("name") or ""
                i = inp.get_attribute("id") or ""
                if t == "hidden": continue
                print(f"  [P4-INP] type='{t}' name='{n}' id='{i}'")
            except: pass

        # Tenta preencher data nascimento
        for sel in ["input[name*='nascimento' i]","input[id*='nascimento' i]","input[name*='nasc' i]","input[id*='nasc' i]","input[name*='data' i]","input[id*='data' i]"]:
            try:
                el = page.locator(sel).first
                if el.is_visible():
                    el.fill("")
                    el.type("07/01/1998", delay=80)
                    print(f"  [P4] data preenchida via '{sel}' = {el.input_value()}")
                    break
            except: pass
        avancar(page)

        # P5 - Enquadramentos
        snap(page, "p5_enquadramentos")
        # Procura item 3280
        rows = page.locator("tr, td, li, a").all()
        print("\n  [P5] Elementos com '3280':")
        for r in rows:
            try:
                txt = r.inner_text().strip()
                if "3280" in txt and len(txt) < 200:
                    tag = r.evaluate("el => el.tagName")
                    cls = r.get_attribute("class") or ""
                    print(f"    <{tag}> class='{cls}' text='{txt[:80]}'")
            except: pass
        # Clica em 3280
        try:
            page.locator("tr").filter(has_text="3280").first.click()
            print("  [P5] clicou em 3280 via tr")
        except:
            page.get_by_text("3280").first.click()
            print("  [P5] clicou em 3280 via get_by_text")
        page.wait_for_load_state("networkidle")

        # P6 - Amortização
        snap(page, "p6_amortizacao")
        for s in page.locator("select").all():
            try:
                opts = [(o.get_attribute("value"), o.inner_text().strip()) for o in s.locator("option").all()]
                print(f"\n  [P6-SEL] name='{s.get_attribute('name')}' id='{s.get_attribute('id')}' opts:")
                for v,t in opts: print(f"    val='{v}' text='{t}'")
            except: pass
        for inp in page.locator("input").all():
            try:
                t = inp.get_attribute("type") or "text"
                if t == "hidden": continue
                print(f"  [P6-INP] type='{t}' name='{inp.get_attribute('name')}' id='{inp.get_attribute('id')}'")
            except: pass

        # Seleciona PRICE e avanca
        try:
            for s in page.locator("select").all():
                opts = [o.inner_text().strip() for o in s.locator("option").all()]
                for opt in opts:
                    if "PRICE" in opt.upper():
                        s.select_option(label=opt)
                        print(f"  [P6] PRICE selecionado: '{opt}'")
                        break
        except Exception as e:
            print(f"  [P6] PRICE erro: {e}")

        avancar(page)

        # P7 - Cronograma
        snap(page, "p7_cronograma")
        for inp in page.locator("input").all():
            try:
                t = inp.get_attribute("type") or "text"
                if t == "hidden": continue
                print(f"  [P7-INP] type='{t}' name='{inp.get_attribute('name')}' id='{inp.get_attribute('id')}'")
            except: pass

        # Preenche meses e avanca
        for sel in ["input[name*='meses' i]","input[id*='meses' i]","input[name*='prazo' i]","input[id*='qtd' i]","input[name*='qtd' i]","input[name*='quantidade' i]"]:
            try:
                el = page.locator(sel).first
                if el.is_visible():
                    el.fill("30")
                    print(f"  [P7] meses=30 via '{sel}'")
                    break
            except: pass
        avancar(page)
        snap(page, "p7b_pos1avancar")

        # Segundo AVANÇAR
        try:
            avancar(page)
        except Exception as e:
            print(f"  [P7b] segundo avancar erro: {e}")
        snap(page, "p8_resultado")

        b.close()
        print("\nDone. Screenshots: d6_p*.png")

if __name__ == "__main__":
    run()
