import os
from flask import Blueprint, jsonify, request
from supabase import Client, create_client

auth_bp = Blueprint("auth_bp", __name__)


def _to_app_profile(db_perfil: str) -> str:
    """Normaliza perfis do banco para os códigos usados no front-end."""
    mapa = {
        "Solicitante": "SOLICITANTE",
        "CCM": "CCM",
        "Administrador": "ADMIN",
    }
    return mapa.get(db_perfil, db_perfil)


def _to_db_profile(app_perfil: str) -> str:
    """Converte códigos do app para os rótulos aceitos na constraint do banco."""
    mapa = {
        "SOLICITANTE": "Solicitante",
        "CCM": "CCM",
        "ADMIN": "Administrador",
    }
    return mapa.get(app_perfil, app_perfil)


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
        result = supabase.table("usuarios").select(
            "id, nome, email, perfil, aprovado, empresa, area"
        ).execute()
        return jsonify({"usuarios": result.data, "total": len(result.data)}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@auth_bp.route("/cadastro", methods=["POST"])
def cadastro():
    payload  = request.get_json(silent=True) or {}
    nome     = (payload.get("nome")    or "").strip()
    email    = (payload.get("email")   or "").strip().lower()
    empresa  = (payload.get("empresa") or "").strip()
    area     = (payload.get("area")    or "").strip()
    senha    = payload.get("senha")    or ""

    if not nome or not email or not empresa or not area or not senha:
        return jsonify({"erro": "Preencha todos os campos obrigatórios."}), 400

    try:
        supabase = _get_supabase_client()
    except RuntimeError:
        return jsonify({"erro": "Configuração do Supabase ausente."}), 500

    try:
        resp = supabase.auth.sign_up({
            "email":    email,
            "password": senha,
            "options": {
                "data": {
                    "nome":    nome,
                    "perfil":  "Solicitante",
                    "empresa": empresa,
                    "area":    area,
                }
            }
        })
    except Exception as e:
        msg = str(e)
        msg_lower = msg.lower()
        if "already registered" in msg_lower or "already exists" in msg_lower or "user already registered" in msg_lower:
            return jsonify({"erro": "Este e-mail já está cadastrado."}), 409
        # Retorna o detalhe real do erro para diagnóstico
        return jsonify({"erro": "Não foi possível concluir o cadastro.", "detalhe": msg}), 500

    if resp.user is None:
        # sign_up pode retornar user=None quando e-mail já existe mas confirmação está desabilitada
        return jsonify({"erro": "Este e-mail já está cadastrado ou o cadastro foi bloqueado."}), 409

    return jsonify({"mensagem": "Cadastro realizado! Aguarde aprovação do administrador."}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    payload = request.get_json(silent=True) or {}
    email   = (payload.get("email") or "").strip().lower()
    senha   = payload.get("senha") or ""

    if not email or not senha:
        return jsonify({"erro": "Credenciais inválidas."}), 401

    try:
        supabase = _get_supabase_client()
    except RuntimeError:
        return jsonify({"erro": "Configuração do Supabase ausente."}), 500

    # 1. Autenticar via Supabase Auth
    try:
        resp = supabase.auth.sign_in_with_password({"email": email, "password": senha})
    except Exception:
        return jsonify({"erro": "Credenciais inválidas."}), 401

    if resp.user is None:
        return jsonify({"erro": "Credenciais inválidas."}), 401

    user_id = resp.user.id

    # 2. Buscar perfil e verificar aprovação
    try:
        result = (
            supabase.table("usuarios")
            .select("id, nome, perfil, aprovado, empresa, area")
            .eq("id", user_id)
            .single()
            .execute()
        )
    except Exception:
        return jsonify({"erro": "Erro ao carregar dados do usuário."}), 500

    usuario = result.data
    if not usuario:
        return jsonify({"erro": "Usuário não encontrado."}), 404

    if not usuario.get("aprovado"):
        return jsonify({"erro": "Acesso pendente. Aguarde a aprovação do administrador."}), 403

    return jsonify({
        "id":      usuario["id"],
        "nome":    usuario["nome"],
        "perfil":  _to_app_profile(usuario["perfil"]),
        "empresa": usuario.get("empresa"),
        "area":    usuario.get("area"),
    }), 200
