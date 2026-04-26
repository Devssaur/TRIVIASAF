/**
 * SAF – Sistema de Abertura de Falhas
 * Utilitários compartilhados (auth, API, formatação, UI)
 */

// =============================================
// AUTH STATE (localStorage)
// =============================================
const Auth = (() => {
  const KEY = 'saf_user';

  function getUser() {
    try { return JSON.parse(localStorage.getItem(KEY)); }
    catch { return null; }
  }

  function setUser(user) {
    localStorage.setItem(KEY, JSON.stringify(user));
  }

  function clearUser() {
    localStorage.removeItem(KEY);
  }

  function requireAuth(allowedProfiles) {
    const user = getUser();
    if (!user) { window.location.href = '/login'; return null; }
    if (allowedProfiles && !allowedProfiles.includes(user.perfil)) {
      window.location.href = '/acesso-negado';
      return null;
    }
    return user;
  }

  function redirectIfLoggedIn() {
    const user = getUser();
    if (!user) return;
    const dest = { SOLICITANTE: '/nova-saf', CCM: '/fila-ccm', ADMIN: '/admin' };
    window.location.href = dest[user.perfil] || '/nova-saf';
  }

  return { getUser, setUser, clearUser, requireAuth, redirectIfLoggedIn };
})();

// =============================================
// API HELPER
// =============================================
const API = (() => {
  const BASE = '/api';

  async function request(method, path, body) {
    const opts = {
      method,
      headers: { 'Content-Type': 'application/json' }
    };
    if (body !== undefined) opts.body = JSON.stringify(body);
    try {
      const res = await fetch(BASE + path, opts);
      const json = await res.json().catch(() => ({}));
      return { ok: res.ok, status: res.status, data: json };
    } catch (err) {
      return { ok: false, status: 0, data: { erro: 'Erro de conexão com o servidor.' } };
    }
  }

  return {
    get:    (path)        => request('GET',    path),
    post:   (path, body)  => request('POST',   path, body),
    put:    (path, body)  => request('PUT',    path, body),
    delete: (path, body)  => request('DELETE', path, body),

    // Auth
    login: (email, senha) => request('POST', '/auth/login', { email, senha }),

    // Solicitações
    minhasSafs:   (uid)   => request('GET', `/solicitacoes/minhas-safs/${uid}`),
    criarSaf:     (body)  => request('POST', '/solicitacoes/criar', body),
    buscarSaf:    (id)    => request('GET', `/solicitacoes/${id}`),
    editarSaf:    (id, b) => request('PUT', `/solicitacoes/${id}`, b),
    cancelarSaf:  (id, b) => request('PUT', `/solicitacoes/cancelar/${id}`, b),

    // CCM
    filaCCM:        ()          => request('GET', '/ccm/pendentes'),
    avaliarSaf:     (id, body)  => request('PUT', `/ccm/avaliar/${id}`, body),

    // SAP
    sincronizarSap: (id)        => request('POST', `/sap/sincronizar/${id}`),

    // Dados mestres
    sugerir:      (q)    => request('GET', `/dados/sugerir?q=${encodeURIComponent(q)}`),
    locais:       ()     => request('GET', '/dados/locais'),
    equipamentos: (lid)  => request('GET', `/dados/equipamentos/${lid}`),
    sintomas:     (eid)  => request('GET', `/dados/sintomas/${eid}`),

    // Admin
    logs:             ()               => request('GET',  '/admin/logs'),
    usuarios:         ()               => request('GET',  '/admin/usuarios'),
    aprovarUsuario:   (id, aprovado, perfil, ator_id) => request('POST', `/admin/usuarios/${id}/aprovar`, { aprovado, perfil, ator_id }),
    alterarPerfil:    (id, perfil, ator_id) => request('PUT',  `/admin/usuarios/${id}/perfil`, { perfil, ator_id }),
    atualizarUsuario: (id, body)       => request('PUT',  `/admin/usuarios/${id}`, body),
    excluirUsuario:   (id, body)       => request('DELETE', `/admin/usuarios/${id}`, body),
    toggleSap:        (id, val)        => request('PATCH', `/ccm/toggle-sap/${id}`, { atualizado_sap: val }),
  };
})();

