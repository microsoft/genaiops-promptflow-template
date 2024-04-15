from promptflow import tool

@tool
def extract_intent(input: str, query: str) -> str:
  entries = None
  if 'Single Intents:' in input:
    entries = input.split('Single Intents:', 2)
  elif 'Single Intent:' in input:
    entries = input.split('Single Intent:', 2)
  
  if entries and len(entries) == 2:
    return {
      "current_message_intent": entries[0].strip(),
      "search_intents": entries[1].strip()
    }
  return {
      "current_message_intent": query,
      "search_intents": query
  }
