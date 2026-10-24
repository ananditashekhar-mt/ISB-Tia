from agent_brain import langgraph_agent
from data_loader import load_dataset
from logger import get_chat_history
import streamlit as st

st.set_page_config(layout="wide", page_title="LangGraph Post-Purchase Support")
st.title("🤖 LangGraph Apparel Agent Studio")

policies_df, catalog_df, orders_df, support_df, _ = load_dataset()

tab1, tab2, tab3 = st.tabs(
    ["💬 LangGraph Chat", "🧠 Memory & SQLite History", "📊 Dataset Explorer"]
)

# TAB 1: CHAT INTERFACE
with tab1:
  col1, col2 = st.columns([2, 1])

  with col2:
    st.subheader("Context Selector")
    selected_order = st.selectbox(
        "Select Order ID:", orders_df["Order_ID"].tolist()[:20]
    )
    sel = orders_df[orders_df["Order_ID"] == selected_order].iloc[0]
    st.write(f"**Customer:** {sel['Customer_Last_Name']}")
    st.write(f"**Item:** {sel['Product_Name']}")
    st.write(f"**Status:** `{sel['Order_Status']}`")

    session_id = st.text_input("Session Thread ID:", value="session_demo_1")

  with col1:
    st.subheader("Customer Interaction")

    history = get_chat_history(session_id)
    for msg in history:
      with st.chat_message(msg["role"]):
        st.write(msg["content"])

    if user_query := st.chat_input("Type customer question..."):
      with st.chat_message("user"):
        st.write(user_query)

      state_input = {
          "message": user_query,
          "order_id": selected_order,
          "session_id": session_id,
      }
      final_state = langgraph_agent.invoke(state_input)

      with st.chat_message("assistant"):
        st.write(final_state["response"])
        if final_state["escalated"]:
          st.error(
              f"⚠️ Escalated to Human: {final_state['escalation_reason']}"
          )

# TAB 2: SQLITE MEMORY VIEW
with tab2:
  st.subheader("💾 Persistent Chat History (`runtime.sqlite`)")
  st.dataframe(get_chat_history(session_id))

# TAB 3: DATASET
with tab3:
  st.subheader("Orders")
  st.dataframe(orders_df.head(10))
  st.subheader("Policies")
  st.dataframe(policies_df)