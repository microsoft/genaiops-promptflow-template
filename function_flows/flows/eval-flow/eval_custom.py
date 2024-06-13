import json

from typing import TypedDict
from pathlib import Path

from jinja2 import Template

from promptflow.tracing import trace
from promptflow.core import AzureOpenAIModelConfiguration
from promptflow.core._flow import Prompty
from promptflow.evals.evaluate import evaluate
from promptflow.evals.evaluators import  SimilarityEvaluator
from function_flows.flows.basic.programmer import write_simple_program

def eval_use_case(run_name, data_id, column_mapping):
    print("Implement your custom evaluation here")
    print("invoke evaluate function withe valuators and evaluator_config")
    print("from promptflow.evals.evaluate import evaluate")
    print("from promptflow.evals.evaluators import  SimilarityEvaluator")
