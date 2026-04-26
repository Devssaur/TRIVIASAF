import os
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request
from supabase import Client, create_client

ccm_bp = Blueprint("ccm_bp", __name__)

STATUS_PENDENTE = "ABERTA"
STATUS_COMPLEMENTO = "DEVOLVIDA"
STATUS_CONFIRMADO = "APROVADA"
STATUS_CANCELADO = "CANCELADA"

STATUS_PERMITIDOS = {"Necessário Complemento", "Confirmado", "Cancelado"}


def _get_supabase_client() -> Client:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        raise RuntimeError("Variaveis SUPABASE_URL e SUPABASE_KEY nao configuradas.")

    return create_client(supabase_url, supabase_key)


@ccm_bp.route("/pendentes", methods=["GET"])
def listar_pendentes():
    try:
        supabase = _get_supabase_client()

        resposta = (
            supabase.table("saf_solicitacoes")
            .select("id, titulo, descricao_falha, prioridade, usuarios(nome)")
            .execute()
        )

        return jsonify(resposta.data), 200

    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@ccm_bp.route("/avaliar/<saf_id>", methods=["POST"])
def avaliar_saf(saf_id):
    """Avalia uma SAF: Necessário Complemento, Confirmado ou Cancelado."""
    payload = request.get_json(silent=True) or {}
    status_recebido = payload.get("status")
    motivo_complemento = payload.get("motivo_complemento")
    motivo_cancelamento = payload.get("motivo_cancelamento")
    avaliado_por = payload.get("avaliado_por_id")

    if not status_recebido or status_recebido not in STATUS_PERMITIDOS:
        return (
            jsonify(
                {
                    "erro": f"Status invalido. Use um dos: {sorted(STATUS_PERMITIDOS)}"
                }
            ),
            400,
        )

    if not avaliado_por:
        return jsonify({"erro": "Campo 'avaliado_por_id' e obrigatorio."}), 400

    if status_recebido == "Necessário Complemento" and not motivo_complemento:
        return jsonify({"erro": "'motivo_complemento' e obrigatorio para este status."}), 400

    if status_recebido == "Cancelado" and not motivo_cancelamento:
        return jsonify({"erro": "'motivo_cancelamento' e obrigatorio para este status."}), 400

    try:
        supabase = _get_supabase_client()

        # Verifica se a SAF existe
        existente = (
            supabase.table("saf_controle_ccm")
            .select("solicitacao_id, status")
            .eq("solicitacao_id", saf_id)
            .limit(1)
            .execute()
        )

        if not existente.data:
            return jsonify({"erro": "SAF nao encontrada."}), 404

        status_atual = existente.data[0]["status"]
        if status_atual in (STATUS_CONFIRMADO, STATUS_CANCELADO):
            return (
                jsonify(
                    {
                        "erro": f"SAF ja encerrada com status '{status_atual}'. Nenhuma alteracao permitida."
                    }
                ),
                409,
            )

        agora = datetime.now(timezone.utc).isoformat()

        # Monta o payload de atualização conforme o status recebido
        if status_recebido == "Necessário Complemento":
            dados_atualizacao = {
                "status": STATUS_COMPLEMENTO,
                "motivo_devolucao": motivo_complemento,
                "avaliado_por": avaliado_por,
                "data_avaliacao": agora,
            }

        elif status_recebido == "Confirmado":
            # Futuramente: disparar integracao SAP aqui
            dados_atualizacao = {
                "status": STATUS_CONFIRMADO,
                "motivo_devolucao": None,
                "avaliado_por": avaliado_por,
                "data_avaliacao": agora,
            }

        else:  # Cancelado
            dados_atualizacao = {
                "status": STATUS_CANCELADO,
                "motivo_cancelamento": motivo_cancelamento,
                "avaliado_por": avaliado_por,
                "data_avaliacao": agora,
            }

        supabase.table("saf_controle_ccm").update(dados_atualizacao).eq(
            "solicitacao_id", saf_id
        ).execute()

        return (
            jsonify(
                {
                    "mensagem": f"SAF avaliada com sucesso. Novo status: {dados_atualizacao['status']}",
                    "saf_id": saf_id,
                    "status": dados_atualizacao["status"],
                    "avaliado_por": avaliado_por,
                    "data_avaliacao": agora,
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"erro": str(e)}), 500
