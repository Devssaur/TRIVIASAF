import os
from flask import Blueprint, jsonify
from supabase import Client, create_client

dados_bp = Blueprint("dados_bp", __name__)


def _get_supabase_client() -> Client:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        raise RuntimeError("Variaveis SUPABASE_URL e SUPABASE_KEY nao configuradas.")

    return create_client(supabase_url, supabase_key)


@dados_bp.route("/locais", methods=["GET"])
def listar_locais():
    try:
        supabase = _get_supabase_client()
        result = (
            supabase.table("locais_instalacao")
            .select("*")
            .order("descricao")
            .execute()
        )
        return jsonify({"locais": result.data, "total": len(result.data)}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@dados_bp.route("/equipamentos/<local_id>", methods=["GET"])
def listar_equipamentos_por_local(local_id):
    try:
        supabase = _get_supabase_client()
        result = (
            supabase.table("equipamentos")
            .select("*")
            .eq("local_instalacao_id", local_id)
            .order("descricao")
            .execute()
        )
        return jsonify({"equipamentos": result.data, "total": len(result.data)}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@dados_bp.route("/sintomas/<equipamento_id>", methods=["GET"])
def listar_sintomas_por_equipamento(equipamento_id):
    try:
        supabase = _get_supabase_client()
        result = (
            supabase.table("sintomas_catalogo")
            .select("*")
            .order("descricao")
            .execute()
        )
        return jsonify({"sintomas": result.data, "total": len(result.data)}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