// =============================================
// FORMATAÇÃO
// =============================================
const Fmt = (() => {
  const STATUS_LABEL = {
    ABERTA:      'Pendente CCM',
    EM_ANALISE:  'Em Análise',
    DEVOLVIDA:   'Necessário Complemento',
    APROVADA:    'Confirmada',
    CANCELADA:   'Cancelada',
  };
  const STATUS_CLASS = {
    ABERTA:      'badge-aberta',
    EM_ANALISE:  'badge-em_analise',
    DEVOLVIDA:   'badge-devolvida',
    APROVADA:    'badge-aprovada',
    CANCELADA:   'badge-cancelada',
  };
  const PRIO_LABEL = { BAIXA: 'Baixa', MEDIA: 'Média', ALTA: 'Alta', CRITICA: 'Crítica' };
  const PRIO_CLASS = { BAIXA: 'badge-baixa', MEDIA: 'badge-media', ALTA: 'badge-alta', CRITICA: 'badge-critica' };

  function statusBadge(s) {
    const lbl = STATUS_LABEL[s] || s;
    const cls = STATUS_CLASS[s] || '';
    return `<span class="badge ${cls}">${lbl}</span>`;
  }
  function prioBadge(p) {
    const lbl = PRIO_LABEL[p] || p;
    const cls = PRIO_CLASS[p] || '';
    return `<span class="badge ${cls}">${lbl}</span>`;
  }
  function date(iso) {
    if (!iso) return '—';
    return new Date(iso).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });
  }
  function datetime(iso) {
    if (!iso) return '—';
    return new Date(iso).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  }
  function ticket(t) {
    if (!t) return '—';
    return `<span class="ticket-num">SAF #${t}</span>`;
  }
  function initials(name) {
    if (!name) return '?';
    return name.split(' ').slice(0, 2).map(n => n[0]).join('').toUpperCase();
  }
  function statusLabel(s) { return STATUS_LABEL[s] || s; }
  function prioLabel(p)   { return PRIO_LABEL[p] || p; }
  return { statusBadge, prioBadge, date, datetime, ticket, initials, statusLabel, prioLabel };
})();

// =============================================
// TOAST NOTIFICATIONS
// =============================================
const Toast = (() => {
  let container;
  function _ensure() {
    if (!container) {
      container = document.getElementById('toast-container');
      if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
      }
    }
  }
  function show(msg, type = 'info', duration = 4000) {
    _ensure();
    const icons = { info: 'ℹ️', success: '✅', warning: '⚠️', error: '❌' };
    const el = document.createElement('div');
    el.className = `toast ${type}`;
    el.innerHTML = `<span>${icons[type] || ''}</span><span>${msg}</span>`;
    container.appendChild(el);
    setTimeout(() => {
      el.style.opacity = '0';
      el.style.transition = 'opacity .3s ease';
      setTimeout(() => el.remove(), 300);
    }, duration);
  }
  return {
    info:    msg => show(msg, 'info'),
    success: msg => show(msg, 'success'),
    warning: msg => show(msg, 'warning'),
    error:   msg => show(msg, 'error'),
  };
})();

// =============================================
// MODAL HELPER
// =============================================
const Modal = (() => {
  function open(id) {
    const el = document.getElementById(id);
    if (el) el.classList.add('open');
  }
  function close(id) {
    const el = document.getElementById(id);
    if (el) el.classList.remove('open');
  }
  function closeAll() {
    document.querySelectorAll('.modal-backdrop.open').forEach(el => el.classList.remove('open'));
  }
  // Close modal on backdrop click
  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
      backdrop.addEventListener('click', e => {
        if (e.target === backdrop) backdrop.classList.remove('open');
      });
    });
  });
  return { open, close, closeAll };
})();

// =============================================
// LOADING STATE
// =============================================
function setLoading(btn, loading, text) {
  if (!btn) return;
  if (loading) {
    btn._originalText = btn.innerHTML;
    btn.innerHTML = `<span class="spinner" style="width:15px;height:15px;"></span> ${text || 'Aguarde...'}`;
    btn.disabled = true;
  } else {
    btn.innerHTML = btn._originalText || text || 'Enviar';
    btn.disabled = false;
  }
}

