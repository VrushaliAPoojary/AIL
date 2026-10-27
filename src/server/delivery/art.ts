import 'server-only';
import type { RunRecord } from './types';
import { executeAgentRun, sanitizeArtUri } from './adkExecution';
import { normalizeAgentReport } from './artContract';
import { setIntegrationReadiness, type IntegrationFailureCode } from './readiness';

const RUN_TIMEOUT_MS = 120_000;

function integrationConfig() {
  const values = {
    Uri: process.env.ART_URI,
    ClientID: process.env.ART_CLIENT_ID,
    ClientSecret: process.env.ART_CLIENT_SECRET,
    OrgTitle: process.env.ART_ORG_TITLE,
    Environment: process.env.ART_ENVIRONMENT,
    ProjectKey: process.env.ART_PROJECT_KEY,
    agentId: process.env.ART_AGENT_ID,
  };
  if (Object.values(values).some((value) => !value || !value.trim())) return null;
  return {
    Uri: values.Uri!.trim(),
    ClientID: values.ClientID!.trim(),
    ClientSecret: values.ClientSecret!.trim(),
    OrgTitle: values.OrgTitle!.trim(),
    Environment: values.Environment!.trim(),
    ProjectKey: values.ProjectKey!.trim(),
    agentId: values.agentId!.trim(),
  };
}

export { sanitizeArtUri };

export async function executeArtMonitoring(run: RunRecord): Promise<unknown> {
  const config = integrationConfig();
  if (!config) throw new Error('ART execution is unavailable: required server-side ART connection and agent settings are missing.');
  let adk: any;
  let phase: 'connection' | 'run' | 'report' = 'connection';
  setIntegrationReadiness('CONNECTING');
  try {
    const { default: Adk } = await import('@arealtimetech/adk-js');
    adk = new (Adk as any)({ Uri: sanitizeArtUri(config.Uri) });
    adk.setCredentials({
      ClientID: config.ClientID,
      ClientSecret: config.ClientSecret,
      OrgTitle: config.OrgTitle,
      Environment: config.Environment,
      ProjectKey: config.ProjectKey,
    });
    adk.connect();
    const result = await executeAgentRun(adk, config.agentId, [
      'Run the configured P02 supplier delivery monitoring workflow using only its existing read-only ERPNext tools.',
      'Do not send supplier messages, modify ERPNext, create documents, or infer missing values.',
      `Run reference: ${run.id}.`,
      'When querying List Stock Ledger Entry - Erp, if using order_by, format it strictly as a single field with lowercase direction matching ^[a-zA-Z0-9_]+ (asc|desc)$ (e.g. "posting_date desc" or "creation desc"). Do not use multiple comma-separated fields, table prefixes, or uppercase DESC.',
      'From Get Purchase Order - Erp, extract PO name/id, supplier, transaction_date, docstatus, status, and nested item rows with item_code, qty (orderedQuantity), received_qty, item-level schedule_date, expected_delivery_date, uom, and warehouse.',
      'From Get Purchase Receipt - Erp / List Purchase Receipts, extract receipt item name, parent (receiptId), purchase_order, purchase_order_item, item_code, qty, and docstatus. Only link receipts with exact purchase_order and purchase_order_item matching the PO item. Do not infer matches from supplier or item code alone.',
      'Return one JSON object with a purchaseOrders array. Each PO has id, supplier, transactionDate, docstatus, status, and items. Each item has id (ERPNext PO item row id), itemCode, description, orderedQuantity, receivedQuantity, scheduleDate, expectedDeliveryDate, uom, warehouse, receiptRetrieval, and receipts. Each receipt includes receiptId, receiptItemId, purchaseOrderId, purchaseOrderItemId (ERPNext PO item row id from the receipt link field), quantity, docstatus, and isReturn. Include only receipts with exact source linkage. For receiptRetrieval, report the exact purchase-order and PO-item retrieval scope, source tool/response identifiers if the tool output provides them, whether retrieval is complete, pages retrieved, and whether another page exists. Do not invent pagination or source metadata. Use null for any completeness or pagination fact not established by tool output; incomplete or unavailable retrieval evidence must not be represented as complete. Use null for missing dates or quantities. Do not calculate status or claim full receipt or overdue status.',
    ].join('\n'), RUN_TIMEOUT_MS, () => { phase = 'run'; setIntegrationReadiness('CONNECTED'); });
    phase = 'report';
    const report = normalizeAgentReport(result);
    setIntegrationReadiness('VALIDATED');
    return report;
  } catch (error) {
    const failure: IntegrationFailureCode = phase === 'connection' ? 'CONNECTION_FAILED' : phase === 'report' ? 'REPORT_INVALID' : 'RUN_FAILED';
    setIntegrationReadiness('FAILED', failure);
    const detail = error instanceof Error ? error.message : String(error);
    const baseMessage = failure === 'CONNECTION_FAILED'
      ? 'ART connection failed. Check server-side configuration and ART availability.'
      : failure === 'REPORT_INVALID'
        ? 'ART returned a report that did not pass P02 validation.'
        : 'ART monitoring run failed. Check the server-side integration logs.';
    console.error(`[ART Execution Error - ${failure}]:`, detail);
    throw new Error(detail ? `${baseMessage} (${detail})` : baseMessage);
  } finally {
    if (adk) {
      try { await adk.disconnect(); } catch { /* Do not expose SDK disconnect details to clients. */ }
    }
  }
}
