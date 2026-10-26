'use client';

import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react';
import './DeliveryControlCenter.css';

type ViewId = 'overview' | 'orders' | 'exceptions' | 'runs' | 'workflow' | 'configuration';
type CenterData = any;

const navigation: Array<{ id: ViewId; label: string; icon: string }> = [
  { id: 'overview', label: 'Overview', icon: '◫' },
  { id: 'orders', label: 'Purchase orders', icon: '▤' },
  { id: 'exceptions', label: 'Delivery exceptions', icon: '⚑' },
  { id: 'runs', label: 'Automation run center', icon: '◷' },
  { id: 'workflow', label: 'Workflow & evidence', icon: '⌘' },
  { id: 'configuration', label: 'Configuration', icon: '⚙' },
];

const fmtDate = (value?: string | null) => value ? new Date(`${value.slice(0, 10)}T00:00:00`).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : 'Not available';
const fmtTime = (value?: string | null) => value ? new Date(value).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' }) : 'No run yet';
const pretty = (value?: string) => value ? value.replaceAll('_', ' ').toLowerCase().replace(/\b\w/g, (letter) => letter.toUpperCase()) : 'Unknown';

export function DeliveryControlCenter() {
  const [view, setView] = useState<ViewId>('overview');
  const [data, setData] = useState<CenterData | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('all');
  const [selectedOrder, setSelectedOrder] = useState<string | null>(null);
  const [authConfigured, setAuthConfigured] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);
  const [authNeeded, setAuthNeeded] = useState(false);
  const [showAuth, setShowAuth] = useState(false);
  const [authError, setAuthError] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [settings, setSettings] = useState({ upcomingDays: 7, dueDateBasis: 'contractual', timezone: 'Asia/Kolkata' });
  const [settingsMessage, setSettingsMessage] = useState('');
  const [busy, setBusy] = useState(false);

  const load = useCallback(async (quiet = false) => {
    if (!quiet) setLoading(true);
    setError('');
    try {
      const response = await fetch('/api/delivery/data', { cache: 'no-store' });
      const result = await response.json();
      if (response.status === 401) {
        setAuthNeeded(true);
        setData(null);
        setError(result.error || 'Sign in to view live procurement data.');
      } else if (!response.ok) throw new Error(result.error || 'Delivery data could not be loaded.');
      else {
        setData(result);
        setAuthNeeded(false);
        setSettings({ upcomingDays: result.settings.upcomingDays, dueDateBasis: result.settings.dueDateBasis, timezone: result.settings.timezone });
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Delivery data could not be loaded.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetch('/api/delivery/session').then((response) => response.json()).then((result) => { setAuthConfigured(Boolean(result.configured)); setAuthenticated(Boolean(result.authenticated)); }).catch(() => undefined);
    void load();
  }, [load]);

  useEffect(() => {
    if (!data?.runs?.some((run: any) => run.status === 'QUEUED' || run.status === 'RUNNING')) return;
    const timer = window.setInterval(() => void load(true), 2500);
    return () => window.clearInterval(timer);
  }, [data?.runs, load]);

  const orders = data?.purchaseOrders || [];
  const visibleOrders = useMemo(() => orders.filter((order: any) => {
    const text = `${order.id} ${order.supplier} ${order.items.map((item: any) => item.itemCode).join(' ')}`.toLowerCase();
    const assessments = order.assessments || [];
    const status = filter === 'all' || (filter === 'received'
      ? assessments.length > 0 && assessments.every((item: any) => item.deliveryStatus === 'RECEIVED')
      : assessments.some((item: any) => item.deliveryStatus.toLowerCase() === filter || (filter === 'partial' && item.partialReceipt)));
    return text.includes(search.trim().toLowerCase()) && status;
  }), [orders, search, filter]);
  const currentOrder = orders.find((order: any) => order.id === selectedOrder) || null;
  const currentView = navigation.find((item) => item.id === view)!;

  async function signIn(event: FormEvent) {
    event.preventDefault();
    setAuthError('');
    setBusy(true);
    try {
      const response = await fetch('/api/delivery/session', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ username, password }) });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || 'Sign-in failed.');
      setAuthenticated(true);
      setAuthNeeded(false);
      setShowAuth(false);
      setPassword('');
      await load();
    } catch (cause) { setAuthError(cause instanceof Error ? cause.message : 'Sign-in failed.'); }
    finally { setBusy(false); }
  }

  async function signOut() {
    await fetch('/api/delivery/session', { method: 'DELETE' });
    setAuthenticated(false);
    setShowAuth(false);
    await load();
  }

  async function startRun() {
    setBusy(true);
    try {
      const idempotencyKey = typeof crypto !== 'undefined' && 'randomUUID' in crypto ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`;
      const response = await fetch('/api/delivery/runs', { method: 'POST', headers: { 'Idempotency-Key': idempotencyKey } });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || 'Unable to start the ART run.');
      setView('runs');
      await load(true);
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to start run.'); }
    finally { setBusy(false); }
  }

  async function saveConfiguration(event: FormEvent) {
    event.preventDefault();
    setSettingsMessage('');
    setBusy(true);
    try {
      const response = await fetch('/api/delivery/config', { method: 'PUT', headers: { 'content-type': 'application/json' }, body: JSON.stringify(settings) });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || 'Configuration could not be saved.');
      setSettingsMessage('Configuration saved. The due-date basis changes overdue classification.');
      await load(true);
    } catch (cause) { setSettingsMessage(cause instanceof Error ? cause.message : 'Configuration could not be saved.'); }
    finally { setBusy(false); }
  }

  return (
    <div className="delivery-shell">
      <aside className="delivery-sidebar">
        <div className="delivery-brand">
          <div className="brand-mark">P2</div>
          <div><strong>DELIVERY</strong><span>CONTROL CENTER</span></div>
        </div>
        <div className="workspace-label">PROCUREMENT WORKSPACE</div>
        <nav className="delivery-nav" aria-label="P02 workspace">
          {navigation.map((item) => <button key={item.id} className={view === item.id ? 'active' : ''} onClick={() => setView(item.id)}><span className="nav-icon" aria-hidden="true">{item.icon}</span><span>{item.label}</span>{item.id === 'exceptions' && data?.metrics?.needsVerification > 0 && <span className="nav-count">{data.metrics.needsVerification}</span>}</button>)}
        </nav>
        <div className="sidebar-bottom">
          <div className="sidebar-process"><span className="process-dot" /> P02 <span>Supplier delivery</span></div>
          <div className="sidebar-owner"><span className="avatar">V</span><span><b>Vrushali Poojary</b><small>Process owner</small></span></div>
        </div>
      </aside>

      <main className="delivery-main">
        <header className="delivery-topbar">
          <div className="breadcrumb">Procurement <span>/</span> P02 <span>/</span> <b>{currentView.label}</b></div>
          <div className="topbar-actions">
            {data?.source === 'synthetic demonstration data' && <span className="demo-pill"><span /> DEMO DATA</span>}
            {data?.settings?.mode === 'configured' && <span className="live-pill"><span /> ART {pretty(data.integrations.readiness)}</span>}
            {authenticated && <button className="quiet-button" onClick={signOut}>Sign out</button>}
            <button className="icon-button" onClick={() => void load()} aria-label="Refresh data" title="Refresh">↻</button>
          </div>
        </header>

        <div className="delivery-content">
          <div className="page-heading">
            <div><div className="eyebrow">P02 · SUPPLIER DELIVERY</div><h1>{currentView.label}</h1><p>Supplier Delivery Confirmation &amp; Delay Escalation</p></div>
            {view === 'runs' && <button className="primary-button" disabled={busy || data?.settings?.mode !== 'configured' || !authenticated} onClick={() => void startRun()}><span>▶</span> {busy ? 'Starting…' : 'Run monitoring now'}</button>}
          </div>

          {error && <div className="notice notice-warning"><span>!</span><div><b>{authNeeded ? 'Sign-in required' : 'Data source unavailable'}</b><p>{error}</p></div>{authNeeded && authConfigured && <button className="text-button" onClick={() => document.getElementById('p02-username')?.focus()}>Sign in below</button>}</div>}
          {data?.source === 'synthetic demonstration data' && <div className="demo-notice"><span>i</span><p><b>Demonstration mode.</b> All purchase orders and receipts shown here are synthetic examples generated for this screen. No ERPNext or ART result is represented as live data.</p></div>}
          {data?.source === 'no validated data' && data.settings.mode === 'configured' && <div className="notice notice-info"><span>i</span><div><b>ART is configured, but no report is validated</b><p>Configuration presence does not verify connectivity or ERPNext retrieval. Start one controlled read-only run after confirming the agent and tools.</p></div></div>}

          {loading && !data ? <div className="loading-panel"><span className="spinner" /> Loading delivery workspace…</div> : null}
          {!loading && !data && authNeeded && <SignInForm username={username} password={password} setUsername={setUsername} setPassword={setPassword} onSubmit={signIn} busy={busy} error={authError} configured={authConfigured} />}
          {!loading && !data && !authNeeded && error && <div className="empty-panel"><div className="empty-icon">↻</div><h3>Workspace could not load</h3><p>Check the backend configuration and try again.</p><button className="secondary-button" onClick={() => void load()}>Try again</button></div>}

          {data && view === 'overview' && <Overview data={data} setView={setView} setFilter={setFilter} setSelectedOrder={setSelectedOrder} />}
          {data && view === 'orders' && <Orders orders={visibleOrders} search={search} setSearch={setSearch} filter={filter} setFilter={setFilter} onSelect={(id: string) => setSelectedOrder(id)} />}
          {data && view === 'exceptions' && <Exceptions exceptions={data.exceptions} onSelect={(id: string) => { setSelectedOrder(id); setView('orders'); }} />}
          {data && view === 'runs' && <Runs data={data} onRun={startRun} busy={busy} authenticated={authenticated} onSignIn={() => setShowAuth(true)} onViewReport={() => setView('orders')} />}
          {data && view === 'workflow' && <Workflow stages={data.workflowStages} />}
          {data && view === 'configuration' && <Configuration settings={settings} setSettings={setSettings} save={saveConfiguration} busy={busy} authenticated={authenticated} configured={authConfigured} message={settingsMessage} onSignIn={() => setShowAuth(true)} integrations={data.integrations} />}

          <footer className="delivery-footer"><span>ART Investigation Lab · P02</span><span>Monitoring date {data?.monitoringDate ? fmtDate(data.monitoringDate) : '—'} · {data?.settings?.timezone || 'Timezone not configured'}</span></footer>
        </div>
      </main>

      {currentOrder && <OrderDrawer order={currentOrder} onClose={() => setSelectedOrder(null)} />}
      {showAuth && <div className="auth-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) setShowAuth(false); }}><div className="auth-dialog"><button className="auth-close icon-button" onClick={() => setShowAuth(false)} aria-label="Close sign-in">×</button><SignInForm username={username} password={password} setUsername={setUsername} setPassword={setPassword} onSubmit={signIn} busy={busy} error={authError} configured={authConfigured} /></div></div>}
    </div>
  );
}

function SignInForm({ username, password, setUsername, setPassword, onSubmit, busy, error, configured }: any) {
  if (!configured) return <div className="auth-card"><div className="auth-symbol">⌑</div><h2>Administrator access is not configured</h2><p>Set <code>P02_ADMIN_USERNAME</code>, <code>P02_ADMIN_PASSWORD</code>, and <code>P02_SESSION_SECRET</code> in the server environment to access live data, run monitoring, or change configuration.</p></div>;
  return <form className="auth-card" onSubmit={onSubmit}><div className="auth-symbol">⌑</div><h2>Administrator sign-in</h2><p>Sign in to access live procurement results and protected controls.</p><label>Username<input id="p02-username" autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} required maxLength={120} /></label><label>Password<input type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} required maxLength={256} /></label>{error && <div className="form-error">{error}</div>}<button className="primary-button" disabled={busy}>{busy ? 'Signing in…' : 'Sign in securely'}</button></form>;
}

function Overview({ data, setView, setFilter, setSelectedOrder }: any) {
  const metric = data.metrics;
  const cards = [
    { label: 'Active purchase orders', value: metric.totalOrders, tone: 'navy', key: 'all', icon: '▤' },
    { label: 'Overdue deliveries', value: metric.overdue, tone: 'red', key: 'overdue', icon: '↗' },
    { label: 'Due today', value: metric.dueToday, tone: 'amber', key: 'due_today', icon: '◷' },
    { label: `Upcoming · ${data.settings.upcomingDays} days`, value: metric.upcoming, tone: 'blue', key: 'upcoming', icon: '→' },
    { label: 'Verified completed deliveries', value: metric.received, tone: 'green', key: 'received', icon: '✓' },
    { label: 'Partially received deliveries', value: metric.partialReceipts, tone: 'purple', key: 'partial', icon: '◐' },
    { label: 'Needs verification', value: metric.needsVerification, tone: 'slate', key: 'needs_verification', icon: '?' },
  ];
  const latest = data.latestRun;
  return <>
    <section className="integration-strip"><div className="integration-copy"><span className="integration-icon">⌁</span><div><b>Integration readiness</b><small>{data.integrations.mode === 'demo' ? 'Synthetic demonstration data' : 'Configuration does not imply successful execution'}</small></div></div><div className="integration-checks">{[['Backend', data.integrations.backend], ['ART', data.integrations.readiness], ['ERPNext report', data.integrations.erpnext]].map(([name, state]: any) => <div key={name} className="integration-check"><span className={`health-dot ${state === 'available' || state === 'VALIDATED' ? 'good' : ''}`} /><span>{name}</span><b>{pretty(state)}</b></div>)}</div></section>
    {metric.needsVerification > 0 && <div className="notice notice-info"><span>ⓘ</span><div><b>Audit notice: {metric.needsVerification} order(s) require verification</b><p>Records lacking complete, exactly scoped receipt retrieval or exhausted pagination are excluded from verified delivery totals to prevent false receipt claims.</p></div><button className="text-button" onClick={() => { setFilter('needs_verification'); setView('orders'); }}>View unverified records <span>→</span></button></div>}
    <div className="metric-grid">{cards.map((item) => <button key={item.key} className={`metric-card metric-${item.tone}`} onClick={() => { setFilter(item.key); setView('orders'); }}><div className="metric-top"><span>{item.label}</span><span className="metric-icon">{item.icon}</span></div><strong>{item.value}</strong><small>{item.key === 'all' ? 'Submitted, active scope' : item.key === 'upcoming' ? `Next ${data.settings.upcomingDays} days` : 'Purchase orders'}</small></button>)}</div>
    <div className="overview-columns"><section className="panel"><div className="panel-heading"><div><h2>Priority delivery queue</h2><p>Items requiring buyer attention</p></div><button className="text-button" onClick={() => setView('exceptions')}>View all exceptions <span>→</span></button></div>{data.exceptions.length ? <div className="compact-list">{data.exceptions.slice(0, 5).map((item: any) => <button className="compact-row" key={item.id} onClick={() => { setSelectedOrder(item.orderId); }}><span className={`severity-dot severity-${item.severity.toLowerCase()}`} /><span className="compact-main"><b>{item.orderId}</b><small>{item.supplier} · {item.itemCode}</small></span><span className={`status-pill status-${item.status.toLowerCase()}`}>{pretty(item.status)}</span><span className="row-chevron">›</span></button>)}</div> : <div className="empty-inline">No open delivery exceptions in this scope.</div>}</section>
      <section className="panel run-summary"><div className="panel-heading"><div><h2>Monitoring activity</h2><p>Latest confirmed ART execution</p></div><span className={`run-status ${latest?.status ? `run-${latest.status.toLowerCase()}` : 'run-idle'}`}>{latest ? pretty(latest.status) : 'No run yet'}</span></div><div className="last-run-date">{fmtTime(latest?.finishedAt || latest?.startedAt)}</div><div className="run-source"><span className="health-dot" /> {latest ? 'ART agent result' : data.source}</div><div className="run-explainer">A queued request is not marked successful. Success requires a final ART response that passes the evidence contract.</div><button className="secondary-button full-button" onClick={() => setView('runs')}>Open automation run center</button></section></div>
    <div className="section-footnote"><span className="footnote-icon">i</span><span>Delivery status uses <b>{pretty(data.settings.dueDateBasis)}</b> as the applicable due date. The contractual schedule and supplier promise are shown separately. No date or quantity is inferred from missing evidence.</span></div>
  </>;
}

function Orders({ orders, search, setSearch, filter, setFilter, onSelect }: any) {
  return <section className="panel data-panel"><div className="panel-heading table-heading"><div><h2>Purchase orders</h2><p>Line-level commitments and receipt evidence</p></div><span className="result-count">{orders.length} orders</span></div><div className="table-tools"><label className="search-input"><span>⌕</span><input placeholder="Search PO, supplier or item code" value={search} onChange={(event) => setSearch(event.target.value)} aria-label="Search purchase orders" /></label><select value={filter} onChange={(event) => setFilter(event.target.value)} aria-label="Filter by delivery status"><option value="all">All delivery states</option><option value="overdue">Overdue</option><option value="due_today">Due today</option><option value="upcoming">Upcoming</option><option value="future_open_delivery">Future open</option><option value="received">Verified completed</option><option value="partial">Partially received</option><option value="needs_verification">Needs verification</option></select></div><div className="table-scroll"><table><thead><tr><th>Purchase order</th><th>Supplier</th><th>Item code &amp; row ID</th><th>Contractual date</th><th>Supplier promise</th><th>Ordered</th><th>Received</th><th>Outstanding</th><th>Delivery state</th><th /></tr></thead><tbody>{orders.map((order: any) => { const states = order.assessments || []; const primary = states.find((item: any) => item.deliveryStatus !== 'RECEIVED') || states[0]; return <tr key={order.id} onClick={() => onSelect(order.id)}><td><button type="button" className="order-code order-open" onClick={(event) => { event.stopPropagation(); onSelect(order.id); }}>{order.id}</button><small>{pretty(order.status)}</small></td><td>{order.supplier}</td><td><b>{primary?.itemCode || 'Unknown'}</b><small>{primary?.orderItemId || 'No row ID'}</small></td><td>{fmtDate(primary?.baselineDate)}</td><td>{fmtDate(primary?.promisedDate)}</td><td>{primary?.orderedQuantity ?? '—'}</td><td>{primary?.receivedQuantity == null ? 'Unverified' : primary.receivedQuantity}</td><td>{primary?.outstandingQuantity == null ? 'Unverified' : primary.outstandingQuantity}</td><td><span className={`status-pill status-${primary?.deliveryStatus?.toLowerCase() || 'needs_verification'}`}>{pretty(primary?.deliveryStatus)}</span>{primary?.partialReceipt && <small className="partial-label">Partial receipt</small>}</td><td><span className="row-chevron">›</span></td></tr>; })}</tbody></table>{orders.length === 0 && <div className="empty-inline">No purchase orders match this search.</div>}</div><div className="table-note"><span>ⓘ</span> Receipt totals are calculated only from submitted receipts linked by exact PO item row identifiers with exhausted pagination.</div></section>;
}

function Exceptions({ exceptions, onSelect }: any) {
  return <section className="panel data-panel"><div className="panel-heading table-heading"><div><h2>Delivery exceptions workbench</h2><p>Prioritized human review required · read-only</p></div><span className="result-count">{exceptions.length} open</span></div><div className="exception-list">{exceptions.map((item: any) => <article className="exception-card" key={item.id}><div className={`exception-priority priority-${item.severity.toLowerCase()}`} /><div className="exception-body"><div className="exception-header"><div><span className="order-code">{item.orderId}</span><span className="separator-dot">·</span><span>{item.supplier}</span></div><span className={`status-pill status-${item.status.toLowerCase()}`}>{pretty(item.status)}</span></div><div className="exception-item"><span><b>Item:</b> {item.itemCode} ({item.orderItemId || 'Row ID missing'})</span>{item.dueDate && <span>Due {fmtDate(item.dueDate)}</span>}</div><div className="exception-audit-block"><b>Detected:</b> <span>{item.detected || item.reason}</span></div><div className="exception-audit-block"><b>Supporting records:</b><ul>{(item.supportingRecords || [`Purchase Order: ${item.orderId}`]).map((rec: string, index: number) => <li key={index}>{rec}</li>)}</ul></div><div className="exception-audit-block"><b>Missing evidence:</b><ul>{(item.missingEvidence || [item.reason]).map((ev: string, index: number) => <li key={index}>{ev}</li>)}</ul></div><div className="next-step"><b>Manual verification needed:</b><span>{item.manualVerificationNeeded || item.suggestedNextStep}</span></div></div><button className="text-button exception-open" onClick={() => onSelect(item.orderId)}>Review order details <span>→</span></button></article>)}{exceptions.length === 0 && <div className="empty-inline">No delivery exceptions currently require review.</div>}</div><div className="table-note"><span>ⓘ</span> Automated action is prohibited. Review exceptions and contact suppliers or dock receivers manually.</div></section>;
}

function Runs({ data, onRun, busy, authenticated, onSignIn, onViewReport }: any) {
  const latest = data.latestRun;
  const isConfigured = data.settings.mode === 'configured';
  return <div className="run-layout"><section className="panel run-launch"><div className="run-launch-icon">▶</div><div><div className="eyebrow">READ-ONLY MONITORING</div><h2>Run supplier delivery monitoring</h2><p>The configured ART agent will retrieve live ERPNext purchase orders and receipts using its existing connector tools. Configuration presence alone does not establish connectivity. This action does not send supplier messages or write to ERPNext.</p></div><button className="primary-button" disabled={!isConfigured || !authenticated || busy} onClick={onRun}>{busy ? 'Monitoring in progress…' : 'Run monitoring now'}</button>{!isConfigured && <div className="blocked-message"><b>Demonstration mode</b><span>ART environment credentials and target agent ID are not configured. To enable live monitoring, provide the required server configuration variables.</span></div>}{isConfigured && !authenticated && <button className="text-button" onClick={onSignIn}>Sign in as administrator to authorize a run →</button>}</section><section className="panel active-run"><div className="panel-heading"><div><h2>Current run</h2><p>Final results are validated before success is recorded</p></div><span className={`run-status ${latest?.status ? `run-${latest.status.toLowerCase()}` : 'run-idle'}`}>{latest ? pretty(latest.status) : 'Idle'}</span></div>{latest ? <><div className="run-facts"><div><small>Run reference</small><b>{latest.id}</b></div><div><small>Execution mode</small><b>{data.settings.mode === 'configured' ? 'Live ART Agent' : 'Synthetic Demo'}</b></div><div><small>Started</small><b>{fmtTime(latest.startedAt)}</b></div><div><small>Finished</small><b>{fmtTime(latest.finishedAt)}</b></div></div>{latest.error && <div className="run-error"><b>Run failure:</b> {latest.error}</div>}{latest.status === 'SUCCEEDED' && <><div className="run-success">Final ART response passed the P02 report contract. {latest.result?.purchaseOrders?.length ?? 0} purchase orders verified.</div><button className="text-button report-link" onClick={onViewReport}>Review validated order report →</button></>}</> : <div className="empty-inline">No monitoring run has been requested.</div>}</section><section className="panel history-panel"><div className="panel-heading"><div><h2>Run history</h2><p>Latest executions, modes, and verified outcomes</p></div><span className="result-count">{data.runs.length} runs</span></div>{data.runs.length ? <div className="history-list">{data.runs.map((run: any) => <div className="history-row" key={run.id}><span className={`history-icon run-${run.status.toLowerCase()}`}>{run.status === 'SUCCEEDED' ? '✓' : run.status === 'FAILED' ? '!' : '◷'}</span><div><b>{run.id.slice(0, 8)}</b><small>{fmtTime(run.startedAt)} · {run.source === 'art' && data.settings.mode === 'configured' ? 'Live ART Execution' : 'Demo Execution'}</small></div><span className={`run-status run-${run.status.toLowerCase()}`}>{pretty(run.status)}</span><small>{run.finishedAt ? `${Math.max(0, Math.round((Date.parse(run.finishedAt) - Date.parse(run.startedAt)) / 1000))} sec` : 'In progress'}</small></div>)}</div> : <div className="empty-inline">Run history appears here after a run request. History is saved by the server.</div>}</section></div>;
}

function Workflow({ stages }: any) {
  return <div className="workflow-view"><div className="workflow-intro"><div className="eyebrow">SPECIFICATION VS. IMPLEMENTATION</div><h2>Six stages from acknowledgment to dock handoff</h2><p>The P02 workflow is a proposed operating model. Stage labels reflect repository evidence and this application’s current capabilities.</p><div className="state-legend">{['SPECIFIED', 'IMPLEMENTED', 'TESTED', 'PARTIALLY VALIDATED', 'OPERATIONAL'].map((state) => <span key={state} className={`stage-badge stage-${state.toLowerCase().replaceAll(' ', '-')}`}>{state}</span>)}</div></div><div className="workflow-stages">{stages.map((stage: any, index: number) => <article className="stage-card" key={stage.id}><div className="stage-number">{String(index + 1).padStart(2, '0')}</div><div className="stage-content"><div className="stage-title"><h3>{stage.name}</h3><span className={`stage-badge stage-${stage.state.toLowerCase().replaceAll(' ', '-')}`}>{stage.state}</span></div><p>{stage.detail}</p><div className="stage-evidence"><span>Source</span><b>workflow.md · WF-P02-00{index + 1}</b><span>Evidence</span><b>{stage.state === 'PARTIALLY VALIDATED' ? 'P02 normalized report (live response required)' : 'Specification only'}</b></div></div></article>)}</div><div className="section-footnote"><span className="footnote-icon">i</span><span>Human review remains required for delay, partial receipt, missing or conflicting dates, and any consequential supplier action. Supplier communication and ERPNext writes are not enabled.</span></div></div>;
}

function Configuration({ settings, setSettings, save, busy, authenticated, configured, message, onSignIn, integrations }: any) {
  return <div className="config-grid"><section className="panel config-form"><div className="panel-heading"><div><h2>Monitoring scope</h2><p>Classification and reporting preferences</p></div></div>{!authenticated ? <div className="config-locked"><div className="lock-symbol">⌑</div><b>Administrator access required</b><p>Sign in to change configuration. Values are stored server-side.</p>{configured && <button className="secondary-button" onClick={onSignIn}>Sign in</button>}{!configured && <small>Set P02 admin environment variables to enable protected settings.</small>}</div> : <form onSubmit={save}><label>Upcoming delivery window<select value={settings.upcomingDays} onChange={(event) => setSettings({ ...settings, upcomingDays: Number(event.target.value) })}><option value={3}>Next 3 days</option><option value={7}>Next 7 days</option><option value={14}>Next 14 days</option><option value={30}>Next 30 days</option></select></label><label>Applicable due date<select value={settings.dueDateBasis} onChange={(event) => setSettings({ ...settings, dueDateBasis: event.target.value })}><option value="contractual">Contractual item schedule date</option><option value="supplier_promise">Supplier promised date</option></select><small>Changing this setting changes which open orders are reported overdue. Both dates remain visible.</small></label><label>Business timezone<input value={settings.timezone} onChange={(event) => setSettings({ ...settings, timezone: event.target.value })} maxLength={100} placeholder="Asia/Kolkata" /><small>Use an IANA timezone, for example Asia/Kolkata.</small></label><button className="primary-button" disabled={busy}>Save settings</button>{message && <div className={message.includes('saved') ? 'form-success' : 'form-error'}>{message}</div>}</form>}</section><section className="panel config-health"><div className="panel-heading"><div><h2>Integration status</h2><p>Server-side configuration overview</p></div></div>{[['Backend', integrations.backend], ['ART readiness', integrations.readiness], ['ERPNext report', integrations.erpnext]].map(([label, state]: any) => <div className="config-status-row" key={label}><span className={`health-dot ${state === 'available' || state === 'VALIDATED' ? 'good' : ''}`} /><span>{label}</span><b>{pretty(state)}</b></div>)}<div className="config-callout"><b>Credentials stay on the server</b><p>ART Client Secret and ERPNext credentials are never requested or sent by this browser. Configure ART through the server environment and the existing agent tools.</p></div><div className="config-callout"><b>Scheduling</b><p>No recurring scheduler is configured. Runs can only be started manually after a verified ART agent connection is available.</p></div></section></div>;
}

function OrderDrawer({ order, onClose }: any) {
  return <div className="drawer-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}><section className="order-drawer" role="dialog" aria-modal="true" aria-labelledby="order-drawer-title"><div className="drawer-head"><div><div className="eyebrow">PURCHASE ORDER</div><h2 id="order-drawer-title">{order.id}</h2><p>{order.supplier}</p></div><button className="icon-button" onClick={onClose} aria-label="Close order details">×</button></div><div className="drawer-body"><div className="detail-pair"><span>ERPNext status</span><b>{pretty(order.status)}</b></div><div className="detail-pair"><span>Order date</span><b>{fmtDate(order.transactionDate)}</b></div>{order.items.map((item: any) => { const assessment = order.assessments?.find((entry: any) => entry.orderItemId === item.id); const retrieval = item.receiptRetrieval; return <div className="drawer-item" key={item.id}><div className="drawer-item-head"><div><b>{item.itemCode || 'Item code missing'}</b><small className="item-row-id">PO Row ID: {item.id || 'Missing'}</small></div><span className={`status-pill status-${assessment?.deliveryStatus.toLowerCase()}`}>{pretty(assessment?.deliveryStatus)}</span></div>{item.description && <p className="item-desc">{item.description}</p>}<div className="quantity-grid"><div><small>Ordered</small><b>{assessment?.orderedQuantity ?? 'Unverified'}</b></div><div><small>Verified received</small><b>{assessment?.receivedQuantity ?? 'Unverified'}</b></div><div><small>Outstanding</small><b>{assessment?.outstandingQuantity ?? 'Unverified'}</b></div></div><div className="detail-pair"><span>Contractual item date</span><b>{fmtDate(assessment?.baselineDate)}</b></div><div className="detail-pair"><span>Supplier promised date</span><b>{fmtDate(assessment?.promisedDate)}</b></div><div className="detail-pair"><span>Applicable due date</span><b>{fmtDate(assessment?.applicableDueDate)}</b></div><div className="evidence-block"><b>Receipt evidence review</b>{assessment?.receiptEvidence?.length ? assessment.receiptEvidence.map((receipt: any) => <div className="receipt-row-card" key={receipt.receiptItemId}><div className="receipt-row-header"><span className="receipt-id"><b>{receipt.receiptId}</b> (Row: {receipt.receiptItemId})</span><span className="receipt-match-tag">Exact Link Verified</span></div><div className="receipt-row-details"><span>Linked PO: <b>{receipt.purchaseOrderId}</b> · Row: <b>{receipt.purchaseOrderItemId}</b></span><span>Qty: <b>{receipt.quantity}</b> {receipt.isReturn ? '(Return Deduction)' : ''} · Status: <b>Submitted (docstatus: {receipt.docstatus})</b></span></div></div>) : <small className="no-receipt-note">No exact-linked submitted receipt records found.</small>}</div><div className="retrieval-audit-block"><b>Receipt retrieval audit trail</b><div className="audit-detail-grid"><div><small>Retrieval scope</small><b>{retrieval?.scope?.purchaseOrderId ? `PO ${retrieval.scope.purchaseOrderId} / Row ${retrieval.scope.purchaseOrderItemId}` : 'No scope evidence'}</b></div><div><small>Pagination status</small><b>{retrieval?.pagesRetrieved != null ? `${retrieval.pagesRetrieved} page(s), ${retrieval.hasMore === false ? 'Exhausted' : 'Has more pages'}` : 'Unevidenced'}</b></div><div><small>Completeness claimed</small><b>{retrieval?.complete ? 'Complete' : 'Incomplete'}</b></div><div><small>Source tool / Response</small><b>{retrieval?.sourceToolId || 'N/A'} / {retrieval?.sourceResponseId || 'N/A'}</b></div></div></div>{assessment?.verificationReasons?.length > 0 && <div className="verification-block"><b>Verification required</b><ul>{assessment.verificationReasons.map((reason: string) => <li key={reason}>{reason}</li>)}</ul></div>}</div>; })}</div><div className="drawer-foot"><span>Read-only · No ERPNext changes are made</span><button className="secondary-button" onClick={onClose}>Close details</button></div></section></div>;
}
