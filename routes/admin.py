import os
from flask import Blueprint, jsonify, request
from supabase import Client, create_client

admin_bp = Blueprint("admin_bp", __name__)


def _get_supabase_client() -> Client:
    supabase_url = os.getenv("SUPABASE_URL")
    # Operações admin usam a service_role key para bypasser RLS
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        raise RuntimeError("Variaveis SUPABASE_URL e SUPABASE_SERVICE_KEY nao configuradas.")
    return create_client(supabase_url, supabase_key)


@admin_bp.route("/logs", methods=["GET"])
def listar_logs():
    try:
        supabase = _get_supabase_client()
        result = (
            supabase.table("logs_auditoria")
            .select("*")
            .order("criado_em", desc=True)
            .limit(500)
            .execute()
        )
        return jsonify({"logs": result.data, "total": len(result.data)}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@admin_bp.route("/usuarios", methods=["GET"])
def listar_usuarios():
    try:
        supabase = _get_supabase_client()
        result = (
            supabase.table("usuarios")
            .select("id, nome, email, perfil, aprovado, empresa, area, created_at")
            .order("created_at", desc=True)
            .execute()
        )
        return jsonify({"usuarios": result.data, "total": len(result.data)}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@admin_bp.route("/usuarios/<usuario_id>/aprovar", methods=["POST"])
def aprovar_usuario(usuario_id):
    payload  = request.get_json(silent=True) or {}
    aprovado = payload.get("aprovado", True)   # True = aprovar, False = bloquear
    perfil   = payload.get("perfil")           # opcional: alterar perfil ao mesmo tempo

    update_data = {"aprovado": bool(aprovado)}
    if perfil:
        update_data["perfil"] = perfil

    try:
        supabase = _get_supabase_client()
        supabase.table("usuarios") \
            .update(update_data) \
            .eq("id", usuario_id) \
            .execute()

        sel = (
            supabase.table("usuarios")
            .select("id, nome, email, perfil, aprovado, empresa, area, created_at")
            .eq("id", usuario_id)
            .single()
            .execute()
        )
        if not sel.data:
            return jsonify({"erro": "Usuário não encontrado."}), 404
        return jsonify({"mensagem": "Usuário atualizado com sucesso.", "usuario": sel.data}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@admin_bp.route("/usuarios/<usuario_id>/perfil", methods=["PUT"])
def alterar_perfil(usuario_id):
    payload = request.get_json(silent=True) or {}
    perfil  = (payload.get("perfil") or "").strip()
    if perfil not in ("Solicitante", "CCM", "Administrador"):
        return jsonify({"erro": "Perfil inválido."}), 400

    try:
        supabase = _get_supabase_client()
        supabase.table("usuarios") \
            .update({"perfil": perfil}) \
            .eq("id", usuario_id) \
            .execute()

        # Busca o usuário atualizado (RLS pode impedir retorno direto do update)
        sel = (
            supabase.table("usuarios")
            .select("id, nome, email, perfil, aprovado, empresa, area, created_at")
            .eq("id", usuario_id)
            .single()
            .execute()
        )
        if not sel.data:
            return jsonify({"erro": "Usuário não encontrado."}), 404
        return jsonify({"mensagem": "Perfil atualizado.", "usuario": sel.data}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
