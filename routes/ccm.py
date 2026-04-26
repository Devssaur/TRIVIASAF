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
# 1. ROTA GET: Listar SAFs Pendentes
# ==========================================
@ccm_bp.route('/pendentes', methods=['GET'])
def listar_pendentes():
    try:
        supabase = _get_supabase_client()
        # Faz um JOIN inteligente: Traz o controle que está 'ABERTA' 
        # e embute os detalhes da tabela principal (saf_solicitacoes)
        resposta = supabase.table('saf_controle_ccm') \
            .select('solicitacao_id, status, criado_em, saf_solicitacoes(ticket_saf, titulo_falha, equipamento, prioridade)') \
            .eq('status', 'ABERTA') \
            .execute()
        
        return jsonify(resposta.data), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# ==========================================
# 2. ROTA PUT: Avaliar a SAF (Aprovar/Devolver)
# ==========================================
@ccm_bp.route('/avaliar/<string:solicitacao_id>', methods=['PUT'])
def avaliar_saf(solicitacao_id):
    dados = request.json
    novo_status = dados.get('status')
    motivo = dados.get('motivo_devolucao')
    avaliador_id = dados.get('avaliador_id') # UUID de quem está avaliando (Maria do CCM)

    try:
        supabase = _get_supabase_client()
        # Prepara a "maleta" de dados para atualizar
        update_data = {
            "status": novo_status,
            "avaliado_por": avaliador_id,
            "data_avaliacao": datetime.now(timezone.utc).isoformat()
        }
        
        # Se for devolvida, adiciona o motivo na maleta
        if novo_status == 'DEVOLVIDA':
            update_data["motivo_devolucao"] = motivo

        # Atualiza a tabela de controle
        resposta = supabase.table('saf_controle_ccm') \
            .update(update_data) \
            .eq('solicitacao_id', solicitacao_id) \
            .execute()

        # Registra a ação na Tabela de Auditoria
        supabase.table('logs_auditoria').insert({
            "usuario_id": avaliador_id,
            "evento": f"AVALIACAO_CCM_{novo_status}",
            "payload": update_data
        }).execute()

        return jsonify({"mensagem": f"SAF atualizada para {novo_status} com sucesso!"}), 200

    except Exception as e:
        return jsonify({"erro": str(e)}), 400