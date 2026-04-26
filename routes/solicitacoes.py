import os
from flask import Blueprint, jsonify, request
from supabase import Client, create_client

solicitacoes_bp = Blueprint("solicitacoes_bp", __name__)


def _get_supabase_client() -> Client:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        raise RuntimeError("Variaveis SUPABASE_URL e SUPABASE_KEY nao configuradas.")

    return create_client(supabase_url, supabase_key)


@solicitacoes_bp.route("/minhas-safs/<usuario_id>", methods=["GET"])
def listar_minhas_safs(usuario_id):
    try:
        supabase = _get_supabase_client()
    except RuntimeError:
        return jsonify({"erro": "Configuracao do Supabase ausente"}), 500

    try:
        # Busca solicitacoes do usuario com o status vindo de saf_controle_ccm via inner join
        result = (
            supabase.table("saf_solicitacoes")
            .select(
                "id, titulo, descricao_falha, prioridade, url_foto, criado_em, "
                "saf_controle_ccm(status, motivo_devolucao, data_avaliacao)"
            )
            .eq("solicitante_id", usuario_id)
            .order("criado_em", desc=True)
            .execute()
        )

        return jsonify({"solicitacoes": result.data, "total": len(result.data)}), 200

    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@solicitacoes_bp.route("/criar", methods=["POST"])
def criar_saf():
    payload = request.get_json(silent=True) or {}

    titulo = payload.get("titulo")
    descricao = payload.get("descricao")
    usuario_id = payload.get("usuario_id")

    if not titulo or not descricao or not usuario_id:
        return jsonify({"erro": "'titulo', 'descricao' e 'usuario_id' sao obrigatorios."}), 400

    try:
        supabase = _get_supabase_client()
    except RuntimeError:
        return jsonify({"erro": "Configuracao do Supabase ausente"}), 500

    try:
        # 1. Insere na tabela saf_solicitacoes
        nova_saf = (
            supabase.table("saf_solicitacoes")
            .insert({
                "solicitante_id": usuario_id,
                "titulo": titulo,
                "descricao_falha": descricao,
                "local_instalacao_id": payload.get("local_id"),
                "equipamento_id": payload.get("equipamento_id"),
                "prioridade": payload.get("prioridade", "MEDIA"),
            })
            .execute()
        )

        saf_id = nova_saf.data[0]["id"]

        # 2. Cria o registro de controle CCM com status inicial
        supabase.table("saf_controle_ccm").insert({
            "solicitacao_id": saf_id,
            "status": "ABERTA",
        }).execute()

        return jsonify({
            "mensagem": "SAF criada com sucesso.",
            "saf_id": saf_id,
            "status": "ABERTA",
        }), 201

    except Exception as e:
        return jsonify({"erro": str(e)}), 500
