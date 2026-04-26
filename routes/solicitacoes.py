import os
from dotenv import load_dotenv
from flask import Blueprint, jsonify, request
from supabase import Client, create_client

load_dotenv()

solicitacoes_bp = Blueprint("solicitacoes_bp", __name__)


def _get_supabase_client() -> Client:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        raise RuntimeError("Variaveis SUPABASE_URL e SUPABASE_KEY nao configuradas.")

    return create_client(supabase_url, supabase_key)


@solicitacoes_bp.route("/minhas/<notificador_id>", methods=["GET"])
def listar_minhas_solicitacoes(notificador_id):
    try:
        supabase = _get_supabase_client()
    except RuntimeError:
        return jsonify({"erro": "Configuracao do Supabase ausente"}), 500

    try:
        result = (
            supabase.table("saf_solicitacoes")
            .select(
                "id, titulo_falha, descricao_longa, prioridade, criado_em, "
                "saf_controle_ccm(status)"
            )
            .eq("notificador_id", notificador_id)
            .order("criado_em", desc=True)
            .execute()
        )
        return jsonify({"solicitacoes": result.data, "total": len(result.data)}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


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
    dados = request.get_json(silent=True) or {}

    campos_obrigatorios = [
        "notificador_id",
        "titulo_falha",
        "descricao_longa",
        "local_instalacao",
        "equipamento",
        "prioridade",
        "data_inicio_avaria",
        "hora_inicio_avaria",
    ]
    campos_faltando = [campo for campo in campos_obrigatorios if not dados.get(campo)]
    if campos_faltando:
        return (
            jsonify({"erro": f"Campos obrigatorios ausentes: {', '.join(campos_faltando)}"}),
            400,
        )

    try:
        prioridade = int(dados.get("prioridade"))
    except (TypeError, ValueError):
        return jsonify({"erro": "Campo 'prioridade' deve ser numerico (1 a 4)."}), 400

    try:
        supabase = _get_supabase_client()
    except RuntimeError:
        return jsonify({"erro": "Configuracao do Supabase ausente"}), 500

    try:
        # 1. Monta o payload com os novos nomes de colunas
        nova_saf = {
            "notificador_id": dados.get("notificador_id"),
            "titulo_falha": dados.get("titulo_falha"),
            "descricao_longa": dados.get("descricao_longa"),
            "local_instalacao": dados.get("local_instalacao"),
            "equipamento": dados.get("equipamento"),
            "prioridade": prioridade,
            "data_inicio_avaria": dados.get("data_inicio_avaria"),
            "hora_inicio_avaria": dados.get("hora_inicio_avaria"),
        }

        # 2. Insere na tabela principal
        resposta_saf = supabase.table("saf_solicitacoes").insert(nova_saf).execute()

        saf_id = resposta_saf.data[0]["id"]
        ticket = resposta_saf.data[0]["ticket_saf"]

        # 3. Insere no controle CCM
        novo_controle = {
            "solicitacao_id": saf_id,
            "status": "ABERTA",
        }
        supabase.table("saf_controle_ccm").insert(novo_controle).execute()

        # 4. Registra auditoria (best-effort para nao quebrar a criacao da SAF)
        try:
            supabase.table("logs_auditoria").insert(
                {
                    "usuario_id": dados.get("notificador_id"),
                    "acao": "CRIACAO_SAF",
                    "entidade": "saf_solicitacoes",
                    "entidade_id": str(saf_id),
                    "dados_depois": {"ticket_saf": ticket, "dados_enviados": nova_saf},
                }
            ).execute()
        except Exception:
            pass

        return (
            jsonify(
                {
                    "mensagem": "SAF criada com sucesso!",
                    "ticket": f"SAF #{ticket}",
                    "id": saf_id,
                }
            ),
            201,
        )

    except Exception as e:
        return jsonify({"erro_interno": str(e)}), 500
