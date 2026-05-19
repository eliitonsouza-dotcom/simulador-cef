"""
Automação Playwright — Simulador Caixa Econômica Federal
Portal: https://www.portaldeempreendimentos.caixa.gov.br/simulador/

Fluxo mapeado e validado (FGTS / NPMCMV 3280 / Sinop-MT):
  P1 /simulador/                  → origem FGTS
  P2 /selecionacategoriaimovel    → categoria, cidade, valor, renda, FGTS 3 anos
  P3 /informavalorobra            → código legislação (vazio) → avançar
  P4 /participantes               → data nascimento → avançar (AJAX load enquadramentos)
  P5 participantes# (AJAX)        → clicar "3280"
  P6 /selecionaapolice            → PRICE, dependente, tipologia, área privativa
  P7 /informacronogramaobra       → prazoObra=30 → avançar → avançar
  P8 /detalhamento                → captura resultado
"""

import re, logging
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

PDF_DIR = Path(__file__).parent / "pdfs"
PDF_DIR.mkdir(exist_ok=True)

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

TIMEOUT = 120_000
URL     = "https://www.portaldeempreendimentos.caixa.gov.br/simulador/"

EMPREENDIMENTOS = {
    "pacaembu": {"valor": 235_000, "nome": "Pacaembu"},
    "paiaguas":  {"valor": 220_000, "nome": "Paiaguás"},
}


