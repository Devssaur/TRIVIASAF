import os
from dotenv import load_dotenv
from flask import Blueprint, jsonify, request
from supabase import Client, create_client

load_dotenv()

auth_bp = Blueprint("auth_bp", __name__)


def _get_supabase_client() -> Client:
	supabase_url = os.getenv("SUPABASE_URL")
	supabase_key = os.getenv("SUPABASE_KEY")

	if not supabase_url or not supabase_key:
		raise RuntimeError("Variaveis SUPABASE_URL e SUPABASE_KEY nao configuradas.")

	return create_client(supabase_url, supabase_key)


@auth_bp.route("/debug-usuarios", methods=["GET"])
def debug_usuarios():
    """Rota temporaria para diagnostico. REMOVER antes de ir para producao."""
    try:
        supabase = _get_supabase_client()
        result = supabase.table("usuarios").select("id, nome, email, perfil").execute()
        return jsonify({"usuarios": result.data, "total": len(result.data)}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@auth_bp.route("/login", methods=["POST"])
def login():
	payload = request.get_json(silent=True) or {}
	email = payload.get("email")
	senha = payload.get("senha")

	if not email or not senha:
		return jsonify({"erro": "Credenciais invalidas"}), 401

	try:
		supabase = _get_supabase_client()
	except RuntimeError:
		return jsonify({"erro": "Configuracao do Supabase ausente"}), 500

	result = (
		supabase.table("usuarios")
		.select("id, nome, email, perfil, senha_hash")
		.eq("email", email)
		.limit(1)
		.execute()
	)

	usuarios = result.data or []
	if not usuarios:
		return jsonify({"erro": "Credenciais invalidas"}), 401

	usuario = usuarios[0]

	# Simulacao de validacao de senha. Em producao, usar hash seguro (ex: bcrypt).
	if senha != usuario.get("senha_hash"):
		return jsonify({"erro": "Credenciais invalidas"}), 401

	return (
		jsonify(
			{
				"id": usuario.get("id"),
				"nome": usuario.get("nome"),
				"email": usuario.get("email"),
				"perfil": usuario.get("perfil"),
			}
		),
		200,
	)
