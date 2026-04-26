import os
from dotenv import load_dotenv
from flask import Blueprint, jsonify
from supabase import Client, create_client

load_dotenv()

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
            .select("id_sap, descricao")
            .order("descricao")
            .execute()
        )
        return jsonify({"locais": result.data, "total": len(result.data)}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@dados_bp.route("/equipamentos/<local_id_sap>", methods=["GET"])
def listar_equipamentos_por_local(local_id_sap):
    try:
        supabase = _get_supabase_client()
        result = (
            supabase.table("equipamentos")
            .select("id_sap, descricao")
            .eq("local_id_sap", local_id_sap)
            .order("descricao")
            .execute()
        )
        return jsonify({"equipamentos": result.data, "total": len(result.data)}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@dados_bp.route("/sintomas/<equipamento_id_sap>", methods=["GET"])
def listar_sintomas_por_equipamento(equipamento_id_sap):
    try:
        supabase = _get_supabase_client()
        result = (
            supabase.table("sintomas_catalogo")
            .select("id, sintoma_codigo, descricao")
            .eq("equipamento_id_sap", equipamento_id_sap)
            .order("descricao")
            .execute()
        )
        return jsonify({"sintomas": result.data, "total": len(result.data)}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
        return jsonify({"erro": str(e)}), 500