// =============================================
// TOOLBAR SETUP (call on every protected page)
// =============================================
function setupToolbar() {
  const user = Auth.getUser();
  if (!user) return;

  const nameEl = document.getElementById('toolbar-user-name');
  const initialsEl = document.getElementById('toolbar-user-badge');
  if (nameEl) nameEl.textContent = user.nome || '';
  if (initialsEl) initialsEl.textContent = Fmt.initials(user.nome || '');

  const perfil = document.getElementById('toolbar-perfil');
  if (perfil) {
    const labels = { SOLICITANTE: 'Solicitante', CCM: 'CCM', ADMIN: 'Administrador' };
    perfil.textContent = labels[user.perfil] || user.perfil;
  }

  // SOLICITANTE: "Minhas SAFs" tab is in the sidebar, not the nav bar
  if (user.perfil === 'SOLICITANTE') {
    document.querySelectorAll('.nav-tab[href="/minhas-safs"]').forEach(el => el.remove());
  }

  // Sidebar toggle
  const sidebar  = document.getElementById('sidebar');
  const overlay  = document.getElementById('sidebar-overlay');
  const menuBtn  = document.querySelector('.toolbar-menu-btn');
  const closeBtn = document.getElementById('sidebar-close');
  function _openSidebar()  { sidebar && sidebar.classList.add('open');    overlay && overlay.classList.add('open'); }
  function _closeSidebar() { sidebar && sidebar.classList.remove('open'); overlay && overlay.classList.remove('open'); }
  if (menuBtn)  menuBtn.addEventListener('click', _openSidebar);
  if (overlay)  overlay.addEventListener('click', _closeSidebar);
  if (closeBtn) closeBtn.addEventListener('click', _closeSidebar);
  _setupSidebar(user);

  const logoutBtn = document.getElementById('btn-logout');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
      Auth.clearUser();
      window.location.href = '/login';
    });
  }
}

function _setupSidebar(user) {
  const nav = document.getElementById('sidebar-nav');
  if (!nav) return;

  const path = window.location.pathname;
  const LINKS = {
    SOLICITANTE: [
      { href: '/nova-saf',    label: 'Nova SAF',    icon: '&#43;' },
      { href: '/minhas-safs', label: 'Minhas SAFs', icon: '&#128203;' },
    ],
    CCM: [
      { href: '/fila-ccm', label: 'Fila CCM', icon: '&#128203;' },
    ],
    ADMIN: [
      { href: '/admin', label: 'Administração', icon: '&#9881;' },
    ],
  };

  const items = LINKS[user.perfil] || [];
  nav.innerHTML = items.map(({ href, label, icon }) => {
    const active = path === href ? ' active' : '';
    return `<a href="${href}" class="sidebar-link${active}">\
<span class="sidebar-icon">${icon}</span><span>${label}</span></a>`;
  }).join('');

  const logoutSide = document.getElementById('sidebar-logout');
  if (logoutSide) {
    logoutSide.addEventListener('click', () => {
      Auth.clearUser();
      localStorage.clear();
      sessionStorage.clear();
      window.location.href = '/login';
    });
  }

  // Dev profile switcher (only rendered when DEV_MODE=true on server)
  const devSelect = document.getElementById('dev-perfil-select');
  if (devSelect) {
    const DB_PERFIL = { SOLICITANTE: 'Solicitante', CCM: 'CCM', ADMIN: 'Administrador' };
    const DEST      = { SOLICITANTE: '/nova-saf', CCM: '/fila-ccm', ADMIN: '/admin' };
    devSelect.addEventListener('change', async function () {
      const appPerfil = this.value;
      if (!appPerfil) return;
      const res = await API.alterarPerfil(user.id, DB_PERFIL[appPerfil]);
      if (!res.ok) {
        Toast.error(res.data?.erro || 'Erro ao trocar perfil.');
        this.value = '';
        return;
      }
      Auth.setUser({ ...user, perfil: appPerfil });
      window.location.href = DEST[appPerfil] || '/';
    });
  }
}

// =============================================
// FORM VALIDATION
// =============================================
function validateField(input) {
  const val = (input.value || '').trim();
  const required = input.required || input.dataset.required === 'true';
  if (required && val === '') {
    input.classList.add('is-invalid');
    return false;
  }
  input.classList.remove('is-invalid');
  return true;
}

function validateForm(formEl) {
  let valid = true;
  formEl.querySelectorAll('[required], [data-required="true"]').forEach(el => {
    if (!validateField(el)) valid = false;
  });
  return valid;
}