def simular_caixa(empreendimento, renda, data_nascimento,
                  fgts_3anos, dependente, tipologia,
                  nome_cliente="", headless=True):

    emp          = EMPREENDIMENTOS[empreendimento]
    valor_imovel = emp["valor"]

    log.info("Iniciando: %s | renda=%s | nasc=%s | fgts3=%s | dep=%s | tipo=%s",
             emp["nome"], renda, data_nascimento, fgts_3anos, dependente, tipologia)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, slow_mo=100 if not headless else 0)
        ctx     = browser.new_context(viewport={"width": 1280, "height": 900}, locale="pt-BR")
        page    = ctx.new_page()
        page.set_default_timeout(TIMEOUT)

        try:
            # ── P1: Origem de Recursos ───────────────────────────────────────
            log.info("P1 · Origem de recursos")
            page.goto(URL, wait_until="networkidle")
            page.select_option("#origemRecurso",
                               label="FGTS - FUNDO DE GARANTIA POR TEMPO DE SERVICO")
            _avancar(page)

            # ── P2: Categoria / Imóvel ───────────────────────────────────────
            log.info("P2 · Categoria, cidade, valor, renda")
            page.wait_for_url("**/selecionacategoriaimovel**", timeout=TIMEOUT)

            page.select_option("#categoriaImovel",
                               label="CONSTRUCAO/AQ TER CONST - IM. PLANTA E COLETIVAS")

            # Cidade — autocomplete Tapestry (t-autocomplete-menu)
            page.locator("#cidade").type("Sinop", delay=80)
            page.wait_for_timeout(2500)
            page.keyboard.press("ArrowDown")
            page.wait_for_timeout(400)
            page.keyboard.press("Enter")
            log.info("  cidade = %s", page.locator("#cidade").input_value())

            page.fill("#valorImovel", _fmt_brl(valor_imovel))
            page.fill("#renda",       _fmt_brl(_parse_brl(renda)))

            if fgts_3anos:
                page.check("#checkbox")   # "Possui 3 anos de trabalho sob o FGTS"

            _avancar(page)

            # ── P3: Código de Legislação ─────────────────────────────────────
            log.info("P3 · Código legislação (vazio)")
            page.wait_for_url("**/informavalorobra**", timeout=TIMEOUT)
            # Deixa codLegislacao VAZIO — selecionar 528 filtra errado
            _avancar(page)

            # ── P4: Participante — data de nascimento ────────────────────────
            log.info("P4 · Data de nascimento")
            page.wait_for_url("**/participantes**", timeout=TIMEOUT)

            dt = _to_ddmmyyyy(data_nascimento)
            page.fill("#dataNascimento", dt)
            log.info("  dataNascimento = %s", dt)

            _avancar(page)

            # ── P5: Enquadramentos (AJAX na mesma URL participantes#) ─────────
            log.info("P5 · Aguardando enquadramento 3280")
            page.wait_for_selector("text=3280", timeout=TIMEOUT)
            page.get_by_text("3280").first.click()
            page.wait_for_url("**/selecionaapolice**", timeout=TIMEOUT)

            # ── P6: Sistema de Amortização e Apólice ────────────────────────
            log.info("P6 · Amortização PRICE + tipologia")
            page.select_option("#rcrRge",    value="894")  # PRICE FGTS

            if dependente:
                # name='possuiMaisUmParticipante' é o checkbox "Possui dependentes?"
                page.check("input[name='possuiMaisUmParticipante']")
                log.info("  dependente marcado")

            tipo_val = "1" if tipologia == "apartamento" else "2"
            page.select_option("#tipologia", value=tipo_val)

            area = "48,29" if tipologia == "apartamento" else "43,85"
            page.fill("#areaUtil", area)
            log.info("  tipologia=%s area=%s", tipologia, area)

            _avancar(page)

            # ── P7: Cronograma — 30 meses ─────────────────────────────────────
            log.info("P7 · Cronograma 30 meses")
            page.wait_for_url("**/informacronogramaobra**", timeout=TIMEOUT)
            page.fill("input[name='prazoObra']", "30")

            _avancar(page)   # 1º AVANÇAR (URL vira informacronogramaobra#)
            _avancar(page)   # 2º AVANÇAR (vai para detalhamento)

            # ── P8: Captura resultado ────────────────────────────────────────
            log.info("P8 · Capturando resultado")
            page.wait_for_url("**/detalhamento**", timeout=TIMEOUT)
            page.wait_for_load_state("networkidle")

            body   = page.inner_text("body")
            result = _parse(body)

            result["nome_cliente"]        = nome_cliente
            result["empreendimento"]      = emp["nome"]
            result["valor_imovel_input"]  = _fmt_brl(valor_imovel)
            result["fgts_3anos"]          = fgts_3anos
            result["dependente"]          = dependente
            result["tipologia"]           = tipologia

            # ── PDF da página da Caixa ────────────────────────────────────────
            safe = re.sub(r'[^\w\s-]', '', nome_cliente or "Simulacao").strip().replace(' ', '_') or "Simulacao"
            pdf_name = f"CEF_{safe}_{datetime.now().strftime('%d-%m-%Y')}.pdf"
            pdf_path = str(PDF_DIR / pdf_name)
            page.pdf(path=pdf_path, format="A4", print_background=True)
            result["pdf_filename"] = pdf_name
            log.info("PDF · %s", pdf_name)

            log.info("OK · Prestação = %s | Entrada = %s",
                     result.get("primeira_prestacao", "?"),
                     result.get("valor_entrada", "?"))
            return result

        except PWTimeout as exc:
            log.error("Timeout: %s", exc)
            raise Exception("Timeout ao aguardar resposta da Caixa. Verifique sua conexão e tente novamente.")
        except Exception as exc:
            log.error("Erro na simulação: %s", exc)
            raise
        finally:
            browser.close()


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _avancar(page):
    """Clica no link AVANÇAR e aguarda carregamento."""
    page.locator("a").filter(has_text="AVANÇAR").click()
    page.wait_for_load_state("networkidle")


def _to_ddmmyyyy(dt_str: str) -> str:
    """YYYY-MM-DD → DD/MM/YYYY. Aceita também DD/MM/YYYY."""
    if "-" in dt_str:
        p = dt_str.split("-")
        return f"{p[2]}/{p[1]}/{p[0]}"
    return dt_str


