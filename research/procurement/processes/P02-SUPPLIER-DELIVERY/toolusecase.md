# P02 ERPNext Lookup Tools Overview

These 10 tools are intended to help a buyer **find purchase orders, inspect supplier and receipt records, and review dates and quantities stored in ERPNext**. They are lookup tools; they do not read supplier emails or change ERPNext records.

| #  | Tool                                          | What it does                                                                                                                                                                                    |
| -- | --------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1  | **List Purchase Orders**                | Returns a limited list of POs, with summary information such as supplier, status, transaction date, and header schedule date. Use it to find an order when you don’t know its exact PO number. |
| 2  | **List Purchase Orders by Supplier**    | Returns a limited list of POs for a specified supplier. Use it when you know the supplier but want to find their orders.                                                                        |
| 3  | **List Submitted Purchase Orders**      | Returns a limited list of submitted POs. “Submitted” does**not** necessarily mean the PO still has items awaiting receipt; check its status and item quantities.                        |
| 4  | **List Purchase Orders Due by Date**    | Lists submitted POs whose**header-level** schedule date is on or before the date you provide. It does not filter by item-level delivery dates.                                            |
| 5  | **Get Purchase Order**                  | Retrieves the full PO using its exact ERPNext document name. Use it to inspect supplier, items, ordered and received quantities, and header- and item-level dates.                              |
| 6  | **Get Supplier**                        | Retrieves a supplier’s ERPNext record, such as supplier type and other available master data. It does not show what the supplier promised to deliver.                                          |
| 7  | **Get Item**                            | Retrieves an Item master record by its exact item code. It provides item information but**does not search for POs containing that item**.                                                 |
| 8  | **List Purchase Receipts**              | Returns a limited list of recorded Purchase Receipts. This can help locate receipt records, but the list may not include the full history.                                                      |
| 9  | **List Submitted Receipts by Supplier** | Returns a limited list of submitted Purchase Receipts for a particular supplier. These are ERPNext records of goods received, not supplier delivery promises.                                   |
| 10 | **Get Purchase Receipt**                | Retrieves a specific receipt by its exact name, including available item details and PO references. You need a real receipt name first, usually from a receipt list.                            |

## Example: how they work together

A buyer might ask, “What orders do we have for P02 Test Supplier?”

1. **List Purchase Orders by Supplier** finds matching POs.
2. **Get Purchase Order** retrieves the exact order selected by the buyer, with item quantities and dates.
3. **Get Supplier** retrieves supplier-record details if useful.
4. If checking what has already been received, **List Submitted Receipts by Supplier** finds receipt records, and **Get Purchase Receipt** provides details for a specific receipt.
5. The agent summarizes the ERPNext information and flags anything the buyer may want to review.

## Important limitations

- These tools **do not retrieve supplier promises from emails or PDFs**. To compare an actual promise with the PO, the buyer must provide that information, or a separate email/document-reading capability must be connected and tested.
- The catalog does **not** contain the earlier item-code search across PO lines. **Get Item** is not a substitute for it.
- A PO’s header schedule date and an item’s schedule date are different fields; the agent should report them separately.
- These tools can help collect facts, but the buyer decides whether a delivery is acceptable or needs follow-up.
- The JSON’s provider was previously marked **disabled/hidden**, so the tools need to be enabled and tested in ART before being relied on.
