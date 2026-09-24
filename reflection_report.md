# Beaver's Choice Paper Company — Multi-Agent System Report

## 1. Overview

This project implements a five-agent system, built with **smolagents** (`ToolCallingAgent`) on `gpt-4o-mini` through the Vocareum OpenAI-compatible proxy, that handles customer paper-supply requests end to end: it works out what the customer wants, checks it against the product range and stock, restocks from the supplier when that can still meet the deadline, prices the order with bulk discounts, books the sale, and replies to the customer with a transparent explanation. Everything lives in one file, `project_starter.py`. The workflow diagram is `agent_workflow_diagram.png`.

## 2. Architecture and agent workflow diagram

### 2.1 The five agents

| # | Agent | Responsibility (non-overlapping) | Tools |
|---|---|---|---|
| 1 | **Orchestrator** | Customer front desk. Delegates to the workers in a fixed order and writes the customer reply from a verified order summary. It computes no stock or prices. | `get_order_summary` + the three managed agents |
| 2 | **Inventory Agent** | Owns **stock**. Maps requested items to the carried product range, checks stock and deadline feasibility, decides on and places supplier restocks, and replenishes items below their reorder point. | `list_product_range`, `check_item_stock`, `assess_order_availability`, `place_supplier_restock`, `replenish_low_stock` |
| 3 | **Quoting Agent** | Owns **pricing**. Prices the lines that can be fulfilled, applies the bulk discount tier, and justifies the price using historical quotes. | `search_past_quotes`, `build_quote` |
| 4 | **Sales Agent** | Owns **revenue**. Runs a health check before large orders, finalises the sale, confirms delivery dates, and flags products now below their reorder point. | `review_financial_health`, `finalize_sale` |
| 5 | **Business Advisor Agent** | Owns **business review**. Runs once after the evaluation, analyses all transactions, and writes internal recommendations to `business_advisor_report.txt`. | `get_business_report`, `get_transaction_summary` |

Only the Inventory Agent writes `stock_orders` transactions, and only the Sales Agent writes `sales` transactions. This keeps each responsibility with a single owner.

### 2.2 Orchestration and data flow (per request)

Before each customer message, the evaluation loop opens a **request context** in the shared `OrderLedger`. The context holds the request date, and each stage stores its result there: the assessment, then the quote, then the confirmation. Every tool reads today's date, and the previous stage's result, from this context.

1. **Orchestrator → Inventory Agent.** The orchestrator passes the customer's message word for word. The inventory agent calls `list_product_range`, builds one line item per product (the customer's quantity and unit exactly as written, plus the matched product name), and calls `assess_order_availability`. That tool converts reams to sheets, merges duplicate lines, and decides each line's status. If any line needs a restock, the agent calls `place_supplier_restock`.
2. **Orchestrator → Quoting Agent** (only if at least one line can be fulfilled). The quoting agent calls `search_past_quotes` for context, then `build_quote`, which prices the current request's assessment. It returns the price breakdown and a rationale.
3. **Orchestrator → Sales Agent.** For quotes of $500 or more, the sales agent first calls `review_financial_health`. It then calls `finalize_sale`, which rechecks stock, records one `sales` transaction per line, and reports any items below their reorder point.
4. **Orchestrator → Inventory Agent** (only if items were flagged). The inventory agent calls `replenish_low_stock`.
5. **Orchestrator → Customer.** The orchestrator calls `get_order_summary` and writes the reply from it alone. A final-answer check rejects any reply containing internal details, and the orchestrator rewrites it.

### 2.3 Why this architecture, and what the first run taught me

- **The LLM routes and writes; Python does the maths.** Every decision that changes money or stock is made in a deterministic tool. The LLMs still make the judgement calls: interpreting the request, mapping wordings like "white printer paper" to `A4 paper`, choosing quote-history search terms, and wording the reply.
- **A request-scoped blackboard instead of passing IDs.** The first design handed records between agents by ID (`ASM-0003` → `Q-0003`). The first full evaluation run showed this failing in two ways:
  - The quoting agent reused `ASM-0001` on seven different requests, so the first customer's order was quoted and sold again.
  - The LLM also passed the *deadline* as the request date, and turned "500 sheets" into `quantity: 1` because it misread the ream conversion.

  The fix was to remove anything the LLM could get wrong from its hands. Dates come from the request context. Tools read only the current request's records, so another customer's order cannot be touched. Quantities are passed exactly as the customer wrote them, together with their unit, and the tool does the conversion.