def _parse_brl(s) -> float:
    """'2.890,00' ou '2890.00' ou 2890 → float"""
    if isinstance(s, (int, float)):
        return float(s)
    s = str(s).strip()
    # Formato BRL: ponto = milhar, vírgula = decimal
    if ',' in s:
        s = s.replace('.', '').replace(',', '.')
    return float(s)


def _fmt_brl(value) -> str:
    """235000 → '235.000,00'"""
    return f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _parse(text: str) -> dict:
    """Extrai os valores da página /detalhamento."""
    fields = {
        "valor_imovel":        r"Valor do im[oó]vel:\s*(R\$\s*[\d.,]+)",
        "prazo_maximo":        r"Prazo M[aá]ximo:\s*([\d]+\s*meses?)",
        "sistema_amortizacao": r"Sistema de Amortiza[cç][aã]o:\s*([A-Z][^\n\r]{1,30})",
        "cota_financiamento":  r"Cota m[aá]x\.?\s*financiamento:\s*([\d,]+%)",
        "valor_entrada":       r"Valor de entrada:\s*(R\$\s*[\d.,]+)",
        "desconto":            r"Desconto:\s*(R\$\s*[\d.,]+)",
        "valor_financiamento": r"Valor de Financiamento[^:\n]*:\s*(R\$\s*[\d.,]+)",
        "despesa_cartoria":    r"Despesa Cartori[aá]ria/Leiloeiro:\s*(R\$\s*[\d.,]+)",
        "apolice":             r"Ap[oó]lice de Seguro:\s*([\d]+)",
        "seguro_vista":        r"Seguro [aà] vista\s*(R\$\s*[\d.,]+)",
        "amortizacao_juros":   r"Amortiza[cç][aã]o \+ Juros\s*(R\$\s*[\d.,]+)",
        "seguro_dfi":          r"Seguro DFI\s*(R\$\s*[\d.,]+)",
        "seguro_mip":          r"Seguro MIP\s*(R\$\s*[\d.,]+)",
        "total_seguros":       r"Total Seguros\s*(R\$\s*[\d.,]+)",
        "taxa_adm":            r"Taxa de administra[cç][aã]o\s*(R\$\s*[\d.,]+)",
    }

    result = {}
    for key, pat in fields.items():
        m = re.search(pat, text, re.I)
        if m:
            result[key] = m.group(1).strip()

    # Primeira Prestação — valor aparece algumas linhas APÓS o cabeçalho
    m_pp = re.search(
        r"Primeira Presta[cç][aã]o[\s\S]{0,400}?(R\$\s*[\d.,]+)", text, re.I
    )
    if m_pp:
        result["primeira_prestacao"] = m_pp.group(1)

    # TOTAL da prestação — pega o TOTAL da seção "Componentes da prestação"
    m_comp = re.search(
        r"Componentes da presta[cç][aã]o[\s\S]{0,600}?\bTOTAL\b\s*(R\$\s*[\d.,]+)", text, re.I
    )
    if m_comp:
        result["total_prestacao"] = m_comp.group(1)
    else:
        # fallback: último TOTAL do texto
        todos = re.findall(r"\bTOTAL\b\s*(R\$\s*[\d.,]+)", text, re.I)
        if todos:
            result["total_prestacao"] = todos[-1]

    # Juros — vêm em colunas separadas por tab/espaço
    m_juros = re.search(
        r"Juros Nominais\s+Juros Efetivos[\s\S]{0,100}?([\d,]+%)\s+([\d,]+%)", text, re.I
    )
    if m_juros:
        result["juros_nominais"] = m_juros.group(1)
        result["juros_efetivos"] = m_juros.group(2)
    else:
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        for l in lines:
            if re.match(r"^[\d,]+%$", l):
                if "juros_nominais" not in result:
                    result["juros_nominais"] = l
                elif "juros_efetivos" not in result:
                    result["juros_efetivos"] = l
                    break

    return result
