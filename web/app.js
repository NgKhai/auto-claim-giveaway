'use strict';
const $ = (selector) => document.querySelector(selector);
const state = { user: null, mode: 'login', goals: [], opportunities: [], applications: [], audit: [], sources: [], sourceAnalyses: {}, sourceAnalysisPending: {}, sourcesTimer: null, selectedGoal: null, approval: null, authEpoch: 0 };
function el(tag, text, className) { const node = document.createElement(tag); if (text !== undefined && text !== null) node.textContent = String(text); if (className) node.className = className; return node; }
function notice(message, error = false) { const node = $('#notice'); node.textContent = message; node.classList.toggle('error', error); node.hidden = !message; }
async function api(path, options = {}) {
  const requestEpoch = state.authEpoch;
  const headers = { ...options.headers };
  if (options.body !== undefined) headers['Content-Type'] = 'application/json';
  if (state.user?.csrf_token) headers['X-CSRF-Token'] = state.user.csrf_token;
  const response = await fetch(path, { credentials: 'same-origin', ...options, headers, body: options.body !== undefined ? JSON.stringify(options.body) : undefined });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401 && requestEpoch === state.authEpoch && state.user && !(path === '/api/account/delete' && data.detail === 'Current password is incorrect')) { state.authEpoch++; state.user = null; showAuth(); }
    const detail = data.detail;
    throw new Error(typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map(item => item.msg).join('; ') : `Yêu cầu thất bại (${response.status}). Vui lòng thử lại.`);
  }
  return data;
}
async function busy(button, action) { if (button.disabled) return; button.disabled = true; button.setAttribute('aria-busy', 'true'); try { await action(); } catch (error) { notice(error.message || 'Không thể kết nối. Vui lòng thử lại.', true); } finally { button.disabled = false; button.removeAttribute('aria-busy'); } }
function date(value) { if (!value) return 'Chưa xác minh'; const d = new Date(typeof value === 'number' ? value * 1000 : value); return Number.isNaN(d.getTime()) ? String(value) : d.toLocaleString('vi-VN', { dateStyle: 'medium', timeStyle: 'short' }); }
function showAuth() { clearTimeout(state.sourcesTimer); state.sourcesTimer = null; state.sources = []; state.sourceAnalyses = {}; state.sourceAnalysisPending = {}; $('#sources').replaceChildren(); state.selectedGoal = null; state.approval = null; state.goals = []; state.opportunities = []; state.applications = []; state.audit = []; $('#current-goal').textContent = 'Danh mục mẫu để kiểm chứng quy trình.'; $('#auth-view').hidden = false; $('#workspace-view').hidden = true; $('#account').hidden = true; for (const selector of ['#approval-dialog', '#account-dialog', '#delete-account-dialog']) if ($(selector).open) $(selector).close(); $('#delete-password').value = ''; }
function showWorkspace() { $('#auth-view').hidden = true; $('#workspace-view').hidden = false; $('#account').hidden = false; $('#account-email').textContent = state.user.email; }
function panel(name) { for (const item of ['discover', 'tracking', 'sources', 'activity']) $(`#${item}-panel`).hidden = item !== name; for (const tab of document.querySelectorAll('.tab')) { const active = tab.dataset.panel === name; tab.classList.toggle('active', active); if (active) tab.setAttribute('aria-current', 'page'); else tab.removeAttribute('aria-current'); } }
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
async function refresh() { const epoch = state.authEpoch; const [goals, applications, audit, sources] = await Promise.all([api('/api/goals'), api('/api/applications'), api('/api/audit'), api('/api/sources')]); if (epoch !== state.authEpoch) return; Object.assign(state, { goals, applications, audit, sources }); renderGoals(); renderApplications(); renderAudit(); renderSources(); await refreshOpportunities(); }
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