// Character count for inputs with maxlength
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-charcount]').forEach(input => {
    const targetId = input.dataset.charcount;
    const counter = document.getElementById(targetId);
    if (!counter) return;
    const max = parseInt(input.maxLength) || parseInt(input.dataset.max) || 0;
    function update() {
      const len = input.value.length;
      counter.textContent = max ? `${len}/${max}` : len;
      counter.className = 'char-count';
      if (max) {
        if (len >= max)       counter.classList.add('at-limit');
        else if (len >= max * 0.85) counter.classList.add('near-limit');
      }
    }
    input.addEventListener('input', update);
    update();
  });
});

// =============================================
// CONFIRM MODAL (generic reusable popup)
// =============================================
const ConfirmModal = (() => {
  let _onConfirm = null;

  document.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('global-confirm-btn');
    if (btn) {
      btn.addEventListener('click', () => {
        Modal.close('global-confirm-modal');
        if (_onConfirm) { _onConfirm(); _onConfirm = null; }
      });
    }
    // Any element with data-dismiss-confirm closes the modal
    document.querySelectorAll('[data-dismiss-confirm]').forEach(el => {
      el.addEventListener('click', () => {
        Modal.close('global-confirm-modal');
        _onConfirm = null;
      });
    });
  });

  /**
   * Shows a confirmation dialog.
   * @param {object} opts
   * @param {string} opts.title            - Modal title
   * @param {string} opts.message          - HTML message body
   * @param {string} [opts.confirmText]    - Confirm button text
   * @param {string} [opts.confirmClass]   - Confirm button class (e.g. 'btn-danger')
   * @param {function} opts.onConfirm      - Callback when confirmed
   */
  function show({ title, message, confirmText = 'Confirmar', confirmClass = 'btn-primary', onConfirm }) {
    const titleEl = document.getElementById('global-confirm-title');
    const msgEl   = document.getElementById('global-confirm-message');
    const btnEl   = document.getElementById('global-confirm-btn');
    if (titleEl) titleEl.textContent = title || 'Confirmar ação';
    if (msgEl)   msgEl.innerHTML     = message || 'Tem certeza que deseja continuar?';
    if (btnEl) {
      btnEl.textContent = confirmText;
      btnEl.className   = `btn ${confirmClass}`;
    }
    _onConfirm = onConfirm;
    Modal.open('global-confirm-modal');
  }

  return { show };
})();

// =============================================
// PERMISSIONS (Geolocation + Notifications)
// Solicita apenas se ainda não foi concedido/negado.
// =============================================
const Permissions = (() => {

  /** Solicita permissão de Notificação (apenas se ainda não decidido). */
  async function _requestNotifications() {
    if (!('Notification' in window)) return;
    if (Notification.permission !== 'default') return;
    try { await Notification.requestPermission(); } catch (_) {}
  }

  /** Solicita permissão de Geolocalização (apenas se ainda não decidido). */
  async function _requestGeolocation() {
    if (!navigator.geolocation) return;
    try {
      if (navigator.permissions) {
        const status = await navigator.permissions.query({ name: 'geolocation' });
        if (status.state !== 'prompt') return; // já decidido: não perguntar de novo
      }
      // Dispara o prompt do navegador silenciosamente (descarta resultado)
      navigator.geolocation.getCurrentPosition(() => {}, () => {});
    } catch (_) {}
  }

  /**
   * Solicita localização + notificações na tela inicial.
   * Usa localStorage para garantir que só acontece quando o estado for 'prompt'
   * (nunca se já concedido ou negado).
   */
  async function requestAll() {
    await _requestNotifications();
    await _requestGeolocation();
  }

  /**
   * Captura a posição GPS atual.
   * @returns {Promise<GeolocationPosition>}
   */
  function getCurrentPosition(opts) {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error('GPS não disponível neste dispositivo.'));
        return;
      }
      navigator.geolocation.getCurrentPosition(
        resolve,
        reject,
        Object.assign({ enableHighAccuracy: true, timeout: 12000, maximumAge: 60000 }, opts)
      );
    });
  }

  return { requestAll, getCurrentPosition };
})();

// =============================================
// QUERY STRING HELPERS
// =============================================
function getParam(name) {
  return new URLSearchParams(window.location.search).get(name);
}
