from typing import List

from promptflow.core import tool, log_metric
import numpy as np


@tool
def aggregate(concatenated_result: List[str]):
    average_score = round(np.nanmean(concatenated_result), 2)
    if (average_score != np.nan or average_score != 'NaN'):
        log_metric("average_score", average_score)

    return concatenated_result
