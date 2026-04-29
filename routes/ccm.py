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
    key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("Variaveis SUPABASE_URL e SUPABASE_SERVICE_KEY nao configuradas.")
    return create_client(url, key)


def _normalize_prioridade(valor) -> str:
    p = str(valor or '').strip().upper()
    mapping = {
        '1': 'BAIXA',
        '2': 'MEDIA',
        '3': 'ALTA',
        '4': 'CRITICA',
        'BAIXA': 'BAIXA',
        'MEDIA': 'MEDIA',
        'MÉDIA': 'MEDIA',
        'ALTA': 'ALTA',
        'CRITICA': 'CRITICA',
        'CRÍTICA': 'CRITICA',
    }
    return mapping.get(p, '')


# ==========================================
# 1. ROTA GET: Listar SAFs para a fila CCM (exceto devolvidas)
# ==========================================
@ccm_bp.route('/pendentes', methods=['GET'])
def listar_pendentes():
    try:
        supabase = _get_supabase_client()
        resposta = supabase.table('saf_solicitacoes') \
            .select(
                'id, ticket_saf, titulo_falha, descricao_longa, '
                'local_instalacao, local_instalacao_id, equipamento, equipamento_id, '
                'sintoma_id, prioridade, data_inicio_avaria, hora_inicio_avaria, '
                'notificador_id, notificador_nome, notificador_area, '
                'anexo_evidencia_url, criado_em, '
                'status, motivo_devolucao, motivo_cancelamento, '
                'atualizado_sap, tipo_nota, qmnum_duplicata, data_avaliacao, '
                'saf_integracao_sap(qmnum, tipo_nota, status_integracao, mensagem_erro)'
            ) \
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
    prioridade = _normalize_prioridade(dados.get('prioridade'))

    if novo_status not in ('APROVADA', 'DEVOLVIDA'):
        return jsonify({"erro": "Status inválido. Use APROVADA ou DEVOLVIDA."}), 400
    if novo_status == 'DEVOLVIDA' and not motivo:
        return jsonify({"erro": "Informe o motivo da devolução."}), 400

    try:
        supabase = _get_supabase_client()
        update_data = {
            "status": novo_status,
            "avaliado_por": avaliador_id,
            "data_avaliacao": datetime.now(timezone.utc).isoformat()
        }
        if prioridade:
            update_data["prioridade"] = prioridade
        if novo_status == 'DEVOLVIDA':
            update_data["motivo_devolucao"] = motivo

        supabase.table('saf_solicitacoes') \
            .update(update_data) \
            .eq('id', solicitacao_id) \
            .execute()

        qmnum    = None
        erro_sap = None

        if novo_status == 'APROVADA':
            tipo_nota = dados.get('tipo_nota', 'YP')

            # Salva tipo_nota escolhido pelo CCM
            supabase.table('saf_solicitacoes') \
                .update({'tipo_nota': tipo_nota}) \
                .eq('id', solicitacao_id) \
                .execute()

            try:
                saf_res = supabase.table('saf_solicitacoes') \
                    .select('*') \
                    .eq('id', solicitacao_id) \
                    .execute()
                saf = saf_res.data[0] if saf_res.data else {}
                saf['tipo_nota'] = tipo_nota

                # Resolve códigos técnicos SAP (id_sap já é o código TPLNR/EQUNR)
                saf['tplnr'] = saf.get('local_instalacao_id') or saf.get('local_instalacao', '')
                saf['equnr'] = saf.get('equipamento_id')      or saf.get('equipamento', '')

                if saf.get('sintoma_id'):
                    sint = supabase.table('sintomas_catalogo') \
                        .select('grupo, codigo_item') \
                        .eq('id', saf['sintoma_id']) \
                        .maybe_single().execute()
                    if sint.data:
                        saf['qmgrp'] = sint.data.get('grupo', '')
                        saf['qmcod'] = sint.data.get('codigo_item', '')

                resultado = sap_client.sap_criar_nota(saf)
                qmnum = resultado['qmnum']

                supabase.table('saf_integracao_sap').upsert({
                    "solicitacao_id":     solicitacao_id,
                    "qmnum":              qmnum,
                    "tipo_nota":          tipo_nota,
                    "status_integracao":  "SUCESSO",
                    "payload_envio": {
                        "ticket_saf": saf.get('ticket_saf'),
                        "tipo_nota":  tipo_nota,
                        "tplnr":      saf.get('tplnr'),
                        "equnr":      saf.get('equnr'),
                        "prioridade": saf.get('prioridade'),
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
                        "solicitacao_id":      solicitacao_id,
                        "status_integracao":   "ERRO",
                        "mensagem_erro":       erro_sap,
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
                resposta["aviso_sap"] = (
                    f"Aprovação registrada, mas a criação da nota SAP falhou: {erro_sap}. "
                    f"Tente novamente via POST /api/sap/criar-nota/{solicitacao_id}."
                )

            # ── Marca duplicatas ──────────────────────────────────────────
            # Regra: mesma SAF = mesmo local + mesmo equipamento + mesmo sintoma.
            # Só marca se AMBAS tiverem sintoma_id definido e forem iguais.
            # Isso evita falsos positivos quando a SAF aprovada não tem sintoma.
            duplicatas_ids = []
            if qmnum:
                try:
                    equip_id   = saf.get('equipamento_id')
                    local_id   = saf.get('local_instalacao_id')
                    sintoma_id = saf.get('sintoma_id')

                    if equip_id and sintoma_id:
                        abertas = supabase.table('saf_solicitacoes') \
                            .select('id, local_instalacao_id, equipamento_id, sintoma_id') \
                            .eq('status', 'ABERTA') \
                            .neq('id', solicitacao_id) \
                            .execute()

                        for r in (abertas.data or []):
                            if r.get('equipamento_id') != equip_id:
                                continue
                            if r.get('local_instalacao_id') != local_id:
                                continue
                            # Exige sintoma igual em ambas — evita marcar SAFs de avaria diferente
                            if r.get('sintoma_id') != sintoma_id:
                                continue
                            duplicatas_ids.append(r['id'])

                        agora = datetime.now(timezone.utc).isoformat()
                        for dup_id in duplicatas_ids:
                            supabase.table('saf_solicitacoes').update({
                                "status":          "DUPLICADA",
                                "qmnum_duplicata": qmnum,
                                "tipo_nota":       tipo_nota,
                                "data_avaliacao":  agora,
                                "avaliado_por":    avaliador_id,
                            }).eq('id', dup_id).execute()

                        if duplicatas_ids:
                            logger.info(
                                "Marcadas %d SAFs como DUPLICADA (local=%s equip=%s sintoma=%s) "
                                "→ QMNUM %s: %s",
                                len(duplicatas_ids), local_id, equip_id,
                                sintoma_id, qmnum, duplicatas_ids,
                            )
                except Exception as dup_err:
                    logger.error("Erro ao marcar duplicatas (não bloqueante): %s", dup_err)

            resposta["duplicatas"] = len(duplicatas_ids)
            return jsonify(resposta), 200

        return jsonify({"mensagem": f"SAF atualizada para {novo_status}."}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


# ==========================================
# 2.1 ROTA PUT: Atualizar criticidade/prioridade pelo CCM
# ==========================================
@ccm_bp.route('/prioridade/<string:solicitacao_id>', methods=['PUT'])
def atualizar_prioridade_ccm(solicitacao_id):
    dados = request.json or {}
    prioridade = _normalize_prioridade(dados.get('prioridade'))
    if not prioridade:
        return jsonify({"erro": "Prioridade inválida. Use BAIXA, MEDIA, ALTA ou CRITICA."}), 400

    try:
        supabase = _get_supabase_client()
        supabase.table('saf_solicitacoes') \
            .update({'prioridade': prioridade}) \
            .eq('id', solicitacao_id) \
            .execute()
        return jsonify({'mensagem': 'Prioridade atualizada.', 'prioridade': prioridade}), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


# ==========================================
# 2.2 ROTA PUT: Marcar ordens como DUPLICADA em lote
# ==========================================
@ccm_bp.route('/duplicar-lote', methods=['PUT'])
def duplicar_lote_ccm():
    dados = request.json or {}
    ids = dados.get('ids') or []
    avaliador_id = dados.get('avaliador_id')

    if not isinstance(ids, list) or not ids:
        return jsonify({'erro': 'Informe uma lista de IDs para duplicar.'}), 400

    # Remove vazios e duplicados preservando ordem
    ids_limpos = []
    vistos = set()
    for sid in ids:
        sid_txt = str(sid or '').strip()
        if not sid_txt or sid_txt in vistos:
            continue
        vistos.add(sid_txt)
        ids_limpos.append(sid_txt)

    if not ids_limpos:
        return jsonify({'erro': 'Nenhum ID valido foi informado.'}), 400

    try:
        supabase = _get_supabase_client()
        abertas = supabase.table('saf_solicitacoes') \
            .select('id') \
            .in_('id', ids_limpos) \
            .eq('status', 'ABERTA') \
            .execute()

        abertas_ids = [r.get('id') for r in (abertas.data or []) if r.get('id')]
        if not abertas_ids:
            return jsonify({'erro': 'Nenhuma ordem aberta encontrada para marcar como duplicada.'}), 400

        agora = datetime.now(timezone.utc).isoformat()
        for sid in abertas_ids:
            supabase.table('saf_solicitacoes') \
                .update({
                    'status': 'DUPLICADA',
                    'data_avaliacao': agora,
                    'avaliado_por': avaliador_id,
                }) \
                .eq('id', sid) \
                .execute()

        try:
            supabase.table('logs_auditoria').insert({
                'evento': 'CCM_DUPLICADA_LOTE',
                'payload': {
                    'total_solicitado': len(ids_limpos),
                    'total_marcado': len(abertas_ids),
                    'ids': abertas_ids,
                    'avaliador_id': avaliador_id,
                },
            }).execute()
        except Exception:
            pass

        return jsonify({
            'mensagem': 'Ordens marcadas como duplicadas.',
            'total_marcado': len(abertas_ids),
            'ids_marcados': abertas_ids,
        }), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


# ==========================================
# 3. ROTA PATCH: Alternar flag atualizado_sap
# ==========================================
@ccm_bp.route('/toggle-sap/<string:solicitacao_id>', methods=['PATCH'])
def toggle_sap(solicitacao_id):
    dados = request.json or {}
    novo_valor = bool(dados.get('atualizado_sap', False))
    try:
        supabase = _get_supabase_client()
        supabase.table('saf_solicitacoes') \
            .update({'atualizado_sap': novo_valor}) \
            .eq('id', solicitacao_id) \
            .execute()
        return jsonify({'atualizado_sap': novo_valor}), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500