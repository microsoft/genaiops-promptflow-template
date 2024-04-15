from promptflow import tool

@tool
def format_conversation(history: list, maxTokens: int) -> str:
  result = ""
  conversation_history = []
  for history_item in history:
      conversation_history.append({
          "speaker": "user",
          "message": history_item["inputs"]["query"]
      })
      conversation_history.append({
          "speaker": "assistant",
          "message": history_item["outputs"]["reply"]
      })
  
  # Start using context from history, starting from most recent, until token limit is reached.
  for turn in reversed(conversation_history):
    turnStr = format_turn(turn["speaker"], turn["message"])
    newResult = turnStr + result
    if estimate_tokens(newResult) > maxTokens:
      break
    result = newResult
  return result

def format_turn(speaker: str, message: str) -> str:
  return f"{speaker}:\n{message}\n"

def estimate_tokens(text: str) -> int:
  return (len(text) + 2) / 3
