import pandas as pd
import numpy as np
import os
import time
import dotenv
import ast
from sqlalchemy.sql import text
from datetime import datetime, timedelta
from typing import Dict, List, Union
from sqlalchemy import create_engine, Engine

# Create an SQLite database
db_engine = create_engine("sqlite:///munder_difflin.db")

# List containing the different kinds of papers 
paper_supplies = [
    # Paper Types (priced per sheet unless specified)
    {"item_name": "A4 paper",                         "category": "paper",        "unit_price": 0.05},
    {"item_name": "Letter-sized paper",               "category": "paper",        "unit_price": 0.06},
    {"item_name": "Cardstock",                        "category": "paper",        "unit_price": 0.15},
    {"item_name": "Colored paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Glossy paper",                     "category": "paper",        "unit_price": 0.20},
    {"item_name": "Matte paper",                      "category": "paper",        "unit_price": 0.18},
    {"item_name": "Recycled paper",                   "category": "paper",        "unit_price": 0.08},
    {"item_name": "Eco-friendly paper",               "category": "paper",        "unit_price": 0.12},
    {"item_name": "Poster paper",                     "category": "paper",        "unit_price": 0.25},
    {"item_name": "Banner paper",                     "category": "paper",        "unit_price": 0.30},
    {"item_name": "Kraft paper",                      "category": "paper",        "unit_price": 0.10},
    {"item_name": "Construction paper",               "category": "paper",        "unit_price": 0.07},
    {"item_name": "Wrapping paper",                   "category": "paper",        "unit_price": 0.15},
    {"item_name": "Glitter paper",                    "category": "paper",        "unit_price": 0.22},
    {"item_name": "Decorative paper",                 "category": "paper",        "unit_price": 0.18},
    {"item_name": "Letterhead paper",                 "category": "paper",        "unit_price": 0.12},
    {"item_name": "Legal-size paper",                 "category": "paper",        "unit_price": 0.08},
    {"item_name": "Crepe paper",                      "category": "paper",        "unit_price": 0.05},
    {"item_name": "Photo paper",                      "category": "paper",        "unit_price": 0.25},
    {"item_name": "Uncoated paper",                   "category": "paper",        "unit_price": 0.06},
    {"item_name": "Butcher paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Heavyweight paper",                "category": "paper",        "unit_price": 0.20},
    {"item_name": "Standard copy paper",              "category": "paper",        "unit_price": 0.04},
    {"item_name": "Bright-colored paper",             "category": "paper",        "unit_price": 0.12},
    {"item_name": "Patterned paper",                  "category": "paper",        "unit_price": 0.15},

    # Product Types (priced per unit)
    {"item_name": "Paper plates",                     "category": "product",      "unit_price": 0.10},  # per plate
    {"item_name": "Paper cups",                       "category": "product",      "unit_price": 0.08},  # per cup
    {"item_name": "Paper napkins",                    "category": "product",      "unit_price": 0.02},  # per napkin
    {"item_name": "Disposable cups",                  "category": "product",      "unit_price": 0.10},  # per cup
    {"item_name": "Table covers",                     "category": "product",      "unit_price": 1.50},  # per cover
    {"item_name": "Envelopes",                        "category": "product",      "unit_price": 0.05},  # per envelope
    {"item_name": "Sticky notes",                     "category": "product",      "unit_price": 0.03},  # per sheet
    {"item_name": "Notepads",                         "category": "product",      "unit_price": 2.00},  # per pad
    {"item_name": "Invitation cards",                 "category": "product",      "unit_price": 0.50},  # per card
    {"item_name": "Flyers",                           "category": "product",      "unit_price": 0.15},  # per flyer
    {"item_name": "Party streamers",                  "category": "product",      "unit_price": 0.05},  # per roll
    {"item_name": "Decorative adhesive tape (washi tape)", "category": "product", "unit_price": 0.20},  # per roll
    {"item_name": "Paper party bags",                 "category": "product",      "unit_price": 0.25},  # per bag
    {"item_name": "Name tags with lanyards",          "category": "product",      "unit_price": 0.75},  # per tag
    {"item_name": "Presentation folders",             "category": "product",      "unit_price": 0.50},  # per folder

    # Large-format items (priced per unit)
    {"item_name": "Large poster paper (24x36 inches)", "category": "large_format", "unit_price": 1.00},
    {"item_name": "Rolls of banner paper (36-inch width)", "category": "large_format", "unit_price": 2.50},

    # Specialty papers
    {"item_name": "100 lb cover stock",               "category": "specialty",    "unit_price": 0.50},
    {"item_name": "80 lb text paper",                 "category": "specialty",    "unit_price": 0.40},
    {"item_name": "250 gsm cardstock",                "category": "specialty",    "unit_price": 0.30},
    {"item_name": "220 gsm poster paper",             "category": "specialty",    "unit_price": 0.35},
]

# Given below are some utility functions you can use to implement your multi-agent system

def generate_sample_inventory(paper_supplies: list, coverage: float = 0.4, seed: int = 137) -> pd.DataFrame:
    """
    Generate inventory for exactly a specified percentage of items from the full paper supply list.

    This function randomly selects exactly `coverage` × N items from the `paper_supplies` list,
    and assigns each selected item:
    - a random stock quantity between 200 and 800,
    - a minimum stock level between 50 and 150.

    The random seed ensures reproducibility of selection and stock levels.

    Args:
        paper_supplies (list): A list of dictionaries, each representing a paper item with
                               keys 'item_name', 'category', and 'unit_price'.
        coverage (float, optional): Fraction of items to include in the inventory (default is 0.4, or 40%).
        seed (int, optional): Random seed for reproducibility (default is 137).

    Returns:
        pd.DataFrame: A DataFrame with the selected items and assigned inventory values, including:
                      - item_name
                      - category
                      - unit_price
                      - current_stock
                      - min_stock_level
    """
    # Ensure reproducible random output
    np.random.seed(seed)

    # Calculate number of items to include based on coverage
    num_items = int(len(paper_supplies) * coverage)

    # Randomly select item indices without replacement
    selected_indices = np.random.choice(
        range(len(paper_supplies)),
        size=num_items,
        replace=False
    )

    # Extract selected items from paper_supplies list
    selected_items = [paper_supplies[i] for i in selected_indices]

    # Construct inventory records
    inventory = []
    for item in selected_items:
        inventory.append({
            "item_name": item["item_name"],
            "category": item["category"],
            "unit_price": item["unit_price"],
            "current_stock": np.random.randint(200, 800),  # Realistic stock range
            "min_stock_level": np.random.randint(50, 150)  # Reasonable threshold for reordering
        })

    # Return inventory as a pandas DataFrame
    return pd.DataFrame(inventory)

