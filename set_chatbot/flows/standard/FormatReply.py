from promptflow import tool

@tool
def format_reply(reply: str) -> str:
  reply = clean_markdown(reply)
  return reply

def clean_markdown(input: str) -> str:
  start = 0
  inBlock = False
  result = ""
  while True:
    nextStart = input.find("```", start)
    if nextStart == -1:
      break
    result += input[start:nextStart]
    if inBlock:
      if nextStart > 0 and input[nextStart - 1] != '\n':
        result += "\n"
      result += "```\n"
      inBlock = False
    else:
      result += "```"
      inBlock = True
    start = nextStart + 3
  result += input[start:]
  if inBlock:
    result += "```"
  return result