- **No silent substitutions.** The second run showed the LLM "helpfully" mapping requests to the nearest product we carry: "matte A3 paper" was sold as A4 paper, and "construction paper" as colored paper. The inventory agent now passes the customer's exact wording alongside its chosen product. The tool refuses any match whose product name lacks a distinguishing word from that wording (A3, A5, matte, recycled, construction, poster, envelope, and so on), so the line is declined as not carried rather than silently swapped.
- **Verified facts for the customer reply.** In the first run, the orchestrator paraphrased its workers' reports and leaked stock counts, reorder points and an "unknown quote ID" error. Now it writes only from `get_order_summary`, whose output contains nothing internal. A smolagents `final_answer_checks` guard also rejects replies that mention stock levels, IDs, costs or errors.
- **Deterministic safety nets for name matching.** Frequent phrasings map through an alias table, and fuzzy matching is used only for typos. It never crosses paper sizes, which prevents "A3 glossy" being matched to the "A4 glossy" alias.
- **Assess before quoting, quote before selling.** Following the order of a real sales desk means a customer is never quoted for something the company cannot deliver, and never charged for something that has not been quoted.
- **The tools are idempotent and defensive.** Restocking, quoting and finalising can each be called twice without side effects. `finalize_sale` refuses to oversell if a restock was missed.
- **The fifth agent was a deliberate choice.** The four core agents cover the brief, so the fifth slot went to the Business Advisor from the rubric's "stand out" suggestions. It runs outside the per-request loop, so it adds no cost per request.
- **smolagents `ToolCallingAgent`** was chosen over `CodeAgent` because structured JSON tool calls are easier to audit and cannot execute arbitrary code against the database.

## 3. Business rules and assumptions

| Rule | Value | Rationale |
|---|---|---|
| Customer price | Catalogue `unit_price` (list price) | Consistent with how historical quotes are priced |
| Supplier (wholesale) cost | 60% of list price | Gives the business a margin on restocked goods |
| Bulk discount tiers (total units) | 5% at 500+, 10% at 1,000+, 15% at 5,000+ | Matches the 5–15% range seen in `quotes.csv` |
| Customer shipping | 1 day after goods are on hand | In-stock goods ship on the request date |
| Restock quantity | Shortfall plus the item's `min_stock_level` | Refills the safety stock as well as the order |
| Cash reserve | $5,000 never spent on restocking | Protects business continuity |
| Product range | Items in the `inventory` table only | Items not carried are declined with a reason |
| Duplicate lines | Merged per product before assessment | Prevents counting the same stock twice (e.g. "A4 paper" plus "reams of printer paper") |
| Units | Reams × 500; all other units counted as single items | Done in code, not by the LLM |

A line is **rejected** if the product is not carried, if the earliest possible delivery (supplier ETA plus shipping) falls after the customer's deadline, or if restocking would breach the cash reserve. Restock and sale transactions are dated on the request date, which is when the order is placed and paid; the customer receives the later estimated delivery date.

### Helper function coverage

| Starter helper | Used in tool(s) |
|---|---|
| `create_transaction` | `place_supplier_restock`, `replenish_low_stock`, `finalize_sale` |
| `get_all_inventory` | `list_product_range`, `replenish_low_stock`, `get_transaction_summary` |
| `get_stock_level` | `check_item_stock`, `assess_order_availability`, `finalize_sale` |
| `get_supplier_delivery_date` | `assess_order_availability`, `replenish_low_stock` |
| `get_cash_balance` | `assess_order_availability`, `replenish_low_stock` |
| `generate_financial_report` | `review_financial_health` (Sales), `get_business_report` (Advisor) |
| `search_quote_history` | `search_past_quotes` |

## 4. Customer-facing transparency and safeguards

