import os
import logging
from flask import Flask, jsonify, render_template
from dotenv import load_dotenv

# Carrega as variaveis antes de importar modulos que dependem delas.
# override=True evita que variaveis antigas do shell mascararem valores do .env.
load_dotenv(override=True)

from routes.auth import auth_bp
from routes.solicitacoes import solicitacoes_bp
from routes.dados_mestres import dados_bp
from routes.ccm import ccm_bp
from routes.sap import sap_bp
from routes.admin import admin_bp

app = Flask(__name__)
app.logger.setLevel(logging.INFO)

# ── Contexto global (disponível em todos os templates) ───────
@app.context_processor
def inject_globals():
    dev_mode = os.environ.get('DEV_MODE', '').lower() in ('1', 'true', 'yes')
    return dict(dev_mode=dev_mode)

# ── Registro de Rotas API ──────────────────────────────────
app.register_blueprint(auth_bp,          url_prefix='/api/auth')
app.register_blueprint(solicitacoes_bp,  url_prefix='/api/solicitacoes')
app.register_blueprint(dados_bp,         url_prefix='/api/dados')
app.register_blueprint(ccm_bp,           url_prefix='/api/ccm')
app.register_blueprint(sap_bp,           url_prefix='/api/sap')
app.register_blueprint(admin_bp,         url_prefix='/api/admin')

# ── Rotas de Front-end (SPA com Jinja2) ───────────────────
@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

# Solicitante
@app.route('/minhassafs')
def minhas_safs():
    return render_template('minhas_safs.html')

@app.route('/novasaf')
def nova_saf():
    return render_template('nova_saf.html')

@app.route('/saf/<saf_id>')
def detalhe_saf(saf_id):
    return render_template('detalhe_saf.html')

@app.route('/editar-saf/<saf_id>')
def editar_saf(saf_id):
    # Reutiliza o mesmo template; o JS detecta a rota e carrega em modo edição
    return render_template('nova_saf.html')

# CCM
@app.route('/filaccm')
def fila_ccm():
    return render_template('fila_ccm.html')

@app.route('/avaliar-saf/<saf_id>')
def avaliar_saf(saf_id):
    return render_template('avaliar_saf.html')

# Admin
@app.route('/admin')
def admin_page():
    return render_template('admin.html')

@app.route('/admin/usuarios')
def admin_usuarios():
    return render_template('admin.html')

@app.route('/admin/logs')
def admin_logs():
    return render_template('admin.html')

# Acesso negado
@app.route('/acesso-negado')
def acesso_negado():
    return render_template('login.html'), 403

if __name__ == "__main__":
    # debug=True é excelente para desenvolvimento (reinicia ao salvar)
    app.run(host="0.0.0.0", port=5000, debug=True)