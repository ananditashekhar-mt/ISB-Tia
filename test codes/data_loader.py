import json
import re
import pandas as pd

DATASET_FILE = "ISB_Post_Purchase_Apparel_AI_Agent_Dataset_v2.xlsx"


def load_dataset():
  policies_df = pd.read_excel(DATASET_FILE, sheet_name="Policies")
  catalog_df = pd.read_excel(DATASET_FILE, sheet_name="Product_Catalog")
  orders_df = pd.read_excel(DATASET_FILE, sheet_name="Orders")
  support_df = pd.read_excel(DATASET_FILE, sheet_name="Support_Conversations")
  intents_df = pd.read_excel(DATASET_FILE, sheet_name="Intent_Taxonomy")
  return policies_df, catalog_df, orders_df, support_df, intents_df


def tool_get_order(order_id: str):
  _, _, orders_df, _, _ = load_dataset()
  matches = orders_df[orders_df["Order_ID"] == order_id]
  return matches.iloc[0].to_dict() if not matches.empty else None


def tool_check_inventory(sku: str, size: str = None, colour: str = None):
  _, catalog_df, _, _, _ = load_dataset()
  query = catalog_df["SKU"] == sku
  if size:
    query &= catalog_df["Size"] == size
  if colour:
    query &= catalog_df["Colour"].str.lower() == colour.lower()
  matches = catalog_df[query]
  return int(matches.iloc[0]["Stock_Qty"]) if not matches.empty else 0


def retrieve_policy_rag(query: str, intent: str = None):
  """Lexical RAG Retriever over store policies."""
  policies_df, _, _, _, _ = load_dataset()
  policies = policies_df.to_dict(orient="records")

  intent_policy_map = {
      "return_request": ["POL-01", "POL-08"],
      "exchange_size": ["POL-02", "POL-01"],
      "exchange_color": ["POL-02", "POL-01"],
      "fit_issue": ["POL-02", "POL-01"],
      "damaged_item": ["POL-03"],
      "wrong_item": ["POL-03"],
      "delivery_delay": ["POL-05"],
      "cancel_order": ["POL-06"],
  }

  required_ids = intent_policy_map.get(intent, [])
  tokens = set(re.findall(r"\w+", query.lower()))

  ranked = sorted(
      policies,
      key=lambda p: len(
          tokens & set(re.findall(r"\w+", json.dumps(p).lower()))
      ),
      reverse=True,
  )

  filtered = [p for p in policies if p["Policy_ID"] in required_ids]
  return filtered if filtered else ranked[:2]