function sourceLink(url, label) {
  let parsed; try { parsed = new URL(url); } catch { return el('span', url || 'Chưa xác minh'); }
  if (parsed.protocol !== 'https:') return el('span', url);
  const link = el('a', label || url, 'source-link'); link.href = parsed.href; link.target = '_blank'; link.rel = 'noopener noreferrer'; return link;
}
function renderSources() {
  clearTimeout(state.sourcesTimer); state.sourcesTimer = null;
  const target = $('#sources'); target.replaceChildren();
  if (!state.sources.length) return empty(target, 'Chưa có nguồn chính thức trong danh sách cho phép.');
  let nextCooldown = Infinity;
  let nextEvidenceExpiry = Infinity;
  const labels = { not_fetched: 'Chưa truy xuất', fresh: 'Bản lưu gần đây', stale: 'Bản lưu đã cũ', unverified: 'Lần truy xuất mới chưa xác minh' };
  for (const source of state.sources) {
    const card = el('article', null, 'source-card'); card.dataset.sourceId = source.id;
    const evidenceExpiry = (source.evidence?.retrieved_at || 0) * 1000 + 86400000;
    const aged = Boolean(source.evidence) && evidenceExpiry <= Date.now();
    if (source.evidence && !aged) nextEvidenceExpiry = Math.min(nextEvidenceExpiry, evidenceExpiry - Date.now());
    const displayStatus = source.status === 'fresh' && aged ? 'stale' : source.status;
    const top = el('div', null, 'card-top'); top.append(badge('CHỈ ĐỌC'), badge(labels[displayStatus] || 'Chưa xác minh', displayStatus === 'fresh' ? '' : 'warning'));
    card.append(top, el('h3', source.title));
    const urls = el('div', null, 'source-urls'); urls.append(el('strong', 'Trang chính thức'), sourceLink(source.canonical_url || source.source_url), el('strong', 'Địa chỉ tài liệu được đọc'), sourceLink(source.source_url)); card.append(urls);
    const attribution = el('p', null, 'source-attribution'); attribution.append(el('span', source.attribution || 'GitHub documentation contributors')); if (source.license_url) { attribution.append(document.createTextNode(' · '), sourceLink(source.license_url, source.license || 'Giấy phép nội dung')); } card.append(attribution);
    card.append(el('p', 'Phạm vi: đọc bằng chứng về điều kiện. Đủ điều kiện: chưa xác minh. Hạn đăng ký: chưa xác minh. Quyền automation: chưa xác minh.', 'muted'));
    const evidence = source.evidence;
    if (evidence) {
      const meta = el('dl', null, 'source-metadata'); meta.append(el('dt', 'Truy xuất thành công lúc'), el('dd', date(evidence.retrieved_at)), el('dt', 'SHA-256 nội dung'), el('dd', evidence.content_hash || 'Chưa có hash'));
      card.append(meta);
      const freshness = aged ? 'stale' : evidence.freshness || source.evidence_freshness || 'unknown';
      card.append(badge(freshness === 'fresh' ? 'BẢN LƯU: TRONG 24 GIỜ' : freshness === 'stale' ? 'BẢN LƯU: QUÁ 24 GIỜ' : 'TUỔI BẢN LƯU: CHƯA XÁC MINH', freshness === 'fresh' ? '' : 'warning'));
      if (evidence.changed) card.append(el('p', 'Nội dung đã thay đổi so với bản lưu thành công trước đó. Hãy đọc lại; thay đổi này không tự cấp quyền hoặc xác nhận điều kiện.', 'source-change'));
      const details = el('details', null, 'source-excerpt'); details.open = true; details.append(el('summary', 'Trích đoạn Markdown gốc (tối đa 4.000 ký tự) · chưa xử lý mẫu Liquid'), el('pre', evidence.excerpt || 'Bản lưu chưa có trích đoạn.')); card.append(details, el('p', 'Đây là trích đoạn từ tài liệu gốc, có thể bị cắt và chứa chỉ thị mẫu Liquid chưa được mở rộng. Nội dung không đầy đủ để tự kết luận điều kiện hoặc quyền lợi.', 'muted'));
      if (displayStatus === 'stale') card.append(el('p', 'Bản lưu đã quá thời hạn mới. Hãy đọc lại nguồn để kiểm tra thay đổi.', 'source-change'));
      if (source.status === 'unverified') card.append(el('p', 'Lần cập nhật mới nhất chưa thành công. Tuổi của bản lưu thành công được hiển thị riêng; chưa xác minh được nội dung hiện tại tại nguồn.', 'source-change'));
    } else card.append(el('p', 'Chưa có bản lưu. Chọn “Đọc nguồn chính thức” để truy xuất tài liệu qua máy chủ.', 'muted'));
    if (source.last_error) card.append(el('p', `Không thể xác minh lần truy xuất mới (${source.last_error}). Bản lưu thành công trước đó được giữ nguyên. Kiểm tra kết nối hoặc chính sách truy cập rồi thử lại sau thời gian chờ.`, 'source-error'));
    if (source.last_attempt_at) card.append(el('p', `Lần thử gần nhất: ${date(source.last_attempt_at)}`, 'muted'));
    const cooldown = Math.max(0, (source.cooldown_until || 0) * 1000 - Date.now());
    const button = el('button', cooldown > 0 ? `Thử lại sau ${Math.ceil(cooldown / 1000)} giây` : evidence ? 'Đọc lại nguồn chính thức' : 'Đọc nguồn chính thức', 'primary'); button.dataset.sourceRefresh = source.id; button.disabled = cooldown > 0;
    if (cooldown > 0) nextCooldown = Math.min(nextCooldown, cooldown);
    button.addEventListener('click', () => busy(button, async () => {
      const epoch = state.authEpoch; let failure = null; delete state.sourceAnalyses[source.id]; delete state.sourceAnalysisPending[source.id];
      try { await api(`/api/sources/${encodeURIComponent(source.id)}/refresh`, { method: 'POST', body: {} }); } catch (error) { failure = error; }
      if (epoch !== state.authEpoch) return;
      const sources = await api('/api/sources'); if (epoch !== state.authEpoch) return;
      state.sources = sources; renderSources();
      if (failure) notice(`${failure.message} Bằng chứng đã lưu được giữ nguyên; hãy xem trạng thái nguồn và thời gian thử lại.`, true);
      else notice('Đã đọc nguồn chính thức và lưu bằng chứng. Điều kiện, phần thưởng và quyền automation vẫn cần xác minh riêng.');
    }));
    card.append(button, el('small', 'Giới hạn: tối đa một lần thử mỗi 60 giây cho mỗi tài khoản. Không có thao tác đăng ký từ nguồn này.'));
    const analysisButton = el('button', state.sourceAnalysisPending[source.id] ? 'Đang đọc điều kiện…' : 'Xem điều kiện', 'secondary source-analysis-button'); analysisButton.dataset.sourceAnalysis = source.id; analysisButton.disabled = Boolean(state.sourceAnalysisPending[source.id]);
    analysisButton.addEventListener('click', () => loadSourceAnalysis(source)); card.append(analysisButton);
    const cached = state.sourceAnalyses[source.id];
    if (cached && cached.snapshot === sourceSnapshot(source)) card.append(renderSourceAnalysis(cached.data));
    else if (cached) { delete state.sourceAnalyses[source.id]; if (aged) card.append(renderSourceAnalysis({ ...cached.data, status: 'needs_refresh', reason: 'evidence_requires_refresh', claims: {} })); }
    target.append(card);
  }
  const nextUpdate = Math.min(Number.isFinite(nextCooldown) ? Math.min(nextCooldown + 30, 1000) : Infinity, nextEvidenceExpiry + 30);
  if (Number.isFinite(nextUpdate)) { const epoch = state.authEpoch; state.sourcesTimer = setTimeout(() => { if (epoch === state.authEpoch && state.user) renderSources(); }, Math.max(30, nextUpdate)); }
}

