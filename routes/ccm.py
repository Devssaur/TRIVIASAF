from flask import Blueprint, request, jsonify
import os
import logging
from supabase import create_client, Client
from datetime import datetime, timezone
import sap_client

logger = logging.getLogger(__name__)

ccm_bp = Blueprint('ccm', __name__)

def _get_supabase_client() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("Variaveis SUPABASE_URL e SUPABASE_KEY nao configuradas.")
    return create_client(url, key)


# ==========================================
# 1. ROTA GET: Listar todos os registros CCM (exceto cancelados)
# ==========================================
@ccm_bp.route('/pendentes', methods=['GET'])
def listar_pendentes():
    try:
        supabase = _get_supabase_client()
        resposta = supabase.table('saf_controle_ccm') \
            .select(
                'solicitacao_id, status, atualizado_sap, motivo_devolucao, '
                'data_avaliacao, criado_em, '
                'saf_solicitacoes('
                '  ticket_saf, titulo_falha, descricao_longa, '
                '  local_instalacao, equipamento, prioridade, '
                '  data_inicio_avaria, hora_inicio_avaria, notificador_id, '
                '  notificador_nome, notificador_area, '
                '  anexo_evidencia_url, status'
                ')'
            ) \
            .neq('status', 'CANCELADA') \
            .neq('status', 'DEVOLVIDA') \
            .order('criado_em', desc=False) \
            .execute()
        return jsonify(resposta.data), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


# ==========================================
# 2. ROTA PUT: Avaliar a SAF (Aceitar = APROVADA / Recusar = DEVOLVIDA)
# ==========================================
@ccm_bp.route('/avaliar/<string:solicitacao_id>', methods=['PUT'])
def avaliar_saf(solicitacao_id):
    dados = request.json or {}
    novo_status  = dados.get('status', '')
    motivo       = (dados.get('motivo_devolucao') or '').strip()
    avaliador_id = dados.get('avaliador_id')

    if novo_status not in ('APROVADA', 'DEVOLVIDA'):
        return jsonify({"erro": "Status inválido. Use APROVADA ou DEVOLVIDA."}), 400

    try:
        supabase = _get_supabase_client()
        update_data = {
            "status": novo_status,
            "avaliado_por": avaliador_id,
            "data_avaliacao": datetime.now(timezone.utc).isoformat()
        }
        if novo_status == 'DEVOLVIDA' and motivo:
            update_data["motivo_devolucao"] = motivo

        supabase.table('saf_controle_ccm') \
            .update(update_data) \
            .eq('solicitacao_id', solicitacao_id) \
            .execute()

        # Sincroniza status na tabela de solicitações
        if novo_status == 'APROVADA':
            supabase.table('saf_solicitacoes') \
                .update({'status': 'Aprovada'}) \
                .eq('id', solicitacao_id) \
                .execute()

            # ── Dispara criação da Nota no SAP (síncrono, retorna QMNUM) ──
            qmnum      = None
            erro_sap   = None
            tipo_nota  = dados.get('tipo_nota', 'M2')

            # Salva tipo_nota no controle CCM
            supabase.table('saf_controle_ccm') \
                .update({'tipo_nota': tipo_nota}) \
                .eq('solicitacao_id', solicitacao_id) \
                .execute()

            try:
                saf_res = supabase.table('saf_solicitacoes') \
                    .select('*') \
                    .eq('id', solicitacao_id) \
                    .execute()
                saf = saf_res.data[0] if saf_res.data else {}
                saf['tipo_nota'] = tipo_nota

                resultado = sap_client.sap_criar_nota(saf)
                qmnum = resultado['qmnum']

                supabase.table('saf_integracao_sap').upsert({
                    "solicitacao_id":     solicitacao_id,
                    "qmnum":              qmnum,
                    "tipo_nota":          tipo_nota,
                    "status_integracao":  "SUCESSO",
                    "payload_envio": {
                        "ticket_saf":       saf.get('ticket_saf'),
                        "tipo_nota":        tipo_nota,
                        "local_instalacao": saf.get('local_instalacao'),
                        "equipamento":      saf.get('equipamento'),
                        "prioridade":       saf.get('prioridade'),
                    },
                    "payload_resposta":    resultado.get('raw', {}),
                    "ultima_tentativa_em": datetime.now(timezone.utc).isoformat(),
                    "mensagem_erro":       None,
                }).execute()

                supabase.table('logs_auditoria').insert({
                    "evento": "INTEGRACAO_SAP_SUCESSO",
                    "payload": {"saf_id": solicitacao_id, "qmnum": qmnum},
                }).execute()

            except Exception as sap_err:
                erro_sap = str(sap_err)
                logger.error("Falha ao criar nota SAP (saf_id=%s): %s", solicitacao_id, sap_err)
                try:
                    supabase.table('saf_integracao_sap').upsert({
                        "solicitacao_id":     solicitacao_id,
                        "status_integracao":  "ERRO",
                        "mensagem_erro":      erro_sap,
                        "ultima_tentativa_em": datetime.now(timezone.utc).isoformat(),
                    }).execute()
                    supabase.table('logs_auditoria').insert({
                        "evento": "INTEGRACAO_SAP_ERRO",
                        "payload": {"saf_id": solicitacao_id, "erro": erro_sap},
                    }).execute()
                except Exception:
                    pass

            resposta = {"mensagem": "SAF aprovada.", "qmnum": qmnum}
            if erro_sap:
                resposta["aviso_sap"] = f"Aprovação registrada, mas a criação da nota SAP falhou: {erro_sap}. Tente novamente via POST /api/sap/criar-nota/{solicitacao_id}."
            return jsonify(resposta), 200

        elif novo_status == 'DEVOLVIDA':
            supabase.table('saf_solicitacoes') \
                .update({'status': 'Pendente'}) \
                .eq('id', solicitacao_id) \
                .execute()

        return jsonify({"mensagem": f"SAF atualizada para {novo_status}."}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


# ==========================================
# 3. ROTA PATCH: Alternar flag atualizado_sap
# ==========================================
@ccm_bp.route('/toggle-sap/<string:solicitacao_id>', methods=['PATCH'])
def toggle_sap(solicitacao_id):
    dados = request.json or {}
    novo_valor = bool(dados.get('atualizado_sap', False))
    try:
        supabase = _get_supabase_client()
        supabase.table('saf_controle_ccm') \
            .update({'atualizado_sap': novo_valor}) \
            .eq('solicitacao_id', solicitacao_id) \
            .execute()
        return jsonify({'atualizado_sap': novo_valor}), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500