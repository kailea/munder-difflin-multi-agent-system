# Beaver's Choice Paper Company — Multi-Agent System

Final project for the Udacity **Agentic AI** program. The system is a five-agent sales desk for a paper supplier, built with [smolagents](https://github.com/huggingface/smolagents). For each customer request it:

- works out which items the customer wants;
- checks them against the product range and current stock;
- restocks from the supplier when that can still meet the customer's deadline;
- prices the order with bulk discounts;
- books the sale in SQLite;
- replies with a clear, customer-safe explanation.

![Agent workflow diagram](https://raw.githubusercontent.com/kailea/munder-difflin-multi-agent-system/main/agent_workflow_diagram.png)

## Submission contents

| File | Purpose |
|---|---|
| [`project_solution.py`](project_solution.py) | Full implementation in a single file: the starter helpers plus all agents and tools |
| [`agent_workflow_diagram.png`](agent_workflow_diagram.png) | Agents, their tools, the starter helper each tool uses, and the data flows |
| [`reflection_report.md`](reflection_report.md) | Architecture rationale, evaluation discussion, and improvement suggestions |
| [`test_results.csv`](test_results.csv) | Evaluation output for all 20 requests in `quote_requests_sample.csv` |
| [`business_advisor_report.txt`](business_advisor_report.txt) | End-of-run internal review written by the Business Advisor agent |

## Architecture

| Agent | Role | Tools |
|---|---|---|
| **Orchestrator** | Customer front desk: delegates in a fixed order and writes the reply | `get_order_summary` + three managed agents |
| **Inventory Agent** | Maps items to the product range, checks stock against the deadline, places supplier restocks | `list_product_range`, `check_item_stock`, `assess_order_availability`, `place_supplier_restock`, `replenish_low_stock` |
| **Quoting Agent** | Prices lines that can be fulfilled, applies bulk discount tiers, justifies price with quote history | `search_past_quotes`, `build_quote` |
| **Sales Agent** | Runs a financial health check on large orders, finalises the sale, flags low stock | `review_financial_health`, `finalize_sale` |
| **Business Advisor** | Runs once after the evaluation; analyses transactions and recommends changes | `get_business_report`, `get_transaction_summary` |

**Key design choices**

- **LLMs route and write; Python does the maths.** Every decision that touches stock or money happens in a deterministic tool.
- **Request-scoped shared ledger.** Agents hand work to each other through a shared, per-request ledger rather than by passing IDs. Dates come from the evaluation loop, not the LLM, and one request can never touch another's order.
- **No silent substitutions.** A match that changes size, finish or material (e.g. "matte A3" → "A4 paper") is refused and declined with a reason.
- **Customer-safe replies.** Replies are written only from a verified order summary. A `final_answer_checks` guard also rejects any draft that mentions stock levels, costs, IDs or errors.

All seven required starter helpers are used: `create_transaction`, `get_all_inventory`, `get_stock_level`, `get_supplier_delivery_date`, `get_cash_balance`, `generate_financial_report` and `search_quote_history`. The helper-to-tool mapping is in the diagram and in Section 3 of the report.

## Evaluation results

| Metric | Result | Rubric requirement |
|---|---|---|
| Requests that changed the cash balance | **14** | ≥ 3 |
| Requests fulfilled | **14** (2 in full, 12 in part) | ≥ 3 |
| Requests declined outright, with reasons | **6** | ≥ 1 |
| Cash balance | $45,059.70 → $46,013.84 | — |

Requests were declined for two kinds of reason:
- **Not in the product range:** e.g. A3 paper, balloons, flyers.
- **Supplier lead time misses the deadline:** e.g. #19, where 2,000 glossy sheets would arrive April 23 against an April 20 deadline.

The full per-request breakdown and discussion are in the [reflection report](reflection_report.md).

## Running it

**Prerequisites:** Python 3.10–3.13 (3.12 recommended) and a Vocareum OpenAI API key.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install pandas==2.2.3 openai==1.76.0 SQLAlchemy==2.0.40 python-dotenv==1.1.0 numpy smolagents
echo "UDACITY_OPENAI_API_KEY=voc-your-key-here" > .env
python project_solution.py
```

A run takes a few minutes and produces `test_results.csv` and `business_advisor_report.txt`. The SQLite database `munder_difflin.db` is rebuilt from the CSVs on every run.

The `pip install` command above skips the starter's `requirements.txt` for two reasons:
- It pins the `typing` backport, which can shadow the built-in `typing` module on modern Python.
- `pandas==2.2.3` crashes on Python 3.14.

## Business assumptions

| Rule | Value |
|---|---|
| Customer price | Catalogue `unit_price` |
| Supplier (restock) cost | 60% of list price |
| Bulk discounts (by total units) | 5% at 500+, 10% at 1,000+, 15% at 5,000+ |
| Customer shipping | 1 day after goods are on hand |
| Restock quantity | Shortfall plus the item's minimum stock level |
| Cash reserve | $5,000 is never spent on restocking |
| Unit conversion | 1 ream = 500 sheets |

## Data files (from the starter kit)

- `quote_requests_sample.csv`: the 20 evaluation requests
- `quote_requests.csv` and `quotes.csv`: historical requests and quotes used for quote-history search