from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
from simulator import simular_caixa, PDF_DIR
from functools import wraps
import threading, webbrowser, time, os

app = Flask(__name__, template_folder="templates")
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-x2-2025")

APP_USER = os.environ.get("APP_USER", "x2")
APP_PASS = os.environ.get("APP_PASS", "x2imob2025")


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


@app.after_request
def cors(r):
    r.headers["Access-Control-Allow-Origin"]  = "*"
    r.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    r.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return r


@app.route("/login", methods=["GET", "POST"])
def login():
    erro = False
    if request.method == "POST":
        u = request.form.get("usuario", "")
        p = request.form.get("senha", "")
        if u == APP_USER and p == APP_PASS:
            session["logged_in"] = True
            return redirect(url_for("index"))
        erro = True
    return render_template("login.html", erro=erro)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/simular", methods=["OPTIONS"])
def simular_options():
    return "", 204


@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/simular", methods=["POST"])
@login_required
def simular():
    data = request.get_json()
    try:
        resultado = simular_caixa(
            empreendimento   = data["empreendimento"],
            renda            = data["renda"],
            data_nascimento  = data["data_nascimento"],
            fgts_3anos       = data["fgts_3anos"],
            dependente       = data["dependente"],
            tipologia        = data["tipologia"],
            nome_cliente     = data.get("nome_cliente", ""),
        )
        return jsonify({"ok": True, "resultado": resultado})
    except Exception as e:
        return jsonify({"ok": False, "erro": str(e)})


@app.route("/pdf/<path:filename>")
@login_required
def baixar_pdf(filename):
    filename = os.path.basename(filename)
    pdf_path = PDF_DIR / filename
    if not pdf_path.exists():
        return jsonify({"erro": "PDF não encontrado"}), 404
    return send_file(str(pdf_path), mimetype="application/pdf",
                     as_attachment=True, download_name=filename)


if __name__ == "__main__":
    def _open():
        time.sleep(1.5)
        webbrowser.open("http://localhost:5055")
    threading.Thread(target=_open, daemon=True).start()
    app.run(host="0.0.0.0", port=5055, debug=False, use_reloader=False)