function sourceSnapshot(source) { return JSON.stringify([source.evidence?.content_hash || null, source.evidence?.retrieved_at || null, source.evidence?.freshness || null, source.status, source.last_error || null, Boolean(source.evidence) && Date.now() - source.evidence.retrieved_at * 1000 >= 86400000]); }
async function loadSourceAnalysis(source) {
  if (state.sourceAnalysisPending[source.id]) return;
  const epoch = state.authEpoch; const snapshot = sourceSnapshot(source); const request = {};
  state.sourceAnalysisPending[source.id] = request; renderSources();
  try {
    const analysis = await api(`/api/sources/${encodeURIComponent(source.id)}/analysis`);
    if (epoch !== state.authEpoch || state.sourceAnalysisPending[source.id] !== request) return;
    const current = state.sources.find(item => item.id === source.id);
    if (!current || snapshot !== sourceSnapshot(current) || analysis.content_hash !== (current.evidence?.content_hash || null) || analysis.retrieved_at !== (current.evidence?.retrieved_at || null)) {
      delete state.sourceAnalyses[source.id];
      const sources = await api('/api/sources'); if (epoch !== state.authEpoch) return;
      state.sources = sources; notice('Nguồn đã thay đổi. Đã bỏ kết quả cũ và cập nhật bản lưu; chọn xem điều kiện lại để đối chiếu.', true); return;
    }
    state.sourceAnalyses[source.id] = { snapshot, data: analysis };
  } catch (error) { if (epoch === state.authEpoch) notice(`Không thể đọc điều kiện: ${error.message}`, true); }
  finally { if (epoch === state.authEpoch && state.sourceAnalysisPending[source.id] === request) { delete state.sourceAnalysisPending[source.id]; renderSources(); } }
}
function renderSourceAnalysis(analysis) {
  const section = el('section', null, 'source-analysis'); section.dataset.analysisStatus = analysis.status;
  section.append(el('h4', 'Điều kiện trích xuất cần đối chiếu'), el('p', 'Đây là các dấu hiệu được đối chiếu theo mẫu trong bản lưu, chưa phải kết luận bạn đủ điều kiện. Không xác nhận quyền lợi, hạn đăng ký hoặc quyền automation.', 'muted'));
  const labels = { candidate_claims: 'Có dấu hiệu cần kiểm tra lại', unknown: 'Chưa đủ bằng chứng để trích xuất', needs_refresh: 'Cần cập nhật nguồn trước khi đối chiếu' };
  section.append(badge(labels[analysis.status] || 'Chưa xác minh', 'warning'));
  if (analysis.reason) section.append(el('p', analysisReason(analysis.reason), 'muted'));
  if (analysis.status === 'needs_refresh') section.append(el('p', 'Bản lưu đã cũ hoặc lần cập nhật mới nhất thất bại. Chọn đọc lại nguồn chính thức, đợi hết thời gian chờ nếu có, rồi xem điều kiện lại.', 'source-change'));
  if (analysis.status === 'unknown') section.append(el('p', 'Chưa có bản lưu phù hợp, tài liệu bị cắt hoặc không nhận diện được phần điều kiện. Không suy ra “không có yêu cầu” từ phần thiếu. Hãy đọc nguồn chính thức để kiểm tra.', 'muted'));
  const names = { minimum_age: 'Độ tuổi tối thiểu', enrollment_required: 'Yêu cầu đang theo học', student_status_evidence_required: 'Bằng chứng tình trạng sinh viên', personal_account_required: 'Tài khoản cá nhân' };
  for (const [key, title] of Object.entries(names)) {
    const claim = analysis.claims?.[key]; const item = el('article', null, 'source-claim'); item.dataset.claim = key;
    item.append(el('h5', title));
    const candidate = claim?.state === 'candidate' && claim.citation;
    item.append(el('p', candidate ? key === 'minimum_age' ? `Dấu hiệu cần đối chiếu: từ ${claim.value} tuổi.` : 'Dấu hiệu cần đối chiếu: có yêu cầu.' : 'Chưa xác định từ bản lưu. Đây không phải kết luận không có yêu cầu.', candidate ? 'claim-candidate' : 'muted'));
    if (!candidate && claim?.reason) item.append(el('p', analysisReason(claim.reason), 'muted'));
    if (candidate) {
      const citation = claim.citation; item.append(el('blockquote', citation.quote, 'claim-quote'));
      const provenance = el('details', null, 'claim-provenance'); provenance.append(el('summary', 'Đối chiếu trích dẫn'));
      const data = el('dl'); data.append(el('dt', 'Nguồn'), el('dd', citation.source_url), el('dt', 'Truy xuất lúc'), el('dd', date(citation.retrieved_at)), el('dt', 'Hash bản nguồn'), el('dd', citation.content_hash), el('dt', 'Vị trí trong trích đoạn'), el('dd', `Ký tự Unicode ${citation.start} đến trước ${citation.end}`), el('dt', 'Phiên bản bộ đối chiếu'), el('dd', citation.extractor_version)); provenance.append(data); item.append(provenance);
    }
    section.append(item);
  }
  section.append(el('small', `Phương pháp: đối chiếu mẫu cố định · ${analysis.extractor_version || 'chưa xác minh'}. Không sử dụng LLM để cấp quyền.`));
  return section;
}

