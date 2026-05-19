# -*- coding: utf-8 -*-
import sys, os, json
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r"C:\Users\User\Desktop\@@logos\simulador-cef")

from simulator import simular_caixa
from playwright.sync_api import sync_playwright

# 1. Roda a simulacao e pega o resultado
print("Simulando... (aguarde ~40s)")
resultado = simular_caixa('pacaembu', '2560', '1995-05-12', True, True, 'casa', 'Joao Guilherme')
print("Simulacao concluida:", resultado.get('primeira_prestacao'))

# 2. Abre a plataforma e injeta o resultado via JS
with sync_playwright() as p:
    b    = p.chromium.launch(headless=True)
    ctx  = b.new_context(viewport={"width": 1100, "height": 950})
    page = ctx.new_page()

    page.goto("http://localhost:5055", wait_until="networkidle")

    # Simula o fluxo real: esconde form, mostra resultado
    page.evaluate(f"""(resultado) => {{
        // Esconde o formulario (como o simular() faz)
        document.getElementById('form-card').style.display = 'none';
        document.getElementById('resultado').style.display = 'none';
        // Mostra o resultado
        mostrarResultado(resultado, {{
            nome: resultado.nome_cliente,
            fgts: resultado.fgts_3anos,
            dep: resultado.dependente,
            emp: resultado.empreendimento,
            tipo: resultado.tipologia
        }});
    }}""", resultado)

    page.wait_for_timeout(600)
    page.screenshot(path="screenshot_plataforma.png", full_page=True)
    print("Screenshot salvo: screenshot_plataforma.png")
    b.close()
