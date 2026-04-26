import os
from flask import Flask, jsonify
from dotenv import load_dotenv
from routes.auth import auth_bp
from routes.solicitacoes import solicitacoes_bp
from routes.dados_mestres import dados_bp
from routes.ccm import ccm_bp

# 1. Carrega as variáveis do arquivo .env
load_dotenv()

app = Flask(__name__)

# 2. Registro de Rotas
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(solicitacoes_bp, url_prefix='/api/solicitacoes')
app.register_blueprint(dados_bp, url_prefix='/api/dados')
app.register_blueprint(ccm_bp, url_prefix='/api/ccm')

@app.route("/")
def index():
    return jsonify({"mensagem": "Sistema SAF Operacional"})

if __name__ == "__main__":
    # debug=True é excelente para desenvolvimento (reinicia ao salvar)
    app.run(debug=True)