- **Explainable outputs.** Every reply lists the supplied items with quantities, line prices and delivery dates. It also shows the subtotal, the discount rate with the reason it applied (e.g. "10% bulk discount for an order of 1,000 units"), how many more units would unlock the next tier, and a reason for every declined item: either "not part of our product range" or "cannot be delivered by your deadline; earliest possible delivery is …".
- **No internal leakage.** The reply is written only from `get_order_summary`, which contains no stock counts, costs, cash figures or internal IDs. The orchestrator's `final_answer_checks` guard rejects any reply that mentions stock levels, reorder points, cash, costs, margins, internal IDs, tools, agents or errors, so the agent must rewrite it.
- **Graceful failure.** If the agent run raises an exception, the error is logged to the console and the customer receives a polite fallback message confirming that no charge was made.
- **No PII.** Only job role and event type are passed as context. No names or contact details are used.

## 5. Evaluation results (`test_results.csv`)

All 20 requests in `quote_requests_sample.csv` were processed in date order (the evaluation sorts by request date, so the IDs in the CSV appear in that order). The run produced no internal errors. The customer-reply check was never triggered, and no reply contained internal data.

| Req | Date | Outcome | Charged | Main reason for any unfulfilled lines |
|---|---|---|---|---|
| 1 | 04-01 | **Fulfilled** (glossy, cardstock, colored paper) | $65.00 | — |
| 2 | 04-03 | Declined | — | Poster paper, streamers and balloons not carried |
| 3 | 04-04 | Partial: 10,000 A4 sheets, 15% off | $425.00 | A3 not carried; "500 reams of printer paper" wrongly declined (see below) |
| 4 | 04-05 | Partial: A4 paper | $12.50 | Recycled cardstock not carried |
| 5 | 04-05 | Partial: cardstock | $45.00 | Letter-size colored paper and washi tape not carried |
| 6 | 04-06 | Partial: A4 paper, cardstock, 5% off | $42.75 | Construction paper not carried |
| 7 | 04-07 | Partial: glossy, 24×36 posters, cardstock, 10% off | $387.00 | Matte A3 not carried |
| 8 | 04-07 | Partial: glossy, 5% off | $95.00 | Matte, A5, recycled not carried |
| 9 | 04-07 | Declined | — | A4 restock cannot arrive by Apr 10; A3 glossy and envelopes not carried |
| 10 | 04-08 | **Fulfilled** (glossy, cardstock), 5% off | $137.75 | — |
| 11 | 04-08 | Declined | — | A3 glossy and A4 matte not carried |
| 12 | 04-08 | Partial: A4 paper and colored paper, 5% off | $42.75 | Napkins not carried; "colorful cardstock" was supplied as colored paper (see below) |
| 13 | 04-08 | Declined | — | A4 paper and cardstock cannot arrive by Apr 10 |
| 14 | 04-09 | Partial: cardstock, 5% off | $71.25 | 5,000 A4 cannot arrive by Apr 15; poster paper not carried |
| 15 | 04-12 | Declined | — | 10,000 A4 cannot arrive by Apr 15; A3 and cardboard not carried |
| 16 | 04-13 | Partial: 24×36 posters | $100.00 | A4 deadline; construction paper not carried |
| 17 | 04-14 | Partial: paper plates, 5% off | $47.50 | A4 deadline; A3, napkins, cups not carried |
| 18 | 04-14 | Partial: colored paper | $20.00 | Cardstock and A4 cannot arrive by Apr 15 |
| 19 | 04-15 | Partial: cardstock, 10% off | $135.00 | 2,000 glossy needs a 7-day restock and misses Apr 20; A3 matte not carried |
| 20 | 04-17 | Declined | — | Flyers, posters, tickets not carried |

**Summary against the rubric**

