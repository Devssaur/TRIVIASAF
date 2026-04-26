from flask import Blueprint, request, jsonify
import os
from supabase import create_client, Client
from datetime import datetime, timezone

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