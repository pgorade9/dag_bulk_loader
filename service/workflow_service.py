import asyncio
import json
import logging
import sys
import time
import types
import uuid

import aiohttp
import requests
from aiohttp import TraceConfig
from aiohttp_retry import RetryClient, ExponentialRetry
from sqlmodel import Session, select

from configuration import keyvault
from data.database import LoadTest
from models.datamodels import TestDetails
from utils.crud import get_run_count_for_test_id

handler = logging.StreamHandler(sys.stdout)
logging.basicConfig(handlers=[handler])
logger = logging.getLogger(__name__)
statuses_for_retry = {x for x in range(100, 600)}
statuses_for_retry.remove(200)
retry_options = ExponentialRetry(attempts=4, statuses=statuses_for_retry)

actual = 0


def get_token(env):
    response = requests.request(method="POST",
                                url=keyvault[env]["token_url"],
                                headers={"content-type": "application/x-www-form-urlencoded"},
                                data=f"grant_type=client_credentials&client_id={keyvault[env]["client_id"]}&client_secret={keyvault[env]["client_secret"]}&scope={keyvault[env]["scope"]}")

    if response.status_code == 200:
        print(f"********* Token Generated Successfully ************")
        response_dict = json.loads(response.text)
        return "Bearer " + response_dict["access_token"]
    else:
        print(f"Error occurred while creating token. {response.text}")
        exit(1)


def create_workflow_payload(env, dag):
    random_uuid = str(uuid.uuid4())  # without string conversion uuid returns dict giving JSON Type Error
    payload = {"runId": random_uuid, "executionContext": {}}
    payload["executionContext"]["dataPartitionId"] = keyvault[env]["data_partition_id"]
    payload["executionContext"]["id"] = keyvault[env]["file_id"][dag]
    # print(f"workflow {payload=}")
    return payload


async def on_request_start(
        session: aiohttp.ClientSession,
        trace_config_ctx: types.SimpleNamespace,
        params: aiohttp.TraceRequestStartParams
) -> None:
    current_attempt = trace_config_ctx.trace_request_ctx['current_attempt']
    if current_attempt > 1:
        logger.warning(f"We are in attempt {current_attempt}")
    if retry_options.attempts <= current_attempt:
        logger.warning('Wow! We are in last attempt')


async def trigger_workflow(env, dag_name, token, retry_options, test_id, session: Session):
    TIME_OUT = 1500
    global actual
    print("Triggering_workflow")

    workflow_url = f"{keyvault[env]["seds_dns_host"]}/api/workflow/v1/workflow/{dag_name}/workflowRun"
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'data-partition-id': keyvault[env]["data_partition_id"],
        'Authorization': token
    }
    payload = create_workflow_payload(env, dag_name)

    trace_config = TraceConfig()
    trace_config.on_request_start.append(on_request_start)
    retry_client = RetryClient(retry_options=retry_options, trace_configs=[trace_config])
    response = await retry_client.post(workflow_url, headers=headers, data=json.dumps(payload), timeout=TIME_OUT,
                                       retry_options=retry_options)
    json_response = await response.json()
    print(json_response)
    await retry_client.close()
    if response.status == 200:
        actual += 1
        print(f"{actual}: Workflow Run ID = {json_response['runId']}")
        test_unit = LoadTest(test_id=test_id,
                             correlation_id=response.headers['correlation-id'],
                             run_id=json_response['runId'],
                             submitted_timestamp=json_response['startTimeStamp'],
                             workflow_name=json_response['workflowId'],
                             env_name=env)
        print(test_unit)
        # results = session.exec(select(LoadTest)).all()
        # for result in results:
        #     print("*****************************")
        #     print(result)
        session.add(test_unit)
        session.commit()
        session.refresh(test_unit)
        # with Session(engine) as session1:
        #     session1.add(test_unit)
        #     session1.commit()
        #     session1.refresh(test_unit)


async def async_workflow(env, dag_name, count, test_id, session: Session):
    token = get_token(env)
    tasks = [trigger_workflow(env, dag_name, token, retry_options, test_id, session) for _ in range(count)]
    await asyncio.gather(*tasks)


async def sleep():
    await asyncio.sleep(1)


def load(env, dag, count, session: Session):
    start_time = time.time()
    ######## Using Asyncio ###############
    envs_ltops = ["evd-ltops", "evt-ltops", "prod-canary-ltops", "prod-aws-ltops", "prod-qanoc-ltops"]
    dags_ltops = ["csv_parser_wf_status_gsm", "wellbore_ingestion_wf_gsm", "doc_ingestor_azure_ocr_wf",
                  "shapefile_ingestor_wf_status_gsm"]

    test_id = str(uuid.uuid4())
    # count = 1
    batch_size = 1

    batches = int(count / batch_size)
    for i in range(0, batches):
        asyncio.run(async_workflow(env, dag, batch_size, test_id, session))

    end_time = time.time()
    print(f"Net Time = {end_time - start_time}")
    return {"trigger": "success", "test_id": test_id}


async def workflow_status(aio_session, env, dag_name, test_record, token, session: Session):
    run_id = test_record.run_id
    print(f"Fetching Workflow status of {run_id=} for {dag_name=} on {env=}")
    data_partition_id = keyvault[env]["data_partition_id"]

    workflow_url = f"{keyvault[env]["seds_dns_host"]}/api/workflow/v1/workflow/{dag_name}/workflowRun/{run_id}"
    headers = {'data-partition-id': data_partition_id,
               'Content-Type': 'application/json',
               'Authorization': token,
               }
    try:
        async with aio_session.get(workflow_url, headers=headers) as response:
            json_response = await response.json()
            print(json_response)
            if response.status == 200 and json_response['status'] in ['success', 'failed']:
                # record = session.exec(select(LoadTest).where(LoadTest.run_id == run_id)).first()
                test_record.success_timestamp = json_response['endTimeStamp'] if json_response[
                                                                                     'status'] == 'success' else None
                test_record.failed_timestamp = json_response['endTimeStamp'] if json_response[
                                                                                    'status'] == 'failed' else None
                session.add(test_record)
                session.commit()
                session.refresh(test_record)
                return json_response['status']
            else:
                print(f"Run-Id: {run_id}: Response status code unchanged = {response.status}")
                print("Please wait !!")
    except Exception as e:
        print(f"Error occurred while fetching WORKFLOW status for {run_id}")
        print(f"Error: {e}")


async def async_status(test_id, session: Session):
    print("I am in async status")
    test_record = session.exec(select(LoadTest).where(LoadTest.test_id == test_id)).first()
    env = test_record.env_name
    dag_name = test_record.workflow_name
    tests = session.exec(select(LoadTest).where(LoadTest.test_id == test_id)
                         .where(LoadTest.success_timestamp.is_(None))
                         ).all()
    for test in tests:
        print(test.run_id)
        print(f"{test.success_timestamp is None}")

    async with aiohttp.ClientSession() as aio_session:
        token = get_token(env)
        tasks = [workflow_status(aio_session, env, dag_name, test, token, session) for test in tests]
        return await asyncio.gather(*tasks)


def get_test_details(test_id, session):
    test_record = session.exec(select(LoadTest).where(LoadTest.test_id == test_id)).first()
    test_details = TestDetails(env=test_record.env_name,
                               workflow_name=test_record.workflow_name,
                               trigger_timestamp=test_record.submitted_timestamp,
                               run_count=get_run_count_for_test_id(test_id, session))

    return test_details
