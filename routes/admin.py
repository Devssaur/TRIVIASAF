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


def _registrar_log(supabase: Client, evento: str, payload: dict | None, usuario_id: str | None = None) -> None:
    """Registra auditoria sem bloquear fluxo principal em caso de falha de log."""
    try:
        supabase.table("logs_auditoria").insert({
            "usuario_id": usuario_id,
            "evento": evento,
            "payload": payload or {},
        }).execute()
    except Exception:
        # Log de auditoria nao deve quebrar a funcionalidade principal.
        pass


def _selecionar_usuario_por_id(supabase: Client, usuario_id: str):
    return (
        supabase.table("usuarios")
        .select("id, nome, email, perfil, aprovado, empresa, area, created_at")
        .eq("id", usuario_id)
        .single()
        .execute()
    )


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
    ator_id  = payload.get("ator_id")

    update_data = {"aprovado": bool(aprovado)}
    if perfil:
        update_data["perfil"] = perfil

    try:
        supabase = _get_supabase_client()

        antes_sel = _selecionar_usuario_por_id(supabase, usuario_id)
        antes = antes_sel.data if antes_sel else None

        supabase.table("usuarios") \
            .update(update_data) \
            .eq("id", usuario_id) \
            .execute()

        sel = _selecionar_usuario_por_id(supabase, usuario_id)
        if not sel.data:
            return jsonify({"erro": "Usuário não encontrado."}), 404

        _registrar_log(
            supabase,
            "ADMIN_ALTEROU_ACESSO_USUARIO",
            {
                "alvo_usuario_id": usuario_id,
                "antes": {
                    "aprovado": (antes or {}).get("aprovado"),
                    "perfil": (antes or {}).get("perfil"),
                },
                "depois": {
                    "aprovado": sel.data.get("aprovado"),
                    "perfil": sel.data.get("perfil"),
                },
            },
            ator_id,
        )

        return jsonify({"mensagem": "Usuário atualizado com sucesso.", "usuario": sel.data}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@admin_bp.route("/usuarios/<usuario_id>/perfil", methods=["PUT"])
def alterar_perfil(usuario_id):
    payload = request.get_json(silent=True) or {}
    perfil  = (payload.get("perfil") or "").strip()
    ator_id = payload.get("ator_id")
    if perfil not in ("Solicitante", "CCM", "Administrador"):
        return jsonify({"erro": "Perfil inválido."}), 400

    try:
        supabase = _get_supabase_client()

        antes_sel = _selecionar_usuario_por_id(supabase, usuario_id)
        antes = antes_sel.data if antes_sel else None

        supabase.table("usuarios") \
            .update({"perfil": perfil}) \
            .eq("id", usuario_id) \
            .execute()

        # Busca o usuário atualizado (RLS pode impedir retorno direto do update)
        sel = _selecionar_usuario_por_id(supabase, usuario_id)
        if not sel.data:
            return jsonify({"erro": "Usuário não encontrado."}), 404

        _registrar_log(
            supabase,
            "ADMIN_ALTEROU_PERFIL_USUARIO",
            {
                "alvo_usuario_id": usuario_id,
                "antes": {"perfil": (antes or {}).get("perfil")},
                "depois": {"perfil": sel.data.get("perfil")},
            },
            ator_id,
        )

        return jsonify({"mensagem": "Perfil atualizado.", "usuario": sel.data}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@admin_bp.route("/usuarios/<usuario_id>", methods=["PUT"])
def editar_usuario(usuario_id):
    payload = request.get_json(silent=True) or {}
    ator_id = payload.get("ator_id")

    nome = (payload.get("nome") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    empresa = (payload.get("empresa") or "").strip() or None
    area = (payload.get("area") or "").strip() or None
    perfil = (payload.get("perfil") or "").strip()

    if not nome or not email:
        return jsonify({"erro": "Nome e e-mail são obrigatórios."}), 400
    if perfil not in ("Solicitante", "CCM", "Administrador"):
        return jsonify({"erro": "Perfil inválido."}), 400

    try:
        supabase = _get_supabase_client()
        antes_sel = _selecionar_usuario_por_id(supabase, usuario_id)
        if not antes_sel.data:
            return jsonify({"erro": "Usuário não encontrado."}), 404

        update_data = {
            "nome": nome,
            "email": email,
            "empresa": empresa,
            "area": area,
            "perfil": perfil,
        }

        supabase.table("usuarios").update(update_data).eq("id", usuario_id).execute()
        sel = _selecionar_usuario_por_id(supabase, usuario_id)
        if not sel.data:
            return jsonify({"erro": "Usuário não encontrado após atualização."}), 404

        _registrar_log(
            supabase,
            "ADMIN_ALTEROU_CADASTRO_USUARIO",
            {
                "alvo_usuario_id": usuario_id,
                "antes": {
                    "nome": antes_sel.data.get("nome"),
                    "email": antes_sel.data.get("email"),
                    "empresa": antes_sel.data.get("empresa"),
                    "area": antes_sel.data.get("area"),
                    "perfil": antes_sel.data.get("perfil"),
                },
                "depois": {
                    "nome": sel.data.get("nome"),
                    "email": sel.data.get("email"),
                    "empresa": sel.data.get("empresa"),
                    "area": sel.data.get("area"),
                    "perfil": sel.data.get("perfil"),
                },
            },
            ator_id,
        )

        return jsonify({"mensagem": "Cadastro atualizado com sucesso.", "usuario": sel.data}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@admin_bp.route("/usuarios/<usuario_id>", methods=["DELETE"])
def excluir_usuario(usuario_id):
    payload = request.get_json(silent=True) or {}
    ator_id = payload.get("ator_id")

    try:
        supabase = _get_supabase_client()
        antes_sel = _selecionar_usuario_por_id(supabase, usuario_id)
        if not antes_sel.data:
            return jsonify({"erro": "Usuário não encontrado."}), 404

        # Remove do Auth (quando a FK existe com ON DELETE CASCADE, apaga de usuarios automaticamente).
        supabase.auth.admin.delete_user(usuario_id)

        # Garantia defensiva caso o banco não esteja com cascata configurada.
        supabase.table("usuarios").delete().eq("id", usuario_id).execute()

        _registrar_log(
            supabase,
            "ADMIN_EXCLUIU_USUARIO",
            {
                "alvo_usuario_id": usuario_id,
                "usuario_excluido": {
                    "nome": antes_sel.data.get("nome"),
                    "email": antes_sel.data.get("email"),
                    "perfil": antes_sel.data.get("perfil"),
                    "empresa": antes_sel.data.get("empresa"),
                    "area": antes_sel.data.get("area"),
                },
            },
            ator_id,
        )

        return jsonify({"mensagem": "Usuário excluído com sucesso."}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
