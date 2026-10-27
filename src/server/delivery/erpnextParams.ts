/**
 * Parameter validation for ERPNext / Frappe tool integration in P02.
 * Registered Frappe tool schemas enforce strict regex patterns on query parameters.
 */

/**
 * Allowed regex pattern for the order_by parameter in Frappe list tools
 * such as 'List Stock Ledger Entry - Erp'.
 * Standard registered contract: ^[a-zA-Z0-9_]+ (asc|desc)$
 */
export const STOCK_LEDGER_ORDER_BY_PATTERN = /^[a-zA-Z0-9_]+ (asc|desc)$/;

/**
 * Validates whether an order_by parameter string conforms to the tool's registered contract.
 * Rejects multi-column sort expressions (e.g. 'posting_date desc, posting_time desc'),
 * table-prefixed fields (e.g. 'tabStock Ledger Entry.posting_date desc'),
 * uppercase sort directions (e.g. 'DESC'), and empty or non-string inputs.
 */
export function validateStockLedgerOrderBy(orderBy: unknown): boolean {
  if (typeof orderBy !== 'string') return false;
  return STOCK_LEDGER_ORDER_BY_PATTERN.test(orderBy.trim());
}

/**
 * Returns a valid, safe order_by parameter string.
 * Defaults to 'posting_date desc' if missing or invalid.
 */
export function sanitizeStockLedgerOrderBy(orderBy?: string | null): string {
  if (typeof orderBy === 'string' && STOCK_LEDGER_ORDER_BY_PATTERN.test(orderBy.trim())) {
    return orderBy.trim();
  }
  return 'posting_date desc';
}
