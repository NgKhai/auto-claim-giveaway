'use strict';
const $ = (selector) => document.querySelector(selector);
const state = { user: null, mode: 'login', goals: [], opportunities: [], applications: [], audit: [], selectedGoal: null, approval: null, authEpoch: 0 };
function el(tag, text, className) { const node = document.createElement(tag); if (text !== undefined && text !== null) node.textContent = String(text); if (className) node.className = className; return node; }
function notice(message, error = false) { const node = $('#notice'); node.textContent = message; node.classList.toggle('error', error); node.hidden = !message; }
async function api(path, options = {}) {
  const headers = { ...options.headers };
  if (options.body !== undefined) headers['Content-Type'] = 'application/json';
  if (state.user?.csrf_token) headers['X-CSRF-Token'] = state.user.csrf_token;
  const response = await fetch(path, { credentials: 'same-origin', ...options, headers, body: options.body !== undefined ? JSON.stringify(options.body) : undefined });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401 && state.user && !(path === '/api/account/delete' && data.detail === 'Current password is incorrect')) { state.authEpoch++; state.user = null; showAuth(); }
    const detail = data.detail;
    throw new Error(typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map(item => item.msg).join('; ') : `Yêu cầu thất bại (${response.status}). Vui lòng thử lại.`);
  }
  return data;
}
async function busy(button, action) { if (button.disabled) return; button.disabled = true; button.setAttribute('aria-busy', 'true'); try { await action(); } catch (error) { notice(error.message || 'Không thể kết nối. Vui lòng thử lại.', true); } finally { button.disabled = false; button.removeAttribute('aria-busy'); } }
function date(value) { if (!value) return 'Chưa xác minh'; const d = new Date(typeof value === 'number' ? value * 1000 : value); return Number.isNaN(d.getTime()) ? String(value) : d.toLocaleString('vi-VN', { dateStyle: 'medium', timeStyle: 'short' }); }
function showAuth() { state.selectedGoal = null; state.approval = null; state.goals = []; state.opportunities = []; state.applications = []; state.audit = []; $('#current-goal').textContent = 'Danh mục mẫu để kiểm chứng quy trình.'; $('#auth-view').hidden = false; $('#workspace-view').hidden = true; $('#account').hidden = true; for (const selector of ['#approval-dialog', '#account-dialog', '#delete-account-dialog']) if ($(selector).open) $(selector).close(); $('#delete-password').value = ''; }
function showWorkspace() { $('#auth-view').hidden = true; $('#workspace-view').hidden = false; $('#account').hidden = false; $('#account-email').textContent = state.user.email; }
function panel(name) { for (const item of ['discover', 'tracking', 'activity']) $(`#${item}-panel`).hidden = item !== name; for (const tab of document.querySelectorAll('.tab')) { const active = tab.dataset.panel === name; tab.classList.toggle('active', active); if (active) tab.setAttribute('aria-current', 'page'); else tab.removeAttribute('aria-current'); } }
function empty(parent, text) { parent.replaceChildren(el('div', text, 'empty')); }
function badge(text, type = '') { return el('span', text, `badge ${type}`); }
const statuses = { awaiting_approval: 'Chờ bạn phê duyệt', ready: 'Đã duyệt · sẵn sàng', submitted: 'Đã gửi trong sandbox', blocked: 'Bị chặn bởi chính sách', revoked: 'Đã thu hồi quyền', failed: 'Thực thi thất bại', submission_unknown: 'Chưa xác định kết quả' };
function renderGoals() { const target = $('#goals'); target.replaceChildren(); for (const goal of state.goals.slice(0, 6)) { const button = el('button', goal.query, 'goal-chip'); button.type = 'button'; button.addEventListener('click', () => busy(button, async () => { state.selectedGoal = goal.id; $('#current-goal').textContent = goal.query; await refreshOpportunities(); })); target.append(button); } }
function evidenceText(value) { if (typeof value === 'string') return value; if (value === null || value === undefined) return 'Chưa có bằng chứng.'; return JSON.stringify(value, null, 2); }
function renderOpportunities() {
  const target = $('#opportunities'); target.replaceChildren(); $('#opportunity-count').textContent = state.opportunities.length;
  if (!state.opportunities.length) return empty(target, 'Chưa có cơ hội phù hợp trong danh mục mẫu. Hãy thử mục tiêu khác.');
  for (const opportunity of state.opportunities) {
    const card = el('article', null, 'opportunity-card'); const top = el('div', null, 'card-top'); top.append(badge(opportunity.is_sandbox ? 'DỮ LIỆU MẪU' : 'CẦN XÁC MINH', opportunity.is_sandbox ? '' : 'warning'), el('span', `#${opportunity.id}`, 'muted')); card.append(top, el('h3', opportunity.title), el('p', opportunity.description));
    const meta = el('div', null, 'card-meta'); const region = el('span', 'Khu vực'); region.append(el('strong', opportunity.country || 'Chưa xác minh')); const deadline = el('span', 'Hạn đăng ký'); deadline.append(el('strong', date(opportunity.deadline))); meta.append(region, deadline); card.append(meta);
    const evidence = el('div', null, 'evidence'); evidence.append(el('strong', 'Bằng chứng & nguồn'), el('p', evidenceText(opportunity.evidence)));
    if (opportunity.source_url) { let url; try { url = new URL(opportunity.source_url, window.location.origin); } catch {} if (url && ['https:', 'http:'].includes(url.protocol) && (url.protocol === 'https:' || url.origin === window.location.origin)) { const link = el('a', opportunity.source_url, 'source-link'); link.href = url.href; link.target = '_blank'; link.rel = 'noopener noreferrer'; evidence.append(link); } else evidence.append(el('p', opportunity.source_url)); }
    card.append(evidence); const bottom = el('div', null, 'card-bottom'); bottom.append(el('small', 'Chính sách được kiểm tra trước khi duyệt.')); const button = el('button', 'Đánh giá đăng ký ↗', 'primary'); button.addEventListener('click', () => busy(button, async () => { const application = await api('/api/applications', { method: 'POST', body: { opportunity_id: opportunity.id } }); await refresh(); panel('tracking'); notice(application.status === 'blocked' ? 'Hành động đã bị chính sách chặn. Xem lý do bên dưới.' : 'Đã tạo yêu cầu. Kiểm tra dữ liệu và phê duyệt trước khi gửi.'); })); bottom.append(button); card.append(bottom); target.append(card);
  }
}
function openApproval(application) {
  state.approval = application; const target = $('#approval-details'); target.replaceChildren();
  const action = application.action || {};
  target.append(el('dt', 'Hành động'), el('dd', action.name || 'Chưa xác minh'), el('dt', 'Đích đến'), el('dd', action.destination || 'Chưa xác minh'), el('dt', 'Phiên bản adapter'), el('dd', action.adapter_version ?? 'Chưa xác minh'));
  $('#approval-confirm').disabled = !action.name || !action.destination || !action.adapter_version;
  const payload = application.payload || {}; for (const [key, value] of Object.entries(payload)) target.append(el('dt', key), el('dd', typeof value === 'object' ? JSON.stringify(value) : value));
  if (!Object.keys(payload).length) target.append(el('dt', 'Nội dung'), el('dd', 'Không có trường dữ liệu trong payload.'));
  $('#approval-version').textContent = `Yêu cầu #${application.id} · Phiên bản ${application.version}. Quyền duyệt có hiệu lực 15 phút; thay đổi nội dung hoặc hành động cần duyệt lại.`; $('#approval-dialog').showModal();
}
function renderApplications() {
  const target = $('#applications'); target.replaceChildren(); $('#application-count').textContent = state.applications.length;
  if (!state.applications.length) return empty(target, 'Chưa có yêu cầu đăng ký. Chọn một cơ hội để xem đánh giá chính sách.');
  for (const application of state.applications.slice().reverse()) {
    const card = el('article', null, 'application-card'); const heading = el('div', null, 'application-header'); heading.append(el('h3', application.title || `Yêu cầu #${application.id}`), badge(statuses[application.status] || application.status, application.status === 'blocked' || application.status === 'failed' ? 'blocked' : application.status === 'awaiting_approval' ? 'warning' : '')); card.append(heading, el('p', application.policy_reason || 'Đăng ký chỉ được thực hiện trong sandbox.'));
    card.append(el('pre', JSON.stringify(application.payload || {}, null, 2), 'payload'));
    if (application.receipt) card.append(el('p', `Biên nhận sandbox: ${typeof application.receipt === 'string' ? application.receipt : JSON.stringify(application.receipt)}`));
    const actions = el('div', null, 'application-actions');
    if (application.status === 'ready') card.append(el('p', `Quyền duyệt hết hạn: ${date(application.approval_expires)}`));
    const expired = application.status === 'ready' && (!application.approval_expires || application.approval_expires * 1000 <= Date.now());
    if (application.status === 'revoked' || expired) { const retry = el('button', 'Đánh giá lại để xin quyền mới', 'primary'); retry.addEventListener('click', () => busy(retry, async () => { await api('/api/applications', { method: 'POST', body: { opportunity_id: application.opportunity_id } }); await refresh(); notice('Đã đánh giá lại. Vui lòng kiểm tra và duyệt phiên bản mới.'); })); actions.append(retry); }
    if (application.status === 'awaiting_approval') { const approve = el('button', 'Xem & duyệt dữ liệu', 'primary'); approve.addEventListener('click', () => openApproval(application)); actions.append(approve); }
    if (application.status === 'ready' && !expired) { const submit = el('button', 'Gửi trong sandbox ↗', 'primary'); submit.addEventListener('click', () => busy(submit, async () => { try { await api(`/api/applications/${application.id}/submit`, { method: 'POST', body: {} }); } catch (error) { await refresh(); throw new Error(`${error.message} Nếu quyền đã hết hạn hoặc bị thu hồi, hãy chọn đánh giá lại để duyệt phiên bản mới.`); } await refresh(); notice('Đã hoàn tất thao tác trong sandbox. Không có đăng ký bên ngoài.'); })); actions.append(submit); }
    if (['awaiting_approval', 'ready'].includes(application.status)) { const revoke = el('button', 'Thu hồi quyền', 'secondary'); revoke.addEventListener('click', () => busy(revoke, async () => { await api(`/api/applications/${application.id}/revoke`, { method: 'POST', body: {} }); await refresh(); notice('Đã thu hồi quyền cho yêu cầu này.'); })); actions.append(revoke); }
    card.append(actions); target.append(card);
  }
}
function renderAudit() { const target = $('#audit'); target.replaceChildren(); if (!state.audit.length) return empty(target, 'Các hoạt động sẽ xuất hiện tại đây.'); for (const entry of state.audit) { const item = el('article', null, 'audit-item'); const content = el('div'); content.append(el('strong', entry.action || entry.event || 'Sự kiện')); const detail = entry.details || entry.detail || entry.data; if (detail) content.append(el('pre', typeof detail === 'string' ? detail : JSON.stringify(detail, null, 2))); const time = el('time', date(entry.created_at || entry.timestamp)); item.append(content, time); target.append(item); } }
async function refreshOpportunities() { const epoch = state.authEpoch; const opportunities = await api(`/api/opportunities${state.selectedGoal ? `?goal_id=${encodeURIComponent(state.selectedGoal)}` : ''}`); if (epoch !== state.authEpoch) return; state.opportunities = opportunities; renderOpportunities(); }
async function refresh() { const epoch = state.authEpoch; const [goals, applications, audit] = await Promise.all([api('/api/goals'), api('/api/applications'), api('/api/audit')]); if (epoch !== state.authEpoch) return; Object.assign(state, { goals, applications, audit }); renderGoals(); renderApplications(); renderAudit(); await refreshOpportunities(); }
$('#auth-mode').addEventListener('click', () => { state.mode = state.mode === 'login' ? 'register' : 'login'; const register = state.mode === 'register'; $('#auth-title').textContent = register ? 'Tạo không gian của bạn' : 'Chào mừng trở lại'; $('#auth-description').textContent = register ? 'Bắt đầu với một tài khoản riêng và quyền kiểm soát rõ ràng.' : 'Đăng nhập để tiếp tục theo dõi cơ hội của bạn.'; $('#country-field').hidden = !register; $('#password').autocomplete = register ? 'new-password' : 'current-password'; $('#auth-submit').textContent = register ? 'Tạo tài khoản ↗' : 'Đăng nhập ↗'; $('#auth-toggle-label').textContent = register ? 'Đã có tài khoản?' : 'Bạn chưa có tài khoản?'; $('#auth-mode').textContent = register ? 'Đăng nhập' : 'Tạo tài khoản'; notice(''); });
$('#auth-form').addEventListener('submit', event => { event.preventDefault(); busy($('#auth-submit'), async () => { const body = { email: $('#email').value.trim(), password: $('#password').value }; if (state.mode === 'register') body.country = $('#country').value; state.user = await api(`/api/auth/${state.mode}`, { method: 'POST', body }); state.authEpoch++; $('#password').value = ''; showWorkspace(); notice(''); await refresh(); }); });
$('#logout').addEventListener('click', () => busy($('#logout'), async () => { await api('/api/auth/logout', { method: 'POST', body: {} }); state.authEpoch++; Object.assign(state, { user: null, goals: [], opportunities: [], applications: [], audit: [], selectedGoal: null }); showAuth(); notice('Đã đăng xuất.'); }));
$('#goal-form').addEventListener('submit', event => { event.preventDefault(); busy($('#goal-form button'), async () => { const query = $('#goal-query').value.trim(); if (!query) throw new Error('Hãy nhập mục tiêu bạn muốn tìm.'); const goal = await api('/api/goals', { method: 'POST', body: { query } }); state.selectedGoal = goal.id; $('#current-goal').textContent = goal.query; await refresh(); panel('discover'); notice('Đã lưu mục tiêu và đối chiếu danh mục cơ hội mẫu.'); }); });
for (const tab of document.querySelectorAll('.tab')) tab.addEventListener('click', () => panel(tab.dataset.panel));
$('#refresh').addEventListener('click', () => busy($('#refresh'), async () => { await refresh(); notice('Đã cập nhật dữ liệu.'); }));
$('#approval-cancel').addEventListener('click', () => $('#approval-dialog').close());
$('#approval-confirm').addEventListener('click', () => busy($('#approval-confirm'), async () => { const application = state.approval; if (!application) return; await api(`/api/applications/${application.id}/approve`, { method: 'POST', body: { version: application.version } }); $('#approval-dialog').close(); state.approval = null; await refresh(); notice('Đã duyệt phiên bản này. Bạn có thể gửi trong sandbox hoặc thu hồi quyền.'); }));
(async () => { try { state.user = await api('/api/me'); showWorkspace(); await refresh(); } catch (error) { if (state.user) notice(error.message, true); else showAuth(); } })();

