"""
Script de diagnóstico — abre o Chromium VISÍVEL e inspeciona o simulador da Caixa
passo a passo, salvando screenshots para identificar os seletores corretos.
"""
from playwright.sync_api import sync_playwright
import json, re, time

URL = "https://www.portaldeempreendimentos.caixa.gov.br/simulador/"
OUT = "debug_resultado.json"

def dump_selects(page, label=""):
    """Mostra todos os <select> e suas opções na página atual."""
    sels = page.locator("select").all()
    print(f"\n── {label} ── {len(sels)} select(s) encontrado(s)")
    for i, s in enumerate(sels):
        try:
            opts = [o.inner_text().strip() for o in s.locator("option").all()]
            print(f"  select[{i}] name={s.get_attribute('name')} id={s.get_attribute('id')}")
            print(f"    opções: {opts[:8]}")
        except Exception as e:
            print(f"  select[{i}] erro: {e}")

def dump_inputs(page, label=""):
    """Mostra todos os inputs visíveis."""
    inputs = page.locator("input:visible").all()
    print(f"\n── {label} ── {len(inputs)} input(s) visível(is)")
    for i, el in enumerate(inputs):
        try:
            print(f"  input[{i}] type={el.get_attribute('type')} "
                  f"name={el.get_attribute('name')} id={el.get_attribute('id')} "
                  f"placeholder={el.get_attribute('placeholder')}")
        except Exception as e:
            print(f"  input[{i}] erro: {e}")

def dump_buttons(page, label=""):
    """Mostra botões e links visíveis."""
    btns = page.locator("button:visible, input[type='submit']:visible, input[type='button']:visible, a.btn:visible").all()
    print(f"\n── {label} ── {len(btns)} botão(ões)")
    for b in btns:
        try:
            print(f"  [{b.tag_name()}] text='{b.inner_text().strip()[:60]}' "
                  f"value='{b.get_attribute('value')}' class='{b.get_attribute('class')}'")
        except Exception:
            pass

def wait_and_shot(page, step, desc):
    page.wait_for_load_state("networkidle", timeout=30000)
    page.screenshot(path=f"debug_step{step:02d}.png")
    print(f"\n{'='*55}")
    print(f"STEP {step}: {desc}")
    print(f"  URL: {page.url}")
    print(f"  Título: {page.title()}")
    print(f"  Screenshot: debug_step{step:02d}.png")

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=400)
        ctx  = browser.new_context(viewport={"width": 1280, "height": 900}, locale="pt-BR")
        page = ctx.new_page()
        page.set_default_timeout(30000)

        try:
            # ── STEP 1 ──────────────────────────────────────────────────────
            print("Abrindo simulador Caixa...")
            page.goto(URL, wait_until="networkidle")
            wait_and_shot(page, 1, "Página inicial do simulador")
            dump_selects(page, "STEP1")
            dump_inputs(page, "STEP1")
            dump_buttons(page, "STEP1")

            # Tenta selecionar FGTS
            sels = page.locator("select").all()
            fgts_sel = None
            for s in sels:
                opts = [o.inner_text().strip() for o in s.locator("option").all()]
                for opt in opts:
                    if re.search(r"FGTS.*GARANTIA", opt, re.I):
                        fgts_sel = s
                        fgts_opt = opt
                        break
                if fgts_sel:
                    break

            if fgts_sel:
                print(f"\n✅ FGTS encontrado: '{fgts_opt}'")
                fgts_sel.select_option(label=fgts_opt)
            else:
                print("\n❌ FGTS NÃO encontrado — veja debug_step01.png")
                input("Pressione Enter para continuar mesmo assim...")

            # Clica AVANÇAR
            btn = _find_avancar(page)
            if btn:
                print(f"✅ Botão AVANÇAR: '{btn.inner_text().strip()}'")
                btn.click()
            else:
                print("❌ Botão AVANÇAR não encontrado")
                input("Pressione Enter para continuar...")

            # ── STEP 2 ──────────────────────────────────────────────────────
            page.wait_for_load_state("networkidle")
            wait_and_shot(page, 2, "Dados do imóvel")
            dump_selects(page, "STEP2")
            dump_inputs(page, "STEP2")
            dump_buttons(page, "STEP2")

            # ── STEP 3 (avançar legislação) ──────────────────────────────────
            btn = _find_avancar(page)
            if btn:
                btn.click()
                page.wait_for_load_state("networkidle")
            wait_and_shot(page, 3, "Código de legislação")
            dump_selects(page, "STEP3")
            dump_inputs(page, "STEP3")
            dump_buttons(page, "STEP3")

            print("\n\nDiagnóstico parcial concluído.")
            print("Veja os arquivos debug_step01.png, debug_step02.png, debug_step03.png")
            print("Pressione Enter para fechar o navegador.")
            input()

        except Exception as e:
            page.screenshot(path="debug_erro.png")
            print(f"\n❌ Erro: {e}")
            print("Screenshot salvo: debug_erro.png")
            input("Pressione Enter para fechar...")
        finally:
            browser.close()

def _find_avancar(page):
    for sel in [
        "button:has-text('AVANÇAR')",
        "input[type='submit'][value*='AVAN']",
        "input[type='button'][value*='AVAN']",
        "button:has-text('Avançar')",
        "a:has-text('AVAN')",
    ]:
        try:
            el = page.locator(sel).first
            if el.is_visible():
                return el
        except Exception:
            pass
    return None

if __name__ == "__main__":
    import os
    os.chdir(r"C:\Users\User\Desktop\@@logos\simulador-cef")
    run()
