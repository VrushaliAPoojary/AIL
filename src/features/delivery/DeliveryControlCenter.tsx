'use client';

import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react';
import './DeliveryControlCenter.css';

import { DeliveryHeader } from './components/DeliveryHeader';
import { DeliverySidebar, ViewId } from './components/DeliverySidebar';
import { OverviewView } from './components/OverviewView';
import { OrdersView } from './components/OrdersView';
import { OrderDrawer } from './components/OrderDrawer';
import { ExceptionsView } from './components/ExceptionsView';
import { RunsView } from './components/RunsView';
import { WorkflowView } from './components/WorkflowView';
import { ConfigurationView } from './components/ConfigurationView';
import { AuthModal } from './components/AuthModal';
import { IconAlertTriangle, IconRefresh } from './components/Icons';

type CenterData = any;

const VIEW_TITLES: Record<ViewId, string> = {
  overview: 'Mission Overview',
  orders: 'Purchase Orders',
  exceptions: 'Delivery Exceptions',
  runs: 'Automation Run Center',
  workflow: 'Workflow & Evidence',
  configuration: 'System Configuration',
};

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
  const [sidebarOpenMobile, setSidebarOpenMobile] = useState(false);

  const load = useCallback(async (quiet = false) => {
    if (!quiet) setLoading(true);
    setError('');
    try {
      const response = await fetch('/api/delivery/data', { cache: 'no-store' });
      const result = await response.json();
      if (response.status === 401) {
        setAuthNeeded(true);
        setData(null);
        setError(result.error || 'Sign in as administrator to view live procurement data.');
      } else if (!response.ok) {
        throw new Error(result.error || 'Delivery workspace data could not be loaded.');
      } else {
        setData(result);
        setAuthNeeded(false);
        setSettings({
          upcomingDays: result.settings.upcomingDays,
          dueDateBasis: result.settings.dueDateBasis,
          timezone: result.settings.timezone,
        });
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Delivery data could not be loaded.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetch('/api/delivery/session')
      .then((response) => response.json())
      .then((result) => {
        setAuthConfigured(Boolean(result.configured));
        setAuthenticated(Boolean(result.authenticated));
      })
      .catch(() => undefined);
    void load();
  }, [load]);

  useEffect(() => {
    if (!data?.runs?.some((run: any) => run.status === 'QUEUED' || run.status === 'RUNNING')) return;
    const timer = window.setInterval(() => void load(true), 2500);
    return () => window.clearInterval(timer);
  }, [data?.runs, load]);

  const orders = data?.purchaseOrders || [];
  const visibleOrders = useMemo(() => {
    return orders.filter((order: any) => {
      const text = `${order.id} ${order.supplier} ${order.items
        .map((item: any) => item.itemCode)
        .join(' ')}`.toLowerCase();
      const assessments = order.assessments || [];
      const status =
        filter === 'all' ||
        (filter === 'received'
          ? assessments.length > 0 &&
            assessments.every((item: any) => item.deliveryStatus === 'RECEIVED')
          : assessments.some(
              (item: any) =>
                item.deliveryStatus.toLowerCase() === filter ||
                (filter === 'partial' && item.partialReceipt)
            ));
      return text.includes(search.trim().toLowerCase()) && status;
    });
  }, [orders, search, filter]);

  const currentOrder = orders.find((order: any) => order.id === selectedOrder) || null;
  const isRunActive = Boolean(
    data?.runs?.some((run: any) => run.status === 'QUEUED' || run.status === 'RUNNING')
  );

  async function signIn(event: FormEvent) {
    event.preventDefault();
    setAuthError('');
    setBusy(true);
    try {
      const response = await fetch('/api/delivery/session', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || 'Authentication failed.');
      setAuthenticated(true);
      setAuthNeeded(false);
      setShowAuth(false);
      setPassword('');
      await load();
    } catch (cause) {
      setAuthError(cause instanceof Error ? cause.message : 'Sign-in failed.');
    } finally {
      setBusy(false);
    }
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
      const idempotencyKey =
        typeof crypto !== 'undefined' && 'randomUUID' in crypto
          ? crypto.randomUUID()
          : `${Date.now()}-${Math.random()}`;
      const response = await fetch('/api/delivery/runs', {
        method: 'POST',
        headers: { 'Idempotency-Key': idempotencyKey },
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || 'Unable to initiate the ART monitoring run.');
      setView('runs');
      await load(true);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Unable to start monitoring run.');
    } finally {
      setBusy(false);
    }
  }

  async function saveConfiguration(event: FormEvent) {
    event.preventDefault();
    setSettingsMessage('');
    setBusy(true);
    try {
      const response = await fetch('/api/delivery/config', {
        method: 'PUT',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify(settings),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || 'Configuration could not be saved.');
      setSettingsMessage('Configuration successfully saved to server.');
      await load(true);
    } catch (cause) {
      setSettingsMessage(cause instanceof Error ? cause.message : 'Configuration update failed.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="delivery-app-shell">
      {/* Sidebar Navigation */}
      <DeliverySidebar
        currentView={view}
        onSelectView={(v) => {
          setView(v);
          setSidebarOpenMobile(false);
        }}
        ordersCount={orders.length}
        exceptionsCount={data?.exceptions?.length || 0}
        needsVerificationCount={data?.metrics?.needsVerification || 0}
        activeRun={isRunActive}
        isOpenMobile={sidebarOpenMobile}
        onCloseMobile={() => setSidebarOpenMobile(false)}
      />

      {/* Main App Content Area */}
      <div className="delivery-main-wrapper">
        <DeliveryHeader
          currentViewLabel={VIEW_TITLES[view]}
          source={data?.source}
          mode={data?.settings?.mode}
          readiness={data?.integrations?.readiness}
          monitoringDate={data?.monitoringDate}
          timezone={data?.settings?.timezone}
          authenticated={authenticated}
          authConfigured={authConfigured}
          loading={loading}
          onRefresh={() => void load()}
          onSignOut={signOut}
          onSignInClick={() => setShowAuth(true)}
          onToggleSidebar={() => setSidebarOpenMobile(!sidebarOpenMobile)}
        />

        <main className="delivery-view-viewport">
          {/* Global Error Banner */}
          {error && (
            <div className="delivery-error-banner" role="alert">
              <IconAlertTriangle size={20} className="banner-alert-icon" />
              <div className="banner-text">
                <strong>{authNeeded ? 'Authentication Required' : 'Data Source Notice'}</strong>
                <p>{error}</p>
              </div>
              {authNeeded && authConfigured && (
                <button
                  type="button"
                  className="banner-action-btn"
                  onClick={() => setShowAuth(true)}
                >
                  Sign in as Admin
                </button>
              )}
            </div>
          )}

          {/* Initial Loading State */}
          {loading && !data && (
            <div className="delivery-initial-loading">
              <div className="loading-spinner-ring" />
              <h3>Loading Delivery Control Center…</h3>
              <p>Normalizing ERPNext purchase orders and receipt evidence contracts.</p>
            </div>
          )}

          {/* Fallback Unauthenticated View when data is null and auth is required */}
          {!loading && !data && authNeeded && (
            <div className="auth-required-standalone">
              <div className="standalone-auth-wrapper">
                <AuthModal
                  username={username}
                  password={password}
                  setUsername={setUsername}
                  setPassword={setPassword}
                  onSubmit={signIn}
                  onClose={() => undefined}
                  busy={busy}
                  error={authError}
                  configured={authConfigured}
                />
              </div>
            </div>
          )}

          {/* Fallback Error View when data failed to load */}
          {!loading && !data && !authNeeded && error && (
            <div className="delivery-fatal-error">
              <IconAlertTriangle size={36} className="fatal-icon" />
              <h3>Workspace Could Not Be Loaded</h3>
              <p>{error}</p>
              <button
                type="button"
                className="retry-load-btn"
                onClick={() => void load()}
              >
                <IconRefresh size={16} />
                <span>Retry Connection</span>
              </button>
            </div>
          )}

          {/* Dynamic Views */}
          {data && view === 'overview' && (
            <OverviewView
              data={data}
              setView={(v) => setView(v as ViewId)}
              setFilter={setFilter}
              setSelectedOrder={setSelectedOrder}
            />
          )}

          {data && view === 'orders' && (
            <OrdersView
              orders={visibleOrders}
              search={search}
              setSearch={setSearch}
              filter={filter}
              setFilter={setFilter}
              onSelect={(id) => setSelectedOrder(id)}
            />
          )}

          {data && view === 'exceptions' && (
            <ExceptionsView
              exceptions={data.exceptions || []}
              onSelect={(id) => {
                setSelectedOrder(id);
                setView('orders');
              }}
            />
          )}

          {data && view === 'runs' && (
            <RunsView
              data={data}
              onRun={startRun}
              busy={busy}
              authenticated={authenticated}
              onSignIn={() => setShowAuth(true)}
              onViewReport={() => setView('orders')}
            />
          )}

          {data && view === 'workflow' && (
            <WorkflowView stages={data.workflowStages || []} />
          )}

          {data && view === 'configuration' && (
            <ConfigurationView
              settings={settings}
              setSettings={setSettings}
              save={saveConfiguration}
              busy={busy}
              authenticated={authenticated}
              configured={authConfigured}
              message={settingsMessage}
              onSignIn={() => setShowAuth(true)}
              integrations={data.integrations || {}}
            />
          )}
        </main>

        {/* Global Footer */}
        <footer className="delivery-global-footer">
          <div className="footer-left">
            <strong>P02 Supplier Delivery Control Center</strong>
            <span className="footer-sep">·</span>
            <span>ART Investigation Lab</span>
            <span className="footer-sep">·</span>
            <span>Read-Only Integration Architecture</span>
          </div>
          <div className="footer-right">
            <span>
              Monitoring Business Date: <strong>{data?.monitoringDate || '—'}</strong>
            </span>
            <span className="footer-sep">·</span>
            <span>Timezone: <strong>{data?.settings?.timezone || 'Asia/Kolkata'}</strong></span>
          </div>
        </footer>
      </div>

      {/* Order Detail Sliding Drawer */}
      {currentOrder && (
        <OrderDrawer
          order={currentOrder}
          onClose={() => setSelectedOrder(null)}
        />
      )}

      {/* Administrator Authentication Modal */}
      {showAuth && (
        <AuthModal
          username={username}
          password={password}
          setUsername={setUsername}
          setPassword={setPassword}
          onSubmit={signIn}
          onClose={() => setShowAuth(false)}
          busy={busy}
          error={authError}
          configured={authConfigured}
        />
      )}
    </div>
  );
}