$('#account-settings').addEventListener('click', () => $('#account-dialog').showModal());
$('#export-account').addEventListener('click', () => busy($('#export-account'), async () => {
  const data = await api('/api/account/export');
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = el('a'); link.href = url; link.download = 'opportunity-hunter-export.json'; document.body.append(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  notice('Bản xuất dữ liệu đã được tạo. Hãy lưu tệp ở nơi riêng tư.');
}));
$('#begin-delete-account').addEventListener('click', () => {
  $('#account-dialog').close(); $('#delete-password').value = ''; $('#delete-error').hidden = true; $('#delete-error').textContent = ''; $('#delete-account-dialog').showModal(); $('#delete-password').focus();
});
$('#cancel-delete-account').addEventListener('click', () => { $('#delete-account-dialog').close(); $('#delete-password').value = ''; $('#account-dialog').showModal(); });
$('#delete-account-dialog').addEventListener('close', () => { $('#delete-password').value = ''; });
$('#delete-account-form').addEventListener('submit', event => {
  event.preventDefault();
  busy($('#confirm-delete-account'), async () => {
    $('#delete-error').hidden = true;
    try { await api('/api/account/delete', { method: 'POST', body: { password: $('#delete-password').value } }); }
    catch (error) { $('#delete-error').textContent = error.message; $('#delete-error').hidden = false; $('#delete-password').value = ''; $('#delete-password').focus(); return; }
    state.authEpoch++; state.user = null; showAuth(); $('#goal-query').value = ''; notice('Đã xóa tài khoản và dữ liệu trên ứng dụng này.');
  });
});
