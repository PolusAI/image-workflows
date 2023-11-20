from polus.plugins.workflows.compute_client.token_service import get_access_token
import requests
import polus.plugins.workflows.utils as utils 
import logging
from pathlib import Path
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

logger = logging.getLogger("polus.plugins.workflows.compute_client")

def submit_workflow(compute_workflow_file: Path):
    token = os.environ.get("ACCESS_TOKEN")
    if token == None :
        logger.debug("""No access token provided. 
                     Requesting new access token.""")
        token = get_access_token()
        # store the token for subsequent requests
        os.environ["ACCESS_TOKEN"] = token 
    else :
        logger.debug("Use existing access token.")

    COMPUTE_URL = os.environ.get("COMPUTE_URL")
    if COMPUTE_URL == None :
        raise Exception(f"COMPUTE_URL env variable not defined.")
        
    headers = {'Authorization': f"Bearer {token}"}

    logger.debug(f"sending to compute : {compute_workflow_file}")
    workflow = utils.load_json(compute_workflow_file)

    url = COMPUTE_URL + '/compute/workflows'
    r = requests.post(url, headers=headers, json = workflow)
    logger.debug(r.status_code)
    logger.debug(r.text)

    if r.status_code == 401:
        # if we fail to authenticate, get rid of stored token
        del os.environ["ACCESS_TOKEN"]