def init_database(db_engine: Engine, seed: int = 137) -> Engine:    
    """
    Set up the Munder Difflin database with all required tables and initial records.

    This function performs the following tasks:
    - Creates the 'transactions' table for logging stock orders and sales
    - Loads customer inquiries from 'quote_requests.csv' into a 'quote_requests' table
    - Loads previous quotes from 'quotes.csv' into a 'quotes' table, extracting useful metadata
    - Generates a random subset of paper inventory using `generate_sample_inventory`
    - Inserts initial financial records including available cash and starting stock levels

    Args:
        db_engine (Engine): A SQLAlchemy engine connected to the SQLite database.
        seed (int, optional): A random seed used to control reproducibility of inventory stock levels.
                              Default is 137.

    Returns:
        Engine: The same SQLAlchemy engine, after initializing all necessary tables and records.

    Raises:
        Exception: If an error occurs during setup, the exception is printed and raised.
    """
    try:
        # ----------------------------
        # 1. Create an empty 'transactions' table schema
        # ----------------------------
        transactions_schema = pd.DataFrame({
            "id": [],
            "item_name": [],
            "transaction_type": [],  # 'stock_orders' or 'sales'
            "units": [],             # Quantity involved
            "price": [],             # Total price for the transaction
            "transaction_date": [],  # ISO-formatted date
        })
        transactions_schema.to_sql("transactions", db_engine, if_exists="replace", index=False)

        # Set a consistent starting date
        initial_date = datetime(2025, 1, 1).isoformat()

        # ----------------------------
        # 2. Load and initialize 'quote_requests' table
        # ----------------------------
        quote_requests_df = pd.read_csv("quote_requests.csv")
        quote_requests_df["id"] = range(1, len(quote_requests_df) + 1)
        quote_requests_df.to_sql("quote_requests", db_engine, if_exists="replace", index=False)

        # ----------------------------
        # 3. Load and transform 'quotes' table
        # ----------------------------
        quotes_df = pd.read_csv("quotes.csv")
        quotes_df["request_id"] = range(1, len(quotes_df) + 1)
        quotes_df["order_date"] = initial_date

        # Unpack metadata fields (job_type, order_size, event_type) if present
        if "request_metadata" in quotes_df.columns:
            quotes_df["request_metadata"] = quotes_df["request_metadata"].apply(
                lambda x: ast.literal_eval(x) if isinstance(x, str) else x
            )
            quotes_df["job_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("job_type", ""))
            quotes_df["order_size"] = quotes_df["request_metadata"].apply(lambda x: x.get("order_size", ""))
            quotes_df["event_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("event_type", ""))

        # Retain only relevant columns
        quotes_df = quotes_df[[
            "request_id",
            "total_amount",
            "quote_explanation",
            "order_date",
            "job_type",
            "order_size",
            "event_type"
        ]]
        quotes_df.to_sql("quotes", db_engine, if_exists="replace", index=False)

        # ----------------------------
        # 4. Generate inventory and seed stock
        # ----------------------------
        inventory_df = generate_sample_inventory(paper_supplies, seed=seed)

        # Seed initial transactions
        initial_transactions = []

        # Add a starting cash balance via a dummy sales transaction
        initial_transactions.append({
            "item_name": None,
            "transaction_type": "sales",
            "units": None,
            "price": 50000.0,
            "transaction_date": initial_date,
        })

        # Add one stock order transaction per inventory item
        for _, item in inventory_df.iterrows():
            initial_transactions.append({
                "item_name": item["item_name"],
                "transaction_type": "stock_orders",
                "units": item["current_stock"],
                "price": item["current_stock"] * item["unit_price"],
                "transaction_date": initial_date,
            })

        # Commit transactions to database
        pd.DataFrame(initial_transactions).to_sql("transactions", db_engine, if_exists="append", index=False)

        # Save the inventory reference table
        inventory_df.to_sql("inventory", db_engine, if_exists="replace", index=False)

        return db_engine

    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

def create_transaction(
    item_name: str,
    transaction_type: str,
    quantity: int,
    price: float,
    date: Union[str, datetime],
) -> int:
    """
    This function records a transaction of type 'stock_orders' or 'sales' with a specified
    item name, quantity, total price, and transaction date into the 'transactions' table of the database.

    Args:
        item_name (str): The name of the item involved in the transaction.
        transaction_type (str): Either 'stock_orders' or 'sales'.
        quantity (int): Number of units involved in the transaction.
        price (float): Total price of the transaction.
        date (str or datetime): Date of the transaction in ISO 8601 format.

    Returns:
        int: The ID of the newly inserted transaction.

    Raises:
        ValueError: If `transaction_type` is not 'stock_orders' or 'sales'.
        Exception: For other database or execution errors.
    """
    try:
        # Convert datetime to ISO string if necessary
        date_str = date.isoformat() if isinstance(date, datetime) else date

        # Validate transaction type
        if transaction_type not in {"stock_orders", "sales"}:
            raise ValueError("Transaction type must be 'stock_orders' or 'sales'")

        # Prepare transaction record as a single-row DataFrame
        transaction = pd.DataFrame([{
            "item_name": item_name,
            "transaction_type": transaction_type,
            "units": quantity,
            "price": price,
            "transaction_date": date_str,
        }])

        # Insert the record into the database
        transaction.to_sql("transactions", db_engine, if_exists="append", index=False)

        # Fetch and return the ID of the inserted row
        result = pd.read_sql("SELECT last_insert_rowid() as id", db_engine)
        return int(result.iloc[0]["id"])

    except Exception as e:
        print(f"Error creating transaction: {e}")
        raise

def get_all_inventory(as_of_date: str) -> Dict[str, int]:
    """
    Retrieve a snapshot of available inventory as of a specific date.

    This function calculates the net quantity of each item by summing 
    all stock orders and subtracting all sales up to and including the given date.

    Only items with positive stock are included in the result.

    Args:
        as_of_date (str): ISO-formatted date string (YYYY-MM-DD) representing the inventory cutoff.

    Returns:
        Dict[str, int]: A dictionary mapping item names to their current stock levels.
    """
    # SQL query to compute stock levels per item as of the given date
    query = """
        SELECT
            item_name,
            SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END) as stock
        FROM transactions
        WHERE item_name IS NOT NULL
        AND transaction_date <= :as_of_date
        GROUP BY item_name
        HAVING stock > 0
    """

    # Execute the query with the date parameter
    result = pd.read_sql(query, db_engine, params={"as_of_date": as_of_date})

    # Convert the result into a dictionary {item_name: stock}
    return dict(zip(result["item_name"], result["stock"]))

def get_stock_level(item_name: str, as_of_date: Union[str, datetime]) -> pd.DataFrame:
    """
    Retrieve the stock level of a specific item as of a given date.

    This function calculates the net stock by summing all 'stock_orders' and 
    subtracting all 'sales' transactions for the specified item up to the given date.

    Args:
        item_name (str): The name of the item to look up.
        as_of_date (str or datetime): The cutoff date (inclusive) for calculating stock.

    Returns:
        pd.DataFrame: A single-row DataFrame with columns 'item_name' and 'current_stock'.
    """
    # Convert date to ISO string format if it's a datetime object
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    # SQL query to compute net stock level for the item
    stock_query = """
        SELECT
            item_name,
            COALESCE(SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END), 0) AS current_stock
        FROM transactions
        WHERE item_name = :item_name
        AND transaction_date <= :as_of_date
    """

    # Execute query and return result as a DataFrame
    return pd.read_sql(
        stock_query,
        db_engine,
        params={"item_name": item_name, "as_of_date": as_of_date},
    )

def get_supplier_delivery_date(input_date_str: str, quantity: int) -> str:
    """
    Estimate the supplier delivery date based on the requested order quantity and a starting date.

    Delivery lead time increases with order size:
        - ≤10 units: same day
        - 11–100 units: 1 day
        - 101–1000 units: 4 days
        - >1000 units: 7 days

    Args:
        input_date_str (str): The starting date in ISO format (YYYY-MM-DD).
        quantity (int): The number of units in the order.

    Returns:
        str: Estimated delivery date in ISO format (YYYY-MM-DD).
    """
    # Debug log (comment out in production if needed)
    print(f"FUNC (get_supplier_delivery_date): Calculating for qty {quantity} from date string '{input_date_str}'")

    # Attempt to parse the input date
    try:
        input_date_dt = datetime.fromisoformat(input_date_str.split("T")[0])
    except (ValueError, TypeError):
        # Fallback to current date on format error
        print(f"WARN (get_supplier_delivery_date): Invalid date format '{input_date_str}', using today as base.")
        input_date_dt = datetime.now()

    # Determine delivery delay based on quantity
    if quantity <= 10:
        days = 0
    elif quantity <= 100:
        days = 1
    elif quantity <= 1000:
        days = 4
    else:
        days = 7

    # Add delivery days to the starting date
    delivery_date_dt = input_date_dt + timedelta(days=days)

    # Return formatted delivery date
    return delivery_date_dt.strftime("%Y-%m-%d")

def get_cash_balance(as_of_date: Union[str, datetime]) -> float:
    """
    Calculate the current cash balance as of a specified date.

    The balance is computed by subtracting total stock purchase costs ('stock_orders')
    from total revenue ('sales') recorded in the transactions table up to the given date.

    Args:
        as_of_date (str or datetime): The cutoff date (inclusive) in ISO format or as a datetime object.

    Returns:
        float: Net cash balance as of the given date. Returns 0.0 if no transactions exist or an error occurs.
    """
    try:
        # Convert date to ISO format if it's a datetime object
        if isinstance(as_of_date, datetime):
            as_of_date = as_of_date.isoformat()

        # Query all transactions on or before the specified date
        transactions = pd.read_sql(
            "SELECT * FROM transactions WHERE transaction_date <= :as_of_date",
            db_engine,
            params={"as_of_date": as_of_date},
        )

        # Compute the difference between sales and stock purchases
        if not transactions.empty:
            total_sales = transactions.loc[transactions["transaction_type"] == "sales", "price"].sum()
            total_purchases = transactions.loc[transactions["transaction_type"] == "stock_orders", "price"].sum()
            return float(total_sales - total_purchases)

        return 0.0

    except Exception as e:
        print(f"Error getting cash balance: {e}")
        return 0.0


def generate_financial_report(as_of_date: Union[str, datetime]) -> Dict:
    """
    Generate a complete financial report for the company as of a specific date.

    This includes:
    - Cash balance
    - Inventory valuation
    - Combined asset total
    - Itemized inventory breakdown
    - Top 5 best-selling products

    Args:
        as_of_date (str or datetime): The date (inclusive) for which to generate the report.

    Returns:
        Dict: A dictionary containing the financial report fields:
            - 'as_of_date': The date of the report
            - 'cash_balance': Total cash available
            - 'inventory_value': Total value of inventory
            - 'total_assets': Combined cash and inventory value
            - 'inventory_summary': List of items with stock and valuation details
            - 'top_selling_products': List of top 5 products by revenue
    """
    # Normalize date input
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    # Get current cash balance
    cash = get_cash_balance(as_of_date)

    # Get current inventory snapshot
    inventory_df = pd.read_sql("SELECT * FROM inventory", db_engine)
    inventory_value = 0.0
    inventory_summary = []

    # Compute total inventory value and summary by item
    for _, item in inventory_df.iterrows():
        stock_info = get_stock_level(item["item_name"], as_of_date)
        stock = stock_info["current_stock"].iloc[0]
        item_value = stock * item["unit_price"]
        inventory_value += item_value

        inventory_summary.append({
            "item_name": item["item_name"],
            "stock": stock,
            "unit_price": item["unit_price"],
            "value": item_value,
        })

    # Identify top-selling products by revenue
    top_sales_query = """
        SELECT item_name, SUM(units) as total_units, SUM(price) as total_revenue
        FROM transactions
        WHERE transaction_type = 'sales' AND transaction_date <= :date
        GROUP BY item_name
        ORDER BY total_revenue DESC
        LIMIT 5
    """
    top_sales = pd.read_sql(top_sales_query, db_engine, params={"date": as_of_date})
    top_selling_products = top_sales.to_dict(orient="records")

    return {
        "as_of_date": as_of_date,
        "cash_balance": cash,
        "inventory_value": inventory_value,
        "total_assets": cash + inventory_value,
        "inventory_summary": inventory_summary,
        "top_selling_products": top_selling_products,
    }


def search_quote_history(search_terms: List[str], limit: int = 5) -> List[Dict]:
    """
    Retrieve a list of historical quotes that match any of the provided search terms.

    The function searches both the original customer request (from `quote_requests`) and
    the explanation for the quote (from `quotes`) for each keyword. Results are sorted by
    most recent order date and limited by the `limit` parameter.

    Args:
        search_terms (List[str]): List of terms to match against customer requests and explanations.
        limit (int, optional): Maximum number of quote records to return. Default is 5.

    Returns:
        List[Dict]: A list of matching quotes, each represented as a dictionary with fields:
            - original_request
            - total_amount
            - quote_explanation
            - job_type
            - order_size
            - event_type
            - order_date
    """
    conditions = []
    params = {}

    # Build SQL WHERE clause using LIKE filters for each search term
    for i, term in enumerate(search_terms):
        param_name = f"term_{i}"
        conditions.append(
            f"(LOWER(qr.response) LIKE :{param_name} OR "
            f"LOWER(q.quote_explanation) LIKE :{param_name})"
        )
        params[param_name] = f"%{term.lower()}%"

    # Combine conditions; fallback to always-true if no terms provided
    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Final SQL query to join quotes with quote_requests
    query = f"""
        SELECT
            qr.response AS original_request,
            q.total_amount,
            q.quote_explanation,
            q.job_type,
            q.order_size,
            q.event_type,
            q.order_date
        FROM quotes q
        JOIN quote_requests qr ON q.request_id = qr.id
        WHERE {where_clause}
        ORDER BY q.order_date DESC
        LIMIT {limit}
    """

    # Execute parameterized query
    with db_engine.connect() as conn:
        result = conn.execute(text(query), params)
        return [dict(row._mapping) for row in result]

########################
########################
########################
# YOUR MULTI AGENT STARTS HERE
########################
########################
########################
#
# Architecture (smolagents, 5 agents in total):
#
#   1. OrchestratorAgent  - customer-facing front desk. Delegates to the three
#                           managed worker agents below in a fixed order and
#                           writes the final customer response.
#   2. InventoryAgent     - maps requested items to the product range, checks
#                           stock, decides on supplier restocks, replenishes
#                           items that fall below their reorder point.
#   3. QuotingAgent       - prices the fulfillable lines, applies bulk
#                           discounts, justifies the price with quote history.
#   4. SalesAgent         - finalises the sale, records revenue, confirms the
#                           delivery schedule, health-checks large orders.
#   5. BusinessAdvisorAgent - runs once after the evaluation, analyses all
#                           transactions and recommends operational changes.
#
# Worker agents never pass raw numbers to each other through the LLM. Every
# decision that touches money or stock is computed by a deterministic tool and
# stored in the shared OrderLedger under an ID (ASM-xxxx for an availability
# assessment, Q-xxxx for a quote). Agents hand these IDs along, which keeps
# the LLM in charge of *routing and wording* and keeps the arithmetic exact.
########################

import json
import difflib
from dataclasses import dataclass, field

from smolagents import OpenAIServerModel, ToolCallingAgent, tool

# ----------------------------------------------------------------------------
# Environment and model
# ----------------------------------------------------------------------------

dotenv.load_dotenv()

OPENAI_API_BASE = "https://openai.vocareum.com/v1"
OPENAI_MODEL_ID = "gpt-4o-mini"


def build_model() -> OpenAIServerModel:
    """Create the OpenAI-compatible model client used by every agent.

    Reads the key from UDACITY_OPENAI_API_KEY (falls back to OPENAI_API_KEY)
    and points the client at the Vocareum proxy.
    """
    api_key = os.getenv("UDACITY_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "No API key found. Add UDACITY_OPENAI_API_KEY=... to your .env file."
        )
    return OpenAIServerModel(
        model_id=OPENAI_MODEL_ID,
        api_base=OPENAI_API_BASE,
        api_key=api_key,
        temperature=0.0,
    )


# ----------------------------------------------------------------------------
# Business policy constants
# ----------------------------------------------------------------------------

# Catalogue unit_price is the customer list price. The supplier sells to us at
# a wholesale discount, which is what we pay when restocking.
SUPPLIER_COST_FACTOR = 0.60

# Days for our courier to deliver to the customer once goods are on hand.
CUSTOMER_SHIPPING_DAYS = 1

# Cash we never spend on restocking, so the business can keep operating.
MINIMUM_CASH_RESERVE = 5_000.00

# Orders whose quoted total exceeds this get a financial health check first.
LARGE_ORDER_THRESHOLD = 500.00

# Bulk discount tiers: (minimum total units in the order, discount rate).
# Ordered from largest to smallest. Rates are in line with the 5-15% range
# found in the historical quotes table.
BULK_DISCOUNT_TIERS = [
    (5_000, 0.15),
    (1_000, 0.10),
    (500, 0.05),
]


# ----------------------------------------------------------------------------
# Shared order ledger (in-memory hand-off between agents)
# ----------------------------------------------------------------------------

@dataclass
class OrderLedger:
    """Shared, request-scoped blackboard that the agents hand work through.

    The evaluation loop opens a new request context (with the request date)
    before each customer message. Every tool reads the date from here and only
    ever sees the assessment and quote belonging to the *current* request, so
    an agent cannot quote or sell another customer's order by reusing an ID.
    """

    assessments: dict = field(default_factory=dict)
    quotes: dict = field(default_factory=dict)
    request_counter: int = 0
    active_request_key: str = ""
    active_request_date: str = ""

    def start_request(self, request_date: str) -> str:
        """Open the context for a new customer request and return its key."""
        self.request_counter += 1
        self.active_request_key = f"REQ-{self.request_counter:04d}"
        self.active_request_date = normalize_date(request_date)
        return self.active_request_key

    def current_date(self) -> str:
        """Business date of the request being processed."""
        if not self.active_request_date:
            raise RuntimeError("No active request context.")
        return self.active_request_date

    def current_assessment(self):
        """Latest availability assessment for the current request, or None."""
        return self.assessments.get(self.active_request_key)

    def current_quote(self):
        """Quote for the current request, or None."""
        return self.quotes.get(self.active_request_key)

    def reset(self) -> None:
        """Clear all records (called at the start of an evaluation run)."""
        self.assessments.clear()
        self.quotes.clear()
        self.request_counter = 0
        self.active_request_key = ""
        self.active_request_date = ""


order_ledger = OrderLedger()


# ----------------------------------------------------------------------------
# Small internal helpers (not tools)
# ----------------------------------------------------------------------------

def normalize_date(date_value: str) -> str:
    """Return a plain YYYY-MM-DD string or raise ValueError.

    Transactions are stored as plain dates on purpose: the starter queries
    compare dates as strings, and '2025-04-07T00:00:00' <= '2025-04-07' is
    False, which would hide same-day transactions.
    """
    return datetime.fromisoformat(str(date_value).strip().split("T")[0]).strftime("%Y-%m-%d")


def add_days(date_str: str, days: int) -> str:
    """Add a number of days to a YYYY-MM-DD date string."""
    return (datetime.fromisoformat(date_str) + timedelta(days=days)).strftime("%Y-%m-%d")


def load_product_range() -> pd.DataFrame:
    """Return the products the company carries (the 'inventory' reference table)."""
    return pd.read_sql("SELECT * FROM inventory", db_engine)


# Common customer wordings for carried products. Checked before fuzzy
# matching so frequent phrasings map reliably, whatever the LLM passes.
PRODUCT_ALIASES = {
    "A4 paper": [
        "a4", "a4 paper", "a4 white paper", "white a4 paper", "a4 printer paper",
        "a4 printing paper", "a4 size printer paper", "a4 white printer paper",
        "high-quality a4 paper", "printer paper", "printing paper",
        "white printer paper", "standard printer paper", "standard printing paper",
        "white paper",
    ],
    "Glossy paper": [
        "glossy", "a4 glossy paper", "glossy a4 paper", "high-quality glossy paper",
    ],
    "Cardstock": [
        "heavy cardstock", "white cardstock", "colorful cardstock", "colored cardstock",
        "sturdy cardstock", "heavyweight cardstock", "high-quality white cardstock",
        "cardstock in various colors", "cardstock in assorted colors",
    ],
    "Colored paper": [
        "coloured paper", "colorful paper", "assorted colored paper",
        "colored paper (assorted colors)",
    ],
    "Large poster paper (24x36 inches)": [
        "poster board", "poster boards", "large poster paper", "24x36 poster paper",
        "poster boards (24x36)", "poster boards 24x36",
    ],
    "Paper plates": ["biodegradable paper plates", "paper plates (biodegradable)"],
}

# Multipliers that turn a customer's unit into single sellable units.
UNIT_MULTIPLIERS = {"ream": 500, "reams": 500}


def resolve_product_name(requested_name: str, product_range: pd.DataFrame):
    """Match a requested name to an exact carried product name.

    Order of checks: exact name (case-insensitive), known alias, then a very
    close spelling match (typos). Anything else is 'not carried'.
    Returns the exact item_name or None.
    """
    carried = {name.lower().strip(): name for name in product_range["item_name"]}
    lookup = dict(carried)
    for product_name, alias_list in PRODUCT_ALIASES.items():
        if product_name.lower() in carried:
            for alias in alias_list:
                lookup.setdefault(alias, product_name)

    import re
    key = " ".join(requested_name.lower().replace('"', "").split())
    key_without_brackets = " ".join(re.sub(r"\(.*?\)", " ", key).split())
    for candidate_key in (key, key_without_brackets):
        if candidate_key in lookup:
            return lookup[candidate_key]

    # Fuzzy match only for typos, and never across paper sizes (A3 vs A4).
    def size_tokens(text: str) -> set:
        return set(re.findall(r"\ba\d\b", text))

    close = difflib.get_close_matches(key_without_brackets, list(lookup.keys()), n=1, cutoff=0.9)
    if close and size_tokens(close[0]) == size_tokens(key_without_brackets):
        return lookup[close[0]]
    return None


def to_single_units(quantity, unit: str) -> int:
    """Convert a customer quantity (e.g. 500 reams) into single units."""
    try:
        value = float(str(quantity).replace(",", ""))
    except (TypeError, ValueError):
        return 0
    multiplier = UNIT_MULTIPLIERS.get(str(unit or "").lower().strip(), 1)
    return int(value * multiplier)


# Words in the customer's wording that name a size, finish, material or
# product type. If the matched product's name lacks the word, the match is a
# substitution (e.g. "matte A3 paper" -> "A4 paper") and is refused.
DISTINGUISHING_WORDS = [
    r"\ba3\b", r"\ba5\b", r"8\.5", r"\bletter\b", r"\blegal\b", r"\bmatte\b",
    r"\brecycled\b", r"\bconstruction\b", r"\benvelopes?\b", r"\bposters?\b",
    r"\bnapkins?\b", r"\bcups?\b", r"\btickets?\b", r"\bflyers?\b",
    r"\bballoons?\b", r"\bstreamers?\b", r"\bcardboard\b", r"\bwashi\b",
]


def is_substitution(customer_wording: str, product_name: str) -> bool:
    """True if the customer's wording names something the product is not."""
    import re
    wording, product = customer_wording.lower(), product_name.lower()
    return any(
        re.search(pattern, wording) and not re.search(pattern, product)
        for pattern in DISTINGUISHING_WORDS
    )


def merge_duplicate_lines(line_items: list, product_range: pd.DataFrame) -> list:
    """Resolve names, convert units, and merge lines for the same product.

    Customers sometimes list one product twice under different wording (e.g.
    "A4 paper" and "reams of printer paper"). Assessing those separately would
    count the same stock twice and double-order from the supplier.
    Returns a list of {"requested_as", "quantity", "exact_name"} dicts.
    """
    merged, order = {}, []
    for raw_line in line_items:
        raw_line = raw_line if isinstance(raw_line, dict) else {}
        requested_name = str(raw_line.get("item_name", "")).strip()
        customer_wording = str(raw_line.get("customer_wording") or requested_name).strip()
        unit = str(raw_line.get("unit", "")).strip()
        quantity = to_single_units(raw_line.get("quantity", 0), unit)
        exact_name = (resolve_product_name(requested_name, product_range)
                      or resolve_product_name(customer_wording, product_range))
        if exact_name and is_substitution(customer_wording, exact_name):
            exact_name = None  # never sell a different product than was asked for
        label = f"{raw_line.get('quantity')} {unit} {customer_wording}".replace("  ", " ").strip()
        key = exact_name or f"__uncarried__{len(order)}"
        if key in merged:
            merged[key]["quantity"] += quantity
            merged[key]["requested_as"] += f" + {label}"
        else:
            merged[key] = {"requested_as": label, "quantity": quantity, "exact_name": exact_name}
            order.append(key)
    return [merged[key] for key in order]


def current_stock(item_name: str, as_of_date: str) -> int:
    """Stock on hand for one item, via the starter helper get_stock_level."""
    stock_df = get_stock_level(item_name, as_of_date)
    return int(stock_df["current_stock"].iloc[0]) if not stock_df.empty else 0


def discount_rate_for_units(total_units: int) -> float:
    """Pick the bulk discount rate for an order of the given total units."""
    for minimum_units, rate in BULK_DISCOUNT_TIERS:
        if total_units >= minimum_units:
            return rate
    return 0.0


def to_json(payload) -> str:
    """Serialise tool output as readable JSON for the LLM."""
    return json.dumps(payload, indent=2, default=str)


# ----------------------------------------------------------------------------
# Tools for the inventory agent
# (dates come from the active request context, never from the LLM)
# ----------------------------------------------------------------------------

@tool
def list_product_range() -> str:
    """List every product the company carries, with its exact name, category
    and list price per unit, and whether it is currently in stock. Use the
    exact names from this list when assessing a customer's order.
    """
    as_of_date = order_ledger.current_date()
    stock_by_item = get_all_inventory(as_of_date)  # only items with stock > 0
    products = [
        {
            "item_name": product["item_name"],
            "category": product["category"],
            "list_price_per_unit": float(product["unit_price"]),
            "in_stock": int(stock_by_item.get(product["item_name"], 0)) > 0,
        }
        for _, product in load_product_range().iterrows()
    ]
    return to_json({"today": as_of_date, "products": products})


@tool
def check_item_stock(item_name: str) -> str:
    """Internal stock check for one carried product: units on hand today and
    whether it is below its reorder point. Use for stock questions only; never
    quote these numbers to customers.

    Args:
        item_name: Exact product name from the product range.
    """
    as_of_date = order_ledger.current_date()
    product_range = load_product_range()
    exact_name = resolve_product_name(item_name, product_range)
    if exact_name is None:
        return to_json({"item_name": item_name, "carried": False})

    product = product_range[product_range["item_name"] == exact_name].iloc[0]
    stock = current_stock(exact_name, as_of_date)
    return to_json({
        "item_name": exact_name,
        "carried": True,
        "units_in_stock": stock,
        "reorder_point": int(product["min_stock_level"]),
        "below_reorder_point": stock < int(product["min_stock_level"]),
    })


@tool
def assess_order_availability(line_items: list, deadline: str) -> str:
    """Check whether each requested line can be delivered by the customer's
    deadline, and work out the supplier restock needed for any shortfall.
    The result is stored for the current request (the quoting and sales
    agents read it from there).

    Per line: products we do not carry are rejected; lines covered by current
    stock ship today; shortfalls are restocked from the supplier (shortfall
    plus the item's reorder point as safety stock) and the line is rejected if
    the supplier cannot deliver in time or restocking would breach the cash
    reserve. Duplicate lines for the same product are merged.

    Args:
        line_items: List of objects {"customer_wording": str, "item_name": str, "quantity": number, "unit": str}. customer_wording is the item description copied verbatim from the customer's message (e.g. "matte A3 paper"). item_name is the exact carried product name when it is clearly the same product, otherwise the customer's wording again. quantity and unit are copied exactly as written (e.g. 500 and "sheets", 500 and "reams"); the tool converts reams itself. A match that changes size, finish or material is automatically refused.
        deadline: Customer's required delivery date as YYYY-MM-DD, or an empty string if none was given.
    """
    request_date = order_ledger.current_date()
    try:
        deadline = normalize_date(deadline) if str(deadline).strip() else ""
    except ValueError:
        return "ERROR: deadline must be YYYY-MM-DD or an empty string."
    if not isinstance(line_items, list) or not line_items:
        return "ERROR: line_items must be a non-empty list of {item_name, quantity, unit} objects."

    product_range = load_product_range()
    spendable_cash = get_cash_balance(request_date) - MINIMUM_CASH_RESERVE
    committed_restock_cost = 0.0
    assessed_lines = []

    for line in merge_duplicate_lines(line_items, product_range):
        quantity = line["quantity"]
        exact_name = line.pop("exact_name")

        if quantity <= 0:
            line.update(status="rejected", reason="The requested quantity was unclear.")
            assessed_lines.append(line)
            continue
        if exact_name is None:
            line.update(status="rejected", reason="This item is not part of our product range.")
            assessed_lines.append(line)
            continue

        product = product_range[product_range["item_name"] == exact_name].iloc[0]
        unit_price = float(product["unit_price"])
        reorder_point = int(product["min_stock_level"])
        stock = current_stock(exact_name, request_date)
        line.update(item_name=exact_name, unit_price=unit_price)

        if stock >= quantity:
            # Fully covered by current stock: ships from the warehouse today.
            ready_date = request_date
            line.update(restock_units=0, restock_cost=0.0, supplier_delivery_date=None)
        else:
            # Shortfall: restock shortfall plus safety stock from the supplier.
            restock_units = (quantity - stock) + reorder_point
            ready_date = get_supplier_delivery_date(request_date, restock_units)
            line.update(
                restock_units=restock_units,
                restock_cost=round(restock_units * unit_price * SUPPLIER_COST_FACTOR, 2),
                supplier_delivery_date=ready_date,
            )

        delivery_date = add_days(ready_date, CUSTOMER_SHIPPING_DAYS)
        line["estimated_delivery_date"] = delivery_date

        if deadline and delivery_date > deadline:
            line.update(
                status="rejected",
                reason=(
                    f"This quantity needs a delivery from our supplier and the earliest we "
                    f"can deliver it is {delivery_date}, after your {deadline} deadline."
                ),
            )
        elif line["restock_cost"] > 0 and committed_restock_cost + line["restock_cost"] > spendable_cash:
            line.update(status="rejected",
                        reason="We are unable to source this volume from our supplier at this time.")
        else:
            committed_restock_cost += line["restock_cost"]
            line.update(status="fulfillable",
                        restock_required=line["restock_units"] > 0,
                        restock_placed=False)
        assessed_lines.append(line)

    order_ledger.assessments[order_ledger.active_request_key] = {
        "request_date": request_date,
        "deadline": deadline,
        "lines": assessed_lines,
    }

    # What the agent sees: statuses and reasons, no stock counts or costs.
    return to_json({
        "request_date": request_date,
        "deadline": deadline or "none given",
        "lines": [
            {
                "requested_as": l["requested_as"],
                "matched_product": l.get("item_name"),
                "units": l["quantity"],
                "status": l["status"],
                "needs_restock": l.get("restock_required", False),
                "estimated_delivery_date": l.get("estimated_delivery_date") if l["status"] == "fulfillable" else None,
                "reason": l.get("reason"),
            }
            for l in assessed_lines
        ],
        "next_step": (
            "Call place_supplier_restock."
            if any(l.get("restock_required") for l in assessed_lines) else "No restock needed."
        ),
    })


@tool
def place_supplier_restock() -> str:
    """Place supplier restock orders for every fulfillable line of the current
    request's assessment that needs more stock. Records a 'stock_orders'
    transaction per item at wholesale cost. Safe to call more than once.
    """
    assessment = order_ledger.current_assessment()
    if assessment is None:
        return "ERROR: no availability assessment exists for this request yet."

    placed = []
    for line in assessment["lines"]:
        if line.get("status") != "fulfillable" or not line.get("restock_required"):
            continue
        if line.get("restock_placed"):
            continue
        create_transaction(
            item_name=line["item_name"],
            transaction_type="stock_orders",
            quantity=int(line["restock_units"]),
            price=float(line["restock_cost"]),
            date=assessment["request_date"],
        )
        line["restock_placed"] = True
        placed.append({"item_name": line["item_name"],
                       "supplier_delivery_date": line["supplier_delivery_date"]})

    return to_json({
        "restock_orders_placed": placed,
        "message": "No restock was required." if not placed else f"{len(placed)} restock order(s) placed.",
    })


@tool
def replenish_low_stock() -> str:
    """Scan every carried product and reorder any item whose stock has fallen
    below its reorder point, topping it back up to twice the reorder point.
    Skips reorders that would breach the company's cash reserve.
    """
    as_of_date = order_ledger.current_date()
    stock_by_item = get_all_inventory(as_of_date)
    spendable_cash = get_cash_balance(as_of_date) - MINIMUM_CASH_RESERVE
    reordered, skipped = [], []

    for _, product in load_product_range().iterrows():
        item_name = product["item_name"]
        stock = int(stock_by_item.get(item_name, 0))
        reorder_point = int(product["min_stock_level"])
        if stock >= reorder_point:
            continue
        units = 2 * reorder_point - stock
        cost = round(units * float(product["unit_price"]) * SUPPLIER_COST_FACTOR, 2)
        if cost > spendable_cash:
            skipped.append({"item_name": item_name, "reason": "insufficient cash above reserve"})
            continue
        create_transaction(item_name, "stock_orders", units, cost, as_of_date)
        spendable_cash -= cost
        reordered.append({
            "item_name": item_name,
            "units_ordered": units,
            "supplier_delivery_date": get_supplier_delivery_date(as_of_date, units),
        })

    return to_json({"as_of_date": as_of_date, "reordered": reordered, "skipped": skipped})


# ----------------------------------------------------------------------------
# Tools for the quoting agent
# ----------------------------------------------------------------------------

@tool
def search_past_quotes(search_terms: list, limit: int = 5) -> str:
    """Search historical quotes for similar requests to guide pricing and the
    explanation given to the customer. Tries all terms together first, then
    each term on its own if nothing matched.

    Args:
        search_terms: One to three short keywords, e.g. ["cardstock", "ceremony"].
        limit: Maximum number of past quotes to return (default 5).
    """
    terms = [str(t).strip() for t in (search_terms or []) if str(t).strip()]
    matches = search_quote_history(terms, limit=limit)
    if not matches:
        for term in terms:
            matches = search_quote_history([term], limit=limit)
            if matches:
                break
    trimmed = [
        {
            "total_amount": m["total_amount"],
            "quote_explanation": m["quote_explanation"],
            "order_size": m["order_size"],
            "event_type": m["event_type"],
        }
        for m in matches
    ]
    return to_json({"search_terms": terms, "matches": trimmed})


@tool
def build_quote() -> str:
    """Price every fulfillable line of the current request's availability
    assessment at list price, apply the bulk discount tier for the total units
    ordered, and store the quote for the sales agent. Lines that cannot be
    fulfilled are listed separately with their reasons. Calling it again
    returns the same quote.

    Discount tiers by total units: 500+ units 5%, 1,000+ units 10%, 5,000+ units 15%.
    """
    existing = order_ledger.current_quote()
    if existing is not None:
        return to_json(existing)
    assessment = order_ledger.current_assessment()
    if assessment is None:
        return "ERROR: no availability assessment exists for this request yet."

    fulfillable = [l for l in assessment["lines"] if l["status"] == "fulfillable"]
    excluded = [
        {"item": l["requested_as"], "reason": l["reason"]}
        for l in assessment["lines"] if l["status"] != "fulfillable"
    ]
    if not fulfillable:
        return to_json({
            "quote_created": False,
            "message": "No lines can be fulfilled, so no quote was created.",
            "excluded_lines": excluded,
        })

    total_units = sum(l["quantity"] for l in fulfillable)
    discount_rate = discount_rate_for_units(total_units)

    quote_lines = []
    for line in fulfillable:
        line_subtotal = round(line["quantity"] * line["unit_price"], 2)
        quote_lines.append({
            "customer_requested": line["requested_as"],
            "item_name": line["item_name"],
            "quantity": line["quantity"],
            "unit_price": line["unit_price"],
            "line_subtotal": line_subtotal,
            "line_total_after_discount": round(line_subtotal * (1 - discount_rate), 2),
            "estimated_delivery_date": line["estimated_delivery_date"],
        })

    subtotal = round(sum(l["line_subtotal"] for l in quote_lines), 2)
    total = round(sum(l["line_total_after_discount"] for l in quote_lines), 2)
    next_tier = next((tier for tier in reversed(BULK_DISCOUNT_TIERS) if tier[0] > total_units), None)

    quote = {
        "quote_created": True,
        "request_date": assessment["request_date"],
        "total_units": total_units,
        "discount_rate": discount_rate,
        "discount_explanation": (
            f"{int(discount_rate * 100)}% bulk discount for an order of {total_units:,} units."
            if discount_rate else
            f"No bulk discount: {total_units:,} units is below our 500-unit tier."
        ),
        "next_discount_tier": (
            f"{int(next_tier[1] * 100)}% off from {next_tier[0]:,} units" if next_tier else None
        ),
        "subtotal": subtotal,
        "discount_amount": round(subtotal - total, 2),
        "total": total,
        "lines": quote_lines,
        "excluded_lines": excluded,
        "status": "quoted",
    }
    order_ledger.quotes[order_ledger.active_request_key] = quote
    return to_json(quote)


# ----------------------------------------------------------------------------
# Tools for the sales agent
# ----------------------------------------------------------------------------

@tool
def review_financial_health() -> str:
    """Internal health check before finalising a large order: cash balance,
    inventory value and total assets from the company financial report as of
    today. Never share these figures with customers.
    """
    report = generate_financial_report(order_ledger.current_date())
    return to_json({
        "cash_balance": round(float(report["cash_balance"]), 2),
        "inventory_value": round(float(report["inventory_value"]), 2),
        "total_assets": round(float(report["total_assets"]), 2),
        "healthy": report["cash_balance"] > MINIMUM_CASH_RESERVE,
    })


@tool
def finalize_sale() -> str:
    """Finalise the current request's quote as a sale. Re-checks stock for
    each line, records a 'sales' transaction per line at the discounted price,
    and returns the order confirmation plus any products now below their
    reorder point. Safe to call more than once.
    """
    quote = order_ledger.current_quote()
    if quote is None:
        return "ERROR: no quote exists for this request. Nothing was charged."
    if quote["status"] == "finalized":
        return to_json({"message": "Already finalised.", "order": quote["confirmation"]})

    sale_date = quote["request_date"]
    product_range = load_product_range().set_index("item_name")
    confirmed, failed = [], []

    for line in quote["lines"]:
        if current_stock(line["item_name"], sale_date) < line["quantity"]:
            # Restock was never placed or stock changed: do not oversell.
            failed.append({"item": line["item_name"],
                           "reason": "We could not secure stock for this item in time."})
            continue
        create_transaction(
            item_name=line["item_name"],
            transaction_type="sales",
            quantity=int(line["quantity"]),
            price=float(line["line_total_after_discount"]),
            date=sale_date,
        )
        confirmed.append(line)

    low_stock_items = [
        l["item_name"] for l in confirmed
        if current_stock(l["item_name"], sale_date) < int(product_range.loc[l["item_name"], "min_stock_level"])
    ]

    confirmation = {
        "order_reference": f"ORD-{order_ledger.active_request_key.split('-')[1]}",
        "order_date": sale_date,
        "confirmed_lines": confirmed,
        "subtotal": round(sum(l["line_subtotal"] for l in confirmed), 2),
        "amount_charged": round(sum(l["line_total_after_discount"] for l in confirmed), 2),
        "unfulfilled_lines": quote["excluded_lines"] + failed,
    }
    quote["status"] = "finalized"
    quote["confirmation"] = confirmation

    return to_json({
        "order": confirmation,
        "items_below_reorder_point": low_stock_items,
    })


# ----------------------------------------------------------------------------
# Tool for the orchestrator
# ----------------------------------------------------------------------------

@tool
def get_order_summary() -> str:
    """Authoritative, customer-safe summary of the current request: what was
    confirmed (items, quantities, prices, delivery dates), subtotal, bulk
    discount and its reason, total charged, order reference, and every item
    that could not be supplied with its reason. Base the customer reply only
    on this summary.
    """
    assessment = order_ledger.current_assessment()
    quote = order_ledger.current_quote()
    if assessment is None:
        return to_json({"status": "not_assessed",
                        "message": "The request has not been assessed yet; ask the inventory agent first."})

    unfulfilled = [
        {"item": l["requested_as"], "reason": l["reason"]}
        for l in assessment["lines"] if l["status"] != "fulfillable"
    ]
    if quote is None or not quote.get("quote_created", True):
        return to_json({"status": "nothing_supplied", "amount_charged": 0.0,
                        "unfulfilled_items": unfulfilled})
    if quote["status"] != "finalized":
        return to_json({"status": "quoted_not_finalised",
                        "message": "Ask the sales agent to finalise the sale first."})

    confirmation = quote["confirmation"]
    if not confirmation["confirmed_lines"]:
        return to_json({"status": "nothing_supplied", "amount_charged": 0.0,
                        "unfulfilled_items": confirmation["unfulfilled_lines"]})
    return to_json({
        "status": "order_confirmed",
        "order_reference": confirmation["order_reference"],
        "items": [
            {
                "customer_requested": l["customer_requested"],
                "item": l["item_name"],
                "total_units": l["quantity"],
                "unit_price": l["unit_price"],
                "price_after_discount": l["line_total_after_discount"],
                "estimated_delivery_date": l["estimated_delivery_date"],
            }
            for l in confirmation["confirmed_lines"]
        ],
        "subtotal": confirmation["subtotal"],
        "discount": quote["discount_explanation"],
        "next_discount_tier": quote["next_discount_tier"],
        "amount_charged": confirmation["amount_charged"],
        "unfulfilled_items": confirmation["unfulfilled_lines"],
    })


# Phrases that must never reach a customer (internal data or failures).
CUSTOMER_REPLY_BLOCKLIST = [
    r"\bASM-\d", r"\bQ-\d", r"\bREQ-\d", r"reorder point", r"\bin stock\b",
    r"\bstock level", r"cash balance", r"inventory value", r"supplier cost",
    r"wholesale", r"\bmargin", r"\berror\b", r"\btool\b", r"_agent\b",
]


def reply_is_customer_safe(final_answer, memory, agent=None) -> bool:
    """final_answer_check for the orchestrator: reject replies that leak
    internal details. smolagents feeds the failure back so the agent rewrites.
    """
    import re
    text = str(final_answer)
    for pattern in CUSTOMER_REPLY_BLOCKLIST:
        if re.search(pattern, text, flags=re.IGNORECASE):
            raise ValueError(
                f"Reply contains internal detail matching '{pattern}'. Rewrite it using "
                f"only get_order_summary content, without stock levels, IDs or internal terms."
            )
    return True


# ----------------------------------------------------------------------------
# Tools for the business advisor agent
# ----------------------------------------------------------------------------

@tool
def get_business_report(as_of_date: str) -> str:
    """Full company financial report: cash, inventory value, total assets,
    per-item stock and value, and the top-selling products by revenue.

    Args:
        as_of_date: Date of the report, YYYY-MM-DD.
    """
    try:
        as_of_date = normalize_date(as_of_date)
    except ValueError:
        return "ERROR: as_of_date must be in YYYY-MM-DD format."
    return to_json(generate_financial_report(as_of_date))


@tool
def get_transaction_summary(start_date: str, end_date: str) -> str:
    """Summarise sales and supplier purchases per item between two dates
    (inclusive), plus current stock via the inventory snapshot.

    Args:
        start_date: First date to include, YYYY-MM-DD.
        end_date: Last date to include, YYYY-MM-DD.
    """
    try:
        start_date, end_date = normalize_date(start_date), normalize_date(end_date)
    except ValueError:
        return "ERROR: dates must be in YYYY-MM-DD format."
    query = """
        SELECT item_name, transaction_type,
               COUNT(*) AS transaction_count, SUM(units) AS units, SUM(price) AS amount
        FROM transactions
        WHERE item_name IS NOT NULL
          AND transaction_date >= :start_date AND transaction_date <= :end_date
        GROUP BY item_name, transaction_type
        ORDER BY item_name
    """
    activity = pd.read_sql(query, db_engine, params={"start_date": start_date, "end_date": end_date})
    return to_json({
        "period": f"{start_date} to {end_date}",
        "activity": activity.to_dict(orient="records"),
        "stock_on_hand": get_all_inventory(end_date),
    })


# ----------------------------------------------------------------------------
# Agent definitions
# ----------------------------------------------------------------------------

INVENTORY_AGENT_INSTRUCTIONS = """
You are the Inventory Agent of the Beaver's Choice Paper Company.
You own stock: you decide which requested items we carry, whether they can be
delivered in time, and you place supplier restock orders. Today's date is
handled by the tools; you never pass the request date.

Standard procedure for a customer order:
1. Call list_product_range to get the exact names of the products we carry.
2. Build one line item per product the customer asked for:
   - customer_wording: the item description copied verbatim from the message.
   - quantity: the number EXACTLY as the customer wrote it (500 stays 500,
     10,000 becomes 10000). Never divide or multiply it yourself.
   - unit: the customer's unit word ("sheets", "reams", "rolls", "units"...).
   - item_name: the exact carried product name when it is clearly the same
     product, otherwise the customer's own wording. Examples:
       "A4 printer paper", "white printer paper", "printing paper" -> "A4 paper"
       "A4 glossy paper", "high-quality glossy paper" -> "Glossy paper"
       "heavy cardstock (white)", "cardstock in various colors" -> "Cardstock"
       "colored paper (assorted colors)" -> "Colored paper"
       "poster boards (24x36)" -> "Large poster paper (24x36 inches)"
     Never substitute a different size, finish or material: A3, A5, 8.5x11 /
     letter, matte, recycled, construction paper, poster paper, envelopes,
     napkins, cups, balloons, streamers, tickets, flyers, cardboard and washi
     tape are not carried unless an identical product is listed, so pass the
     customer's wording as item_name for those.
3. Call assess_order_availability ONCE with all line items and the customer's
   deadline as YYYY-MM-DD (the year of the request if the customer omits it;
   "" if there is no deadline).
4. If the result says to, call place_supplier_restock.
5. Final answer: for each line, the product, units, status, delivery date or
   the rejection reason. Do not mention stock counts.

For a replenishment task, call replenish_low_stock.
For an internal stock question, use check_item_stock.
"""

QUOTING_AGENT_INSTRUCTIONS = """
You are the Quoting Agent of the Beaver's Choice Paper Company.
You price the current request, which the inventory agent has already assessed.

Procedure:
1. Call search_past_quotes with one or two keywords (the main product and/or
   the event type) to see how similar orders were priced and discounted.
2. Call build_quote (no arguments). Never invent or change prices: the
   tool's numbers are final.
3. Final answer: each priced line (quantity, unit price, line total), the
   subtotal, the discount and its explanation, the total, the delivery dates,
   the excluded lines with reasons, and a one or two sentence customer-friendly
   rationale that relates the price to similar past orders. If no quote was
   created, say so and list the excluded lines.
"""

SALES_AGENT_INSTRUCTIONS = """
You are the Sales Agent of the Beaver's Choice Paper Company.
You close the sale for the current request, which has already been quoted.

Procedure:
1. If the quote total is 500 or more, first call review_financial_health.
   This is an internal check; never repeat its figures.
2. Call finalize_sale (no arguments).
3. Final answer: the order reference, confirmed lines with prices and
   delivery dates, the amount charged, any unfulfilled lines with reasons,
   and items_below_reorder_point exactly as returned.
"""

ORCHESTRATOR_INSTRUCTIONS = """
You are the customer service Orchestrator of the Beaver's Choice Paper Company.
You never compute stock or prices yourself: you delegate to your team, then
reply to the customer. The system keeps each request's working data for you,
so you only need to pass on what the customer asked.

For every customer request follow these steps in order:
1. inventory_agent: pass the customer's message word for word, and ask it to
   assess availability for this order and place any restocks needed.
2. If at least one line is fulfillable, quoting_agent: ask it to build the
   quote for the current request, mentioning the customer's event type.
3. If a quote was created, sales_agent: ask it to finalise the current
   request's sale, and tell it the quote total.
4. If the sales agent reports items below their reorder point, ask the
   inventory_agent to run replenish_low_stock.
5. Call get_order_summary, then call final_answer with the customer reply.

Write the reply ONLY from get_order_summary:
- confirm each supplied item using its customer_requested wording, the product
  name and total_units (e.g. "10,000 sheets A4 paper + 500 reams printer paper
  -> 260,000 sheets of A4 paper"), with its price and estimated delivery date;
- show the subtotal, the discount and why it applied (or why none did), and the total charged;
- give the order reference if there is one;
- list every item we cannot supply with its reason, suggesting a close carried
  alternative where one obviously exists;
- if nothing could be supplied, apologise, explain why, and state that no
  charge has been made.
Never mention stock quantities, reorder points, costs, cash, internal IDs,
tools, agents or errors. Address the customer as "Dear Customer". Be concise.
"""

BUSINESS_ADVISOR_INSTRUCTIONS = """
You are the Business Advisor of the Beaver's Choice Paper Company.
Analyse the company's transactions and financial position and recommend
concrete operational changes to improve revenue and efficiency.
Call get_business_report for the end date and get_transaction_summary for
the whole period, then answer with: a short performance summary, the three to
five most important observations (best sellers, slow movers, restock spend
versus revenue, cash position), and three to five specific recommendations
(e.g. product range additions for frequently requested items we do not
carry, reorder point changes, discount tier changes). This report is internal.
"""


def build_agent_team(model: OpenAIServerModel) -> dict:
    """Create the five agents and wire the three workers under the orchestrator.

    Returns a dict with keys: orchestrator, inventory, quoting, sales, advisor.
    """
    inventory_agent = ToolCallingAgent(
        tools=[
            list_product_range,
            check_item_stock,
            assess_order_availability,
            place_supplier_restock,
            replenish_low_stock,
        ],
        model=model,
        name="inventory_agent",
        description=(
            "Inventory specialist for the current request. Give it the customer's "
            "message word for word. It maps items to our product range, checks stock "
            "and delivery feasibility against the deadline, places supplier restocks, "
            "and reports each line's status and reason. Can also replenish low stock."
        ),
        instructions=INVENTORY_AGENT_INSTRUCTIONS,
        max_steps=8,
        verbosity_level=1,
    )

    quoting_agent = ToolCallingAgent(
        tools=[search_past_quotes, build_quote],
        model=model,
        name="quoting_agent",
        description=(
            "Pricing specialist for the current request (after the inventory agent). "
            "Give it the customer's event type. It prices the fulfillable lines with "
            "bulk discounts informed by quote history and returns the price breakdown "
            "and a rationale."
        ),
        instructions=QUOTING_AGENT_INSTRUCTIONS,
        max_steps=6,
        verbosity_level=1,
    )

    sales_agent = ToolCallingAgent(
        tools=[review_financial_health, finalize_sale],
        model=model,
        name="sales_agent",
        description=(
            "Sales closer for the current request (after the quoting agent). Give it "
            "the quote total. It finalises the sale, records the transactions and "
            "returns the confirmation, delivery dates and any items now below their "
            "reorder point."
        ),
        instructions=SALES_AGENT_INSTRUCTIONS,
        max_steps=6,
        verbosity_level=1,
    )

    orchestrator_agent = ToolCallingAgent(
        tools=[get_order_summary],
        model=model,
        managed_agents=[inventory_agent, quoting_agent, sales_agent],
        name="orchestrator_agent",
        instructions=ORCHESTRATOR_INSTRUCTIONS,
        final_answer_checks=[reply_is_customer_safe],
        max_steps=12,
        verbosity_level=1,
    )

    business_advisor_agent = ToolCallingAgent(
        tools=[get_business_report, get_transaction_summary],
        model=model,
        name="business_advisor_agent",
        instructions=BUSINESS_ADVISOR_INSTRUCTIONS,
        max_steps=5,
        verbosity_level=1,
    )

    return {
        "orchestrator": orchestrator_agent,
        "inventory": inventory_agent,
        "quoting": quoting_agent,
        "sales": sales_agent,
        "advisor": business_advisor_agent,
    }


FALLBACK_CUSTOMER_MESSAGE = (
    "Dear Customer, thank you for your request. We were unable to complete your order "
    "automatically at this time, and no charge has been made. A member of our sales "
    "team will follow up with you shortly."
)


def handle_customer_request(orchestrator_agent: ToolCallingAgent, request_text: str,
                            request_date: str, customer_context: str) -> str:
    """Run one customer request through the orchestrator and return the reply.

    Opens a fresh request context first, so every tool works on this request's
    date and data only. Internal failures are logged to the console but never
    shown to the customer; a polite fallback message is returned instead.
    """
    order_ledger.start_request(request_date)
    task = (
        f"New customer request. Customer context: {customer_context}.\n"
        f"Customer message (the request date is {request_date}):\n{request_text}"
    )
    try:
        reply = str(orchestrator_agent.run(task, reset=True)).strip()
        return reply or FALLBACK_CUSTOMER_MESSAGE
    except Exception as error:  # keep internal errors away from the customer
        print(f"INTERNAL ERROR while handling request: {error}")
        return FALLBACK_CUSTOMER_MESSAGE


def run_business_advisor(advisor_agent: ToolCallingAgent, start_date: str, end_date: str) -> str:
    """Ask the business advisor for an end-of-period review and save it to disk."""
    try:
        advice = str(advisor_agent.run(
            f"Review company performance from {start_date} to {end_date} and give recommendations."
        ))
    except Exception as error:
        advice = f"Business advisor could not complete the review: {error}"
    with open("business_advisor_report.txt", "w", encoding="utf-8") as report_file:
        report_file.write(advice)
    return advice


# Run your test scenarios by writing them here. Make sure to keep track of them.

def run_test_scenarios():

    print("Initializing Database...")
    init_database(db_engine)
    order_ledger.reset()
    try:
        quote_requests_sample = pd.read_csv("quote_requests_sample.csv")
        quote_requests_sample["request_date"] = pd.to_datetime(
            quote_requests_sample["request_date"], format="%m/%d/%y", errors="coerce"
        )
        quote_requests_sample.dropna(subset=["request_date"], inplace=True)
        quote_requests_sample = quote_requests_sample.sort_values("request_date")
    except Exception as e:
        print(f"FATAL: Error loading test data: {e}")
        return

    # Get initial state
    initial_date = quote_requests_sample["request_date"].min().strftime("%Y-%m-%d")
    report = generate_financial_report(initial_date)
    current_cash = report["cash_balance"]
    current_inventory = report["inventory_value"]

    ############
    # INITIALIZE YOUR MULTI AGENT SYSTEM HERE
    ############
    agent_team = build_agent_team(build_model())
    orchestrator_agent = agent_team["orchestrator"]

    results = []
    for idx, row in quote_requests_sample.iterrows():
        request_date = row["request_date"].strftime("%Y-%m-%d")

        print(f"\n=== Request {idx+1} ===")
        print(f"Context: {row['job']} organizing {row['event']}")
        print(f"Request Date: {request_date}")
        print(f"Cash Balance: ${current_cash:.2f}")
        print(f"Inventory Value: ${current_inventory:.2f}")

        # Process request
        request_with_date = f"{row['request']} (Date of request: {request_date})"

        ############
        # USE YOUR MULTI AGENT SYSTEM TO HANDLE THE REQUEST
        ############
        customer_context = f"{row['job']} organizing a {row['event']} ({row['need_size']} order)"
        response = handle_customer_request(
            orchestrator_agent, request_with_date, request_date, customer_context
        )

        # Update state
        report = generate_financial_report(request_date)
        current_cash = report["cash_balance"]
        current_inventory = report["inventory_value"]

        print(f"Response: {response}")
        print(f"Updated Cash: ${current_cash:.2f}")
        print(f"Updated Inventory: ${current_inventory:.2f}")

        results.append(
            {
                "request_id": idx + 1,
                "request_date": request_date,
                "cash_balance": current_cash,
                "inventory_value": current_inventory,
                "response": response,
            }
        )

        time.sleep(1)

    # Final report
    final_date = quote_requests_sample["request_date"].max().strftime("%Y-%m-%d")
    final_report = generate_financial_report(final_date)
    print("\n===== FINAL FINANCIAL REPORT =====")
    print(f"Final Cash: ${final_report['cash_balance']:.2f}")
    print(f"Final Inventory: ${final_report['inventory_value']:.2f}")

    # Save results
    pd.DataFrame(results).to_csv("test_results.csv", index=False)

    # End-of-run review by the business advisor agent (internal report)
    print("\n===== BUSINESS ADVISOR REVIEW =====")
    print(run_business_advisor(agent_team["advisor"], initial_date, final_date))
    return results


if __name__ == "__main__":
    results = run_test_scenarios()