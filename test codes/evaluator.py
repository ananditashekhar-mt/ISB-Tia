from agent_brain import langgraph_agent
from data_loader import load_dataset


def run_langgraph_benchmark():
  _, _, _, support_df, _ = load_dataset()
  total = len(support_df)
  correct = 0

  print(f"--- Running LangGraph Benchmark on {total} Cases ---")

  for idx, row in support_df.iterrows():
    initial_state = {
        "message": str(row["Customer_Message"]),
        "order_id": "ORD-10006",
        "session_id": f"benchmark_{idx}",
    }
    output = langgraph_agent.invoke(initial_state)

    if output["intent"] in str(row["Intent"]):
      correct += 1

  acc = (correct / total) * 100
  print(f"Benchmark Complete!")
  print(f"Accuracy: {acc:.2f}% ({correct}/{total} cases passed)")
  return acc


if __name__ == "__main__":
  run_langgraph_benchmark()