function analysisReason(reason) {
  const reasons = {
    no_cached_evidence: 'Chưa có bản lưu. Hãy đọc nguồn chính thức trước khi xem điều kiện.',
    not_observed: 'Không tìm thấy cách diễn đạt được hỗ trợ cho điều kiện này. Hãy đối chiếu trực tiếp tài liệu.',
    invalid_evidence: 'Bản lưu thiếu dữ liệu để đối chiếu. Hãy đọc lại nguồn chính thức.',
    evidence_requires_refresh: 'Bản lưu đã cũ hoặc lần cập nhật gần nhất thất bại. Hãy đọc lại nguồn trước khi tiếp tục.',
    excerpt_truncated: 'Trích đoạn bị cắt; có thể thiếu điều kiện quan trọng. Đối chiếu tài liệu đầy đủ tại trang chính thức.',
    unsupported_source: 'Chưa hỗ trợ đối chiếu điều kiện từ nguồn này. Hãy kiểm tra thủ công.',
    qualification_section_missing_or_ambiguous: 'Không tìm thấy duy nhất một phần điều kiện phù hợp. Cấu trúc tài liệu có thể đã thay đổi; hãy kiểm tra trang chính thức.',
    unsupported_qualification_content: 'Nội dung phần điều kiện không khớp mẫu được hỗ trợ. Hãy đọc trực tiếp; ứng dụng không tự suy diễn yêu cầu.',
    conflicting_candidate_claims: 'Các dấu hiệu về điều kiện này mâu thuẫn. Không chọn một giá trị; hãy xác minh với nguồn chính thức.',
    candidate_claims_require_manual_review: 'Có cách diễn đạt khớp mẫu. Bạn cần kiểm tra từng trích dẫn cùng bối cảnh tại nguồn trước khi sử dụng.',
    no_recognized_claims: 'Chưa nhận diện được điều kiện nào từ mẫu hỗ trợ. Không suy ra rằng chương trình không có điều kiện.'
  };
  return reasons[reason] || 'Chưa thể xác minh điều kiện này từ bản lưu. Hãy đọc tài liệu chính thức để đối chiếu.';
}
