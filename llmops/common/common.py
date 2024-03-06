import logging
import time

from promptflow.entities import Run


def wait_job_finish(job: Run, logger: logging.Logger):
    """
    Wait for job to complete/finish

    :param job: The prompt flow run object.
    :type job: Run
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
