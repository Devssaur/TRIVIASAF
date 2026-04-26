from flask import Blueprint, request, jsonify
import os
import random
from datetime import datetime, timezone
from supabase import create_client, Client

sap_bp = Blueprint('sap', __name__)

def _get_supabase_client() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")

    if not url or not key:
        raise RuntimeError("Variaveis SUPABASE_URL e SUPABASE_KEY nao configuradas.")

    return create_client(url, key)

@sap_bp.route('/sincronizar/<string:solicitacao_id>', methods=['POST'])
def sincronizar_sap(solicitacao_id):
    dados = request.json or {}
    # Lê o que o Thunder Client pediu para simular (se não mandar nada, ele escolhe aleatório)
    cenario = dados.get('simular', random.choice(['SUCESSO', 'ERRO']))

    try:
        supabase = _get_supabase_client()
        # 1. Regra de Negócio: Verifica se a SAF realmente está APROVADA
        ccm_data = supabase.table('saf_controle_ccm').select('status').eq('solicitacao_id', solicitacao_id).execute()
        if not ccm_data.data or ccm_data.data[0]['status'] != 'APROVADA':
            return jsonify({"erro": "Bloqueado: Apenas SAFs com status APROVADA podem ser enviadas ao SAP."}), 400

        # 2. Busca os dados da SAF para montar o pacote (Payload) do SAP
        saf_data = supabase.table('saf_solicitacoes').select('*').eq('id', solicitacao_id).execute()
        saf = saf_data.data[0]

        payload_envio = {
            "sistema_origem": "APP_SAF_MOBILE",
            "ticket_saf": saf['ticket_saf'],
            "equipamento": saf['equipamento'],
            "prioridade": saf['prioridade'],
            "texto_breve": saf['titulo_falha']
        }

        # 3. O Simulador da BAPI do SAP
        if cenario == 'SUCESSO':
            # Gera números falsos de Nota (qmnum) e Ordem (aufnr) parecidos com o SAP real
            qmnum = f"100{random.randint(1000, 9999)}"
            aufnr = f"400{random.randint(1000, 9999)}"
            status_banco = 'SUCESSO'
            mensagem_erro = None
            payload_resposta = {"status": "200 OK", "qmnum": qmnum, "aufnr": aufnr, "mensagem": "Nota QM gerada com sucesso."}
        else:
            qmnum = None
            aufnr = None
            status_banco = 'ERRO'
            mensagem_erro = "Timeout 504: O servidor SAP não respondeu a tempo (Simulação)."
            payload_resposta = {"status": "504 Gateway Timeout", "mensagem": mensagem_erro}

        # 4. Grava na tabela saf_integracao_sap usando UPSERT 
        # (Upsert atualiza se já existir um erro anterior, ou insere se for a primeira vez)
        dados_banco = {
            "solicitacao_id": solicitacao_id,
            "status_integracao": status_banco,
            "payload_envio": payload_envio,
            "payload_resposta": payload_resposta,
            "ultima_tentativa_em": datetime.now(timezone.utc).isoformat(),
            "mensagem_erro": mensagem_erro
        }
        
        # Só adiciona no JSON se houver número (para não quebrar as chaves UNIQUE do banco)
        if qmnum: dados_banco["qmnum"] = qmnum
        if aufnr: dados_banco["aufnr"] = aufnr

        supabase.table('saf_integracao_sap').upsert(dados_banco).execute()

        # 5. Registra o Log de Auditoria
        supabase.table('logs_auditoria').insert({
            "evento": f"INTEGRACAO_SAP_{status_banco}",
            "payload": dados_banco
        }).execute()

        # Retorna para o Front-end o resultado
        if status_banco == 'SUCESSO':
            return jsonify({
                "mensagem": "Sincronização concluída!",
                "sap_nota": qmnum,
                "sap_ordem": aufnr
            }), 200
        else:
            return jsonify({"erro": mensagem_erro}), 500

    except Exception as e:
        return jsonify({"erro_interno": str(e)}), 500