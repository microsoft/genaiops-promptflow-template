import ast
import logging
import os
import time

from promptflow.entities import Run


def wait_job_finish(job: Run, logger: logging.Logger):
    """
    Wait for job to complete/finish

    :param job: The prompt flow run object.
    :type job: Run
    :param logger: The used logger.
    :type logger: logging.Logger
    :raises Exception: If job not finished after 3 attempts with 5 second wait.
    """
    max_tries = 3
    attempt = 0
    while attempt < max_tries:
        logger.info(
            "\nWaiting for job %s to finish (attempt: %s)...",
            job.name,
            str(attempt + 1),
        )
        time.sleep(5)
        if job.status in ["Completed", "Finished"]:
            return
        attempt = attempt + 1

    raise Exception("Sorry, exiting job with failure..")


def resolve_run_ids(run_id: str) -> list[str]:
    """
    Read run_id from string or from file.

    :param run_id: List of run IDs (example '["run_id_1", "run_id_2", ...]') OR path to file containing list of run IDs.
    :type run_id: str
    :return: List of run IDs.
    :rtype: List[str]
    """
    if os.path.isfile(run_id):
        with open(run_id, "r") as run_file:
            raw_runs_ids = run_file.read()
            run_ids = [] if raw_runs_ids is None else ast.literal_eval(raw_runs_ids)
    else:
        run_ids = [] if run_id is None else ast.literal_eval(run_id)

    return run_ids
