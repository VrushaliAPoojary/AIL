import React from 'react';
import { IconSearch, IconFilter, IconChevronRight, IconInfo, IconBox } from './Icons';
import { DeliveryStatusBadge } from './StatusBadges';

interface OrdersViewProps {
  orders: any[];
  search: string;
  setSearch: (value: string) => void;
  filter: string;
  setFilter: (value: string) => void;
  onSelect: (orderId: string) => void;
}

const fmtDate = (value?: string | null) =>
  value
    ? new Date(`${value.slice(0, 10)}T00:00:00`).toLocaleDateString('en-IN', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      })
    : '—';

const pretty = (val?: string) =>
  val
    ? val
        .replaceAll('_', ' ')
        .toLowerCase()
        .replace(/\b\w/g, (c) => c.toUpperCase())
    : 'Unknown';

export function OrdersView({
  orders,
  search,
  setSearch,
  filter,
  setFilter,
  onSelect,
}: OrdersViewProps) {
  const filterTabs = [
    { id: 'all', label: 'All Orders' },
    { id: 'overdue', label: 'Overdue' },
    { id: 'due_today', label: 'Due Today' },
    { id: 'upcoming', label: 'Upcoming' },
    { id: 'future_open_delivery', label: 'Future Open' },
    { id: 'received', label: 'Verified Completed' },
    { id: 'partial', label: 'Partially Received' },
    { id: 'needs_verification', label: 'Needs Verification' },
  ];

  return (
    <section className="orders-workbench-panel" aria-labelledby="orders-title">
      <div className="workbench-top-bar">
        <div>
          <h2 id="orders-title" className="workbench-heading">
            Purchase Orders &amp; Delivery Commitments
          </h2>
          <p className="workbench-subheading">
            Line-level schedule verification and exact-linked Purchase Receipt audit
          </p>
        </div>
        <div className="orders-count-badge">
          <strong>{orders.length}</strong> {orders.length === 1 ? 'order' : 'orders'} matching
        </div>
      </div>

      {/* Filter Tabs Bar */}
      <div className="filter-tabs-row" role="tablist" aria-label="Filter orders by delivery state">
        {filterTabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={filter === tab.id}
            className={`filter-tab-btn ${filter === tab.id ? 'is-active' : ''}`}
            onClick={() => setFilter(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Search and Secondary Filter Row */}
      <div className="table-controls-bar">
        <div className="search-box">
          <IconSearch size={16} className="search-icon" />
          <input
            type="text"
            placeholder="Search by Purchase Order ID, supplier name, or item code…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            aria-label="Search purchase orders"
          />
          {search && (
            <button
              type="button"
              className="clear-search-btn"
              onClick={() => setSearch('')}
              aria-label="Clear search"
            >
              ×
            </button>
          )}
        </div>

        <div className="filter-select-wrapper">
          <IconFilter size={15} className="select-icon" />
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            aria-label="Filter orders by status"
          >
            <option value="all">All Delivery States</option>
            <option value="overdue">Overdue Deliveries</option>
            <option value="due_today">Due Today</option>
            <option value="upcoming">Upcoming</option>
            <option value="future_open_delivery">Future Open</option>
            <option value="received">Verified Completed</option>
            <option value="partial">Partially Received</option>
            <option value="needs_verification">Needs Verification</option>
          </select>
        </div>
      </div>

      {/* Table Container */}
      <div className="table-scroll-container">
        <table className="orders-table">
          <thead>
            <tr>
              <th scope="col" className="col-po">Purchase Order</th>
              <th scope="col" className="col-supplier">Supplier</th>
              <th scope="col" className="col-item">Item &amp; Row ID</th>
              <th scope="col" className="col-date">Contractual Date</th>
              <th scope="col" className="col-date">Supplier Promise</th>
              <th scope="col" className="col-qty text-right">Ordered</th>
              <th scope="col" className="col-qty text-right">Received</th>
              <th scope="col" className="col-qty text-right">Outstanding</th>
              <th scope="col" className="col-status">Delivery State</th>
              <th scope="col" className="col-action text-center">Inspect</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((order) => {
              const assessments = order.assessments || [];
              const primary =
                assessments.find((item: any) => item.deliveryStatus !== 'RECEIVED') ||
                assessments[0];

              return (
                <tr
                  key={order.id}
                  className="order-table-row"
                  onClick={() => onSelect(order.id)}
                >
                  <td className="col-po">
                    <span className="po-code-text monospace">{order.id}</span>
                    <span className="po-docstatus-tag">{pretty(order.status)}</span>
                  </td>
                  <td className="col-supplier">
                    <strong className="supplier-name-text">{order.supplier}</strong>
                  </td>
                  <td className="col-item">
                    <div className="item-cell-wrapper">
                      <strong className="item-code-text">
                        {primary?.itemCode || 'Unknown item'}
                      </strong>
                      <span className="item-row-tag monospace">
                        Row: {primary?.orderItemId || 'N/A'}
                      </span>
                    </div>
                  </td>
                  <td className="col-date">
                    <span className="date-cell-text">{fmtDate(primary?.baselineDate)}</span>
                  </td>
                  <td className="col-date">
                    <span className="date-cell-text">{fmtDate(primary?.promisedDate)}</span>
                  </td>
                  <td className="col-qty text-right">
                    <span className="qty-val">{primary?.orderedQuantity ?? '—'}</span>
                  </td>
                  <td className="col-qty text-right">
                    {primary?.receivedQuantity == null ? (
                      <span className="qty-unverified">Unverified</span>
                    ) : (
                      <strong className="qty-val qty-received">{primary.receivedQuantity}</strong>
                    )}
                  </td>
                  <td className="col-qty text-right">
                    {primary?.outstandingQuantity == null ? (
                      <span className="qty-unverified">Unverified</span>
                    ) : (
                      <span
                        className={`qty-val ${
                          primary.outstandingQuantity > 0 ? 'qty-open' : 'qty-zero'
                        }`}
                      >
                        {primary.outstandingQuantity}
                      </span>
                    )}
                  </td>
                  <td className="col-status">
                    <DeliveryStatusBadge
                      status={primary?.deliveryStatus}
                      partialReceipt={primary?.partialReceipt}
                      size="sm"
                    />
                  </td>
                  <td className="col-action text-center">
                    <button
                      type="button"
                      className="table-inspect-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelect(order.id);
                      }}
                      title={`Inspect order details for ${order.id}`}
                      aria-label={`Inspect ${order.id}`}
                    >
                      <span>View</span>
                      <IconChevronRight size={14} />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>

        {orders.length === 0 && (
          <div className="table-empty-state">
            <IconBox size={36} className="empty-table-icon" />
            <h3>No purchase orders found</h3>
            <p>
              {search
                ? `No orders matching "${search}" in this delivery filter.`
                : 'No purchase orders match the selected delivery filter.'}
            </p>
            {(search || filter !== 'all') && (
              <button
                type="button"
                className="reset-filter-btn"
                onClick={() => {
                  setSearch('');
                  setFilter('all');
                }}
              >
                Reset Filters
              </button>
            )}
          </div>
        )}
      </div>

      <div className="table-footer-note">
        <IconInfo size={15} className="note-icon" />
        <span>
          <strong>Audit Principle:</strong> Receipt quantities are computed strictly from submitted Purchase Receipts (<code>docstatus: 1</code>) that have exact PO number and line-item row ID matches. Pagination completeness must be confirmed before quantities are credited.
        </span>
      </div>
    </section>
  );
}
