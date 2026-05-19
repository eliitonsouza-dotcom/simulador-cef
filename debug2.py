# -*- coding: utf-8 -*-
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r"C:\Users\User\Desktop\@@logos\simulador-cef")

from playwright.sync_api import sync_playwright
import re

URL = "https://www.portaldeempreendimentos.caixa.gov.br/simulador/"

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx  = browser.new_context(viewport={"width":1280,"height":900}, locale="pt-BR")
        page = ctx.new_page()
        page.set_default_timeout(30000)

        # ── PAGE 1 ────────────────────────────────────────────────────────
        page.goto(URL, wait_until="networkidle")
        print("=== PAGE 1 SELECTS ===")
        for s in page.locator("select").all():
            name = s.get_attribute("name") or ""
            sid  = s.get_attribute("id") or ""
            opts = [o.inner_text().strip() for o in s.locator("option").all()]
            print(f"  SELECT name='{name}' id='{sid}'")
            for o in opts:
                print(f"    - {o}")

        print("\n=== PAGE 1 RADIOS ===")
        for r in page.locator("input[type='radio']").all():
            print(f"  RADIO name='{r.get_attribute('name')}' value='{r.get_attribute('value')}' id='{r.get_attribute('id')}'")

        print("\n=== PAGE 1 BUTTONS ===")
        for b in page.locator("button, input[type='submit'], input[type='button']").all():
            txt = b.inner_text().strip() if b.tag_name() == "button" else b.get_attribute("value") or ""
            print(f"  BTN tag={b.tag_name()} text='{txt}' name='{b.get_attribute('name')}' id='{b.get_attribute('id')}'")

        # Seleciona FGTS e avanca para ver pagina 2
        print("\n=== SELECTING FGTS ===")
        for s in page.locator("select").all():
            opts = [o.inner_text().strip() for o in s.locator("option").all()]
            for opt in opts:
                if re.search(r"FGTS.*GARANTIA", opt, re.I):
                    s.select_option(label=opt)
                    print(f"  Selecionado: '{opt}' em select name='{s.get_attribute('name')}'")
                    break

        # Clica AVANCAR
        for sel in ["button:has-text('AVANÇAR')", "input[value*='AVAN']"]:
            try:
                el = page.locator(sel).first
                if el.is_visible():
                    el.click()
                    print(f"  Clicou AVANCAR via '{sel}'")
                    break
            except Exception:
                pass
        page.wait_for_load_state("networkidle")
        page.screenshot(path="debug_p2.png")

        print("\n=== PAGE 2 URL:", page.url)
        print("=== PAGE 2 SELECTS ===")
        for s in page.locator("select").all():
            name = s.get_attribute("name") or ""
            sid  = s.get_attribute("id") or ""
            opts = [o.inner_text().strip() for o in s.locator("option").all()]
            print(f"  SELECT name='{name}' id='{sid}'")
            for o in opts[:6]:
                print(f"    - {o}")
            if len(opts) > 6:
                print(f"    ... (+{len(opts)-6} mais)")

        print("\n=== PAGE 2 INPUTS ===")
        for inp in page.locator("input:visible").all():
            print(f"  INPUT type='{inp.get_attribute('type')}' name='{inp.get_attribute('name')}' id='{inp.get_attribute('id')}' placeholder='{inp.get_attribute('placeholder')}'")

        print("\n=== PAGE 2 BUTTONS ===")
        for b in page.locator("button, input[type='submit'], input[type='button']").all():
            txt = b.inner_text().strip() if b.tag_name() == "button" else b.get_attribute("value") or ""
            print(f"  BTN text='{txt}' name='{b.get_attribute('name')}' id='{b.get_attribute('id')}'")

        browser.close()
        print("\nDone. Veja debug_p2.png")

if __name__ == "__main__":
    run()
