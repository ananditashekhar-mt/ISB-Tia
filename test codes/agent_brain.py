import re
from typing import List, TypedDict
from data_loader import (
    retrieve_policy_rag,
    tool_check_inventory,
    tool_get_order,
)
from langgraph.graph import END, START, StateGraph
from logger import log_audit, save_message
import pandas as pd


class AgentState(TypedDict, total=False):
  message: str
  session_id: str
  order_id: str
  intent: str
  frustration_score: int
  retrieved_policies: List[dict]
  order_details: dict
  response: str
  escalated: bool
  escalation_reason: str


def node_understand(state: AgentState) -> AgentState:
  text = state["message"].lower()
  angry_words = [
      "bad",
      "worst",
      "horrible",
      "terrible",
      "unacceptable",
      "useless",
      "angry",
      "scam",
      "fraud",
  ]
  score = sum(2 for w in angry_words if w in text)

  if any(
      w in text
      for w in ["where", "track", "status", "shipped", "arriving", "delivery"]
  ):
    intent = "order_tracking"
  elif any(w in text for w in ["late", "delayed", "delay"]):
    intent = "delivery_delay"
  elif any(
      w in text
      for w in ["return", "exchange", "replace", "size", "fit", "color", "colour"]
  ):
    intent = "return_exchange"
  elif any(w in text for w in ["policy", "rule", "guideline", "window"]):
    intent = "policy_query"
  elif any(
      w in text for w in ["damaged", "broken", "wrong", "missing", "defect"]
  ):
    intent = "damaged_item"
  else:
    intent = "general_query"

  match = re.search(r"ORD-\d+", state["message"], re.I)
  order_id = match.group().upper() if match else state.get("order_id")

  return {
      "intent": intent,
      "frustration_score": min(score, 10),
      "order_id": order_id,
  }


def node_retrieve(state: AgentState) -> AgentState:
  policies = retrieve_policy_rag(state["message"], state["intent"])
  order = tool_get_order(state["order_id"]) if state.get("order_id") else None
  return {"retrieved_policies": policies, "order_details": order}


def node_resolve(state: AgentState) -> AgentState:
  intent = state["intent"]
  order = state.get("order_details")

  if state["frustration_score"] >= 6:
    return {
        "response": (
            "I apologize for the poor experience. Escalating your ticket to a"
            " human specialist immediately."
        ),
        "escalated": True,
        "escalation_reason": "High Frustration / Aggressive Tone",
    }

  if not order:
    return {
        "response": (
            f"Could not find order **{state.get('order_id', 'N/A')}** in our"
            " records."
        ),
        "escalated": True,
        "escalation_reason": "Order ID Not Found",
    }

  if intent in ["order_tracking", "delivery_delay"]:
    resp = (
        f"Order **{order['Order_ID']}** ({order['Product_Name']}) Status:"
        f" **{order['Order_Status']}**.\n"
        f"Carrier: {order['Carrier']} | Tracking ID: {order['Tracking_ID']}"
    )
    escalate = order["Order_Status"] == "Delayed"
    return {
        "response": resp,
        "escalated": escalate,
        "escalation_reason": "Order Delayed past ETA" if escalate else "None",
    }

  elif intent == "return_exchange":
    if pd.isna(order.get("Delivered_Date")):
      return {
          "response": (
              f"Order {order['Order_ID']} has not been delivered yet."
          ),
          "escalated": False,
          "escalation_reason": "None",
      }

    days_passed = (
        pd.Timestamp.now() - pd.to_datetime(order["Delivered_Date"])
    ).days
    if days_passed > 30:
      return {
          "response": (
              f"Order {order['Order_ID']} was delivered {days_passed} days ago."
              " According to Policy **POL-01**, returns are only accepted"
              " within 30 days."
          ),
          "escalated": True,
          "escalation_reason": "Out of 30-Day Policy Window",
      }

    stock = tool_check_inventory(order["SKU"])
    if stock > 0:
      return {
          "response": (
              f"Exchange/Return approved for **{order['Product_Name']}**!"
              f" Stock Available: {stock} units."
          ),
          "escalated": False,
          "escalation_reason": "None",
      }
    else:
      return {
          "response": (
              f"The item **{order['Product_Name']}** is currently out of stock."
              " Transferring to human desk for refund options."
          ),
          "escalated": True,
          "escalation_reason": "Exchange Item Out of Stock",
      }

  elif intent == "policy_query":
    p_text = "\n".join([
        f"• **{p['Policy_Type']} ({p['Policy_ID']})**: {p['Policy_Text']}"
        for p in state["retrieved_policies"]
    ])
    return {
        "response": f"**Relevant Store Policies (RAG Retrieved):**\n\n{p_text}",
        "escalated": False,
        "escalation_reason": "None",
    }

  return {
      "response": "Transferring your request to human support.",
      "escalated": True,
      "escalation_reason": "Complex Policy Inquiry",
  }


def node_respond(state: AgentState) -> AgentState:
  save_message(state["session_id"], "user", state["message"])
  save_message(state["session_id"], "assistant", state["response"])
  log_audit(
      state["session_id"],
      state["intent"],
      state["escalated"],
      state["escalation_reason"],
  )
  return state


# Compile LangGraph
builder = StateGraph(AgentState)
builder.add_node("understand", node_understand)
builder.add_node("retrieve", node_retrieve)
builder.add_node("resolve", node_resolve)
builder.add_node("respond", node_respond)

builder.add_edge(START, "understand")
builder.add_edge("understand", "retrieve")
builder.add_edge("retrieve", "resolve")
builder.add_edge("resolve", "respond")
builder.add_edge("respond", END)

langgraph_agent = builder.compile()