- **14 requests changed the cash balance** (at least 3 required). Revenue was $1,626.50 against restock spend of about $672. Cash rose from $45,059.70 before the first request to $46,013.84.
- **14 requests were successfully fulfilled**: 2 in full (#1, #10) and 12 in part, each with a charge, an order reference and a confirmed delivery date.
- **6 requests were declined outright** (#2, #9, #11, #13, #15, #20), and many individual lines were declined, each with a stated reason. Both kinds of "impossible constraint" appear: items the company does not carry, and supplier timelines that cannot meet the deadline (#9, #13, #15, #19).

### Strengths

- **Correct timeline reasoning.** The system restocks when the supplier can still meet the deadline and declines when it cannot. In #3, a restock of just under 10,000 sheets has a 7-day lead time, arrives Apr 11, and is delivered Apr 12, before the Apr 15 deadline. In #19, 2,000 glossy sheets would arrive Apr 23, after the Apr 20 deadline.
- **Profitable and consistent pricing.** Discounts follow the tiers every time, stay within the historical 5–15% band, and never undercut wholesale cost. The Business Advisor's report confirms A4 revenue of $475.50 against $327.39 of restock spend.
- **Honest partial fulfilment.** Customers receive what the company can supply, with a clear reason for the rest, and size, finish and material substitutions are refused (see #12 for the one gap). #11's reply even explains that we carry glossy and A4 paper, but not in the A3 size or matte finish requested. This recovered revenue on 12 requests that an all-or-nothing policy would have lost.
- **Accurate, isolated ledger.** Each request only sees its own records, every `sales` transaction matches its quoted line total, and no line was sold without stock.
- **Transparent, customer-safe replies.** Every reply shows the customer's own wording next to the product supplied, the subtotal, the discount and why it applied, delivery dates, and a reason for each declined item. None contains stock counts, costs or internal IDs.

### Areas for improvement observed

- **An item-mapping miss (#3).** The inventory agent put the quantity inside the product name (`"500 reams of printer paper"`), so the alias lookup for "printer paper" did not match. The line was declined as not carried instead of being sold as 250,000 A4 sheets. The failure was conservative, since nothing wrong was sold, but it lost the largest potential order in the dataset. The fix is small: strip a leading quantity and unit from names before lookup, and warn the orchestrator when an unmatched line resembles a carried product.
- **A gap in the substitution guard (#12).** The LLM mapped "colorful cardstock" to Colored paper, and the guard allowed it: its word list covers sizes, finishes and product types such as A3, matte, recycled and envelopes, but not the difference between cardstock and plain paper. The customer was charged the lower colored-paper price, so it cost them nothing, but it is still a silent substitution. The fix is to add "cardstock", "glossy" and "kraft" to the distinguishing words, so that each product family must match its own name.
- **A4 stock stuck at the reorder point.** After request #3, A4 stock stayed at its reorder point of 135 units, which the Business Advisor also flagged. Every later A4 request then needed a supplier restock with a 4–7 day lead time, and seven A4 lines (#9 and #13–#18) missed their deadlines. A4 was the most requested product, so the "shortfall plus reorder point" rule is too thin for high-demand items.
- **Narrow product range.** Most declined lines are items the company does not carry: A3 and A5 sheets, matte, recycled, construction paper, napkins and cups. This is lost revenue rather than a system error, and the advisor's report recommends broadening the range.
- **LLM variability.** Reply wording and some item mappings vary between runs. The code-level guards keep the numbers correct, but phrasing is not identical from run to run.

## 6. Suggestions for further improvement

1. **Demand-aware reorder targets.** Replace the fixed "shortfall plus reorder point" rule with targets based on recent sales velocity from the `transactions` table, for example keeping enough stock for 7–10 days of average demand for each item. Run `replenish_low_stock` after every sale rather than only when an item falls below its reorder point. This addresses the A4 deadline misses directly. The Business Advisor's output could also feed these targets back into the Inventory Agent.
2. **Split deliveries and partial-quantity offers.** When a deadline cannot be met in full, offer the in-stock quantity by the deadline and the remainder on the supplier date, priced as one order so the discount tier is kept. This would turn several declined lines (#9, #13, #14–#18) into sales and give customers a real choice.
3. **Customer negotiation agent.** Add a customer agent, driven by the job, event and mood context in `quote_requests.csv`, that can accept, decline or counter a quote (for example, "if I add 250 sheets do I reach the 10% tier?"). The Quoting Agent already reports the next discount tier, which gives the negotiation a concrete lever.
4. **Structured parsing with validation.** Have the Inventory Agent return a typed line-item list (for example a Pydantic model) that is validated before `assess_order_availability` is called, and log any mappings with low confidence. Every run so far has shown that parsing quantities, dates and item names is where the LLM is least reliable. The #3 miss, where the quantity ended up inside the product name, is exactly the kind of error a validated schema would reject before any stock is assessed.

## 7. How to run

```bash
pip install -r requirements.txt
pip install smolagents
echo "UDACITY_OPENAI_API_KEY=voc-..." > .env
python project_starter.py
```

The run produces `test_results.csv` (one row per request) and `business_advisor_report.txt` (internal review), and prints each agent's tool calls to the console.