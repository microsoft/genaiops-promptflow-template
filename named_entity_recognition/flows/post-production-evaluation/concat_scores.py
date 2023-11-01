from promptflow import tool
import numpy as np

@tool
def concat_score(llm_score: str) -> float:
  try:
    return float(llm_score)
  except:
    return np.nan
