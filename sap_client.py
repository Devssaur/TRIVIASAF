"""
Cliente HTTP para o SAP Gateway (API_MAINTNOTIFICATION / OData REST).

Centraliza todas as chamadas ao SAP para facilitar manutenção e testes.
Configurado via variáveis de ambiente (.env):
  SAP_BASE_URL, SAP_USER, SAP_PASSWORD, SAP_CLIENT, SAP_VERIFY_SSL
  SAP_ENDPOINT_CRIAR_NOTA, SAP_ENDPOINT_CANCELAR_NOTA,
  SAP_ENDPOINT_CONSULTAR_NOTA, SAP_ENDPOINT_LOCAIS,
  SAP_ENDPOINT_EQUIPAMENTOS, SAP_ENDPOINT_SINTOMAS
"""
import os
import base64
import logging
import requests

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# Helpers internos
# ──────────────────────────────────────────────────────────────

def _base_url() -> str:
    return os.environ.get("SAP_BASE_URL", "").rstrip("/")


def _headers() -> dict:
    user = os.environ.get("SAP_USER", "")
    pwd  = os.environ.get("SAP_PASSWORD", "")
    token = base64.b64encode(f"{user}:{pwd}".encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "sap-client": os.environ.get("SAP_CLIENT", "100"),
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _verify_ssl() -> bool:
    return os.environ.get("SAP_VERIFY_SSL", "false").strip().lower() not in ("false", "0", "no")


def _endpoint(env_key: str, default_path: str) -> str:
    custom = os.environ.get(env_key, "").strip()
    if custom:
        return custom
    return f"{_base_url()}{default_path}"


# ──────────────────────────────────────────────────────────────
# Mapeamento de prioridade SAF → SAP (PRIOK)
# ──────────────────────────────────────────────────────────────

_PRIORIDADE_MAP = {
    "CRITICA": "1",
    "ALTA":    "2",
    "MEDIA":   "3",
    "BAIXA":   "4",
}


# ──────────────────────────────────────────────────────────────
# CRIAR NOTA DE MANUTENÇÃO  (BAPI_ALM_NOTIF_CREATE equivalente)
# Endpoint: POST /sap/opu/odata/sap/API_MAINTNOTIFICATION/MaintenanceNotification
# ──────────────────────────────────────────────────────────────

def sap_criar_nota(saf: dict) -> dict:
    """
    Cria Nota de Manutenção no SAP a partir dos dados de uma SAF.

    Parâmetros esperados em `saf` (colunas de saf_solicitacoes):
      tipo_nota, titulo_falha, local_instalacao, equipamento,
      prioridade, data_inicio_avaria, hora_inicio_avaria,
      notificador_nome, descricao_longa

    Retorna dict com chaves:
      qmnum  – número da nota criada (QMNUM)
      raw    – resposta bruta do SAP
    """
    url = _endpoint(
        "SAP_ENDPOINT_CRIAR_NOTA",
        "/sap/opu/odata/sap/API_MAINTNOTIFICATION/MaintenanceNotification",
    )

    prioridade_sap = _PRIORIDADE_MAP.get(
        str(saf.get("prioridade", "MEDIA")).upper(), "3"
    )

    # Formata data/hora como strings aceitas pelo SAP OData
    data_avaria = str(saf.get("data_inicio_avaria") or "")
    hora_avaria = str(saf.get("hora_inicio_avaria") or "")

    payload = {
        "NotificationType":     saf.get("tipo_nota", "M2"),
        "MaintNotifBrfTxt":     (saf.get("titulo_falha") or "")[:40],
        "FunctionalLocation":   saf.get("local_instalacao", ""),
        "Equipment":            saf.get("equipamento", ""),
        "Priority":             prioridade_sap,
        "MalfunctionStartDate": data_avaria,
        "MalfunctionStartTime": hora_avaria,
        "MalfunctionEndDate":   data_avaria,
        "MalfunctionEndTime":   hora_avaria,
        "RequiredStartDate":    data_avaria,   # STRMN
        "RequiredStartTime":    hora_avaria,   # STRUR
        "ReportedByUser":       (saf.get("notificador_nome") or saf.get("notificador_id") or ""),
        "LongText":             saf.get("descricao_longa", ""),
    }

    logger.info("SAP criar_nota → %s | payload=%s", url, payload)

    resp = requests.post(
        url,
        json=payload,
        headers=_headers(),
        timeout=30,
        verify=_verify_ssl(),
    )
    resp.raise_for_status()
    data = resp.json()

    # SAP retorna o número da nota em diferentes campos dependendo do serviço
    qmnum = (
        data.get("d", {}).get("MaintenanceNotification")
        or data.get("d", {}).get("NotificationNo")
        or data.get("MaintenanceNotification")
        or data.get("NotificationNo")
        or data.get("qmnum")
    )

    return {"qmnum": qmnum, "raw": data}


# ──────────────────────────────────────────────────────────────
# CANCELAR NOTA  (BAPI_ALM_NOTIF_CLOSE equivalente)
# Endpoint: POST .../MaintenanceNotification('<qmnum>')/Cancel
# ──────────────────────────────────────────────────────────────

def sap_cancelar_nota(qmnum: str) -> dict:
    """
    Cancela Nota de Manutenção no SAP (seta status CANCL).
    Levanta exceção em caso de falha para garantir transação atômica.
    """
    url = _endpoint(
        "SAP_ENDPOINT_CANCELAR_NOTA",
        f"/sap/opu/odata/sap/API_MAINTNOTIFICATION/MaintenanceNotification('{qmnum}')/Cancel",
    )

    logger.info("SAP cancelar_nota → %s | qmnum=%s", url, qmnum)

    resp = requests.post(
        url,
        headers=_headers(),
        timeout=30,
        verify=_verify_ssl(),
    )
    resp.raise_for_status()
    return resp.json() if resp.content else {}


# ──────────────────────────────────────────────────────────────
# CONSULTAR NOTA  (leitura de status e AUFNR)
# Endpoint: GET .../MaintenanceNotification('<qmnum>')
# ──────────────────────────────────────────────────────────────

def sap_consultar_nota(qmnum: str) -> dict:
    """
    Retorna dados de uma Nota do SAP: status (JEST-STAT) e ordem vinculada (AUFNR).
    """
    url = _endpoint(
        "SAP_ENDPOINT_CONSULTAR_NOTA",
        f"/sap/opu/odata/sap/API_MAINTNOTIFICATION/MaintenanceNotification('{qmnum}')?$format=json",
    )

    resp = requests.get(
        url,
        headers=_headers(),
        timeout=30,
        verify=_verify_ssl(),
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("d", data)


# ──────────────────────────────────────────────────────────────
# LISTAR LOCAIS DE INSTALAÇÃO  (IL03 / API_FUNCTLOCATION_SRV)
# ──────────────────────────────────────────────────────────────

def sap_listar_locais() -> list:
    """
    Retorna lista de Locais de Instalação ativos do SAP (TPLNR).
    """
    url = _endpoint(
        "SAP_ENDPOINT_LOCAIS",
        (
            "/sap/opu/odata/sap/API_FUNCTLOCATION_SRV/FunctionalLocation"
            "?$select=FunctionalLocation,FunctionalLocationName"
            "&$filter=IsActive%20eq%20true&$format=json"
        ),
    )

    resp = requests.get(
        url,
        headers=_headers(),
        timeout=60,
        verify=_verify_ssl(),
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("d", {}).get("results", [])


# ──────────────────────────────────────────────────────────────
# LISTAR EQUIPAMENTOS  (IE03 / API_EQUIPMENT_SRV)
# ──────────────────────────────────────────────────────────────

def sap_listar_equipamentos(tplnr: str = None) -> list:
    """
    Retorna Equipamentos do SAP (EQUNR), opcionalmente filtrados por Local (TPLNR).
    """
    filtro = f"$filter=FunctionalLocation%20eq%20%27{tplnr}%27&" if tplnr else ""
    url = _endpoint(
        "SAP_ENDPOINT_EQUIPAMENTOS",
        (
            f"/sap/opu/odata/sap/API_EQUIPMENT_SRV/Equipment"
            f"?{filtro}$select=Equipment,EquipmentName,FunctionalLocation&$format=json"
        ),
    )

    resp = requests.get(
        url,
        headers=_headers(),
        timeout=60,
        verify=_verify_ssl(),
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("d", {}).get("results", [])


# ──────────────────────────────────────────────────────────────
# LISTAR SINTOMAS  (Catálogo Tipo C / API_MAINTNOTIFICATION)
# ──────────────────────────────────────────────────────────────

def sap_listar_sintomas(equnr: str = None) -> list:
    """
    Retorna Catálogo Tipo C (Sintomas/Danos) do SAP.
    Opcionalmente filtrado pelo Equipamento para evitar erros na BAPI.
    """
    filtro = f"$filter=Equipment%20eq%20%27{equnr}%27%20and%20" if equnr else "$filter="
    url = _endpoint(
        "SAP_ENDPOINT_SINTOMAS",
        (
            "/sap/opu/odata/sap/API_MAINTNOTIFICATION/MaintNotifCatalog"
            f"?{filtro}CatalogType%20eq%20%27C%27"
            "&$select=CodeGroup,Code,CodeGroupDescription&$format=json"
        ),
    )

    resp = requests.get(
        url,
        headers=_headers(),
        timeout=30,
        verify=_verify_ssl(),
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("d", {}).get("results", [])
