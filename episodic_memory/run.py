#!/usr/bin/env python
from datetime import datetime, timezone
from dotenv import load_dotenv
import random
from typing import Any, Dict
from naptha_sdk.schemas import MemoryRunInput, MemoryDeployment
from naptha_sdk.storage.schemas import CreateStorageRequest, DeleteStorageRequest, ReadStorageRequest
from naptha_sdk.storage.storage_client import StorageClient
from naptha_sdk.user import sign_consumer_id
from naptha_sdk.utils import get_logger
from episodic_memory.schemas import InputSchema

load_dotenv()

logger = get_logger(__name__)

class EpisodicMemory:
    """
    Manages the 'episodic' memory table.
    Each row represents a full 'episode' containing multiple steps.
    """

    def __init__(self, deployment: Dict[str, Any]):
        self.deployment = deployment
        self.config = self.deployment.config
        self.storage_client = StorageClient(self.deployment.node)
        self.storage_type = self.config.storage_config.storage_type
        self.table_name = self.config.storage_config.path
        self.schema = self.config.storage_config.storage_schema

    # TODO: Remove this. In future, the create function should be called by create_module in the same way that run is called by run_module
    async def init(self, *args, **kwargs):
        await create(self.deployment)
        return {"status": "success", "message": f"Successfully populated {self.table_name} table"}

    async def store_episode(self, input_data: Dict[str, Any], *args, **kwargs):
        """
        Insert an entire 'episode' in agent_{agent_id}_episodic.
        """
        logger.info(f"Adding {(input_data)} to table {self.table_name}")
        # If no embedding was provided, derive from the task_query + cognitive steps
        # if episode.embedding is None:
        #     concat_str = f"Task:{episode.task_query} + Steps:{episode.cognitive_steps}"
        #     episode.embedding = self.embedder.get_embeddings(concat_str)

        print("AAAA", input_data)

        # if row has no id, generate a random one
        if 'id' not in input_data:
            input_data['id'] = random.randint(1, 1000000)

        if 'created_at' not in input_data:
            input_data['created_at'] =  str(datetime.now(timezone.utc))

        create_row_result = await self.storage_client.execute(CreateStorageRequest(
            storage_type=self.storage_type,
            path=self.table_name,
            data={"data": input_data}
        ))
        logger.info(f"Create row result: {create_row_result}")

        logger.info(f"Successfully added {input_data} to table {self.table_name}")
        return {"status": "success", "message": f"Successfully added {input_data} to table {self.table_name}"}

    async def get_episodes(self, input_data: Dict[str, Any], *args, **kwargs):
        """
        Retrieve episodes in descending order of created_at.
        """
        logger.info(f"Querying table {self.table_name} with query: {input_data}")

        read_storage_request = ReadStorageRequest(
            storage_type=self.storage_type,
            path=self.table_name,
            options={"conditions": [input_data]}
        )

        read_result = await self.storage_client.execute(read_storage_request)
        print(f"Query results: {read_result}")
        return {"status": "success", "message": f"Query results: {read_result}"}

    async def delete_episodes(self, input_data: Dict[str, Any], *args, **kwargs):
        """
        Delete entire episodes based on optional filters.
        Returns how many rows were deleted.
        """
        delete_row_request = DeleteStorageRequest(
            storage_type=self.storage_type,
            path=self.table_name,
            options={"condition": input_data['condition']}
        )

        delete_row_result = await self.storage_client.execute(delete_row_request)
        logger.info(f"Delete row result: {delete_row_result}")
        return {"status": "success", "message": f"Delete row result: {delete_row_result}"}

    async def delete_table(self, input_data: Dict[str, Any], *args, **kwargs):
        delete_table_request = DeleteStorageRequest(
            storage_type=self.storage_type,
            path=input_data['table_name'],
        )
        delete_table_result = await self.storage_client.execute(delete_table_request)
        logger.info(f"Delete table result: {delete_table_result}")
        return {"status": "success", "message": f"Delete table result: {delete_table_result}"}

# TODO: Make it so that the create function is called when the memory/create endpoint is called
async def create(deployment: MemoryDeployment):
    """
    Create the Episodic Memory table
    Args:
        deployment: Deployment configuration containing deployment details
    """
    storage_client = StorageClient(deployment.node)
    storage_type = deployment.config.storage_config.storage_type
    table_name = deployment.config.storage_config.path
    schema = {"schema": deployment.config.storage_config.storage_schema}

    logger.info(f"Creating {storage_type} at {table_name} with schema {schema}")


    create_table_request = CreateStorageRequest(
        storage_type=storage_type,
        path=table_name,
        data=schema
    )

    # Create a table
    create_table_result = await storage_client.execute(create_table_request)

    logger.info(f"Result: {create_table_result}")
    return {"status": "success", "message": f"Successfully created {table_name}"}


# Default entrypoint when the module is executed
async def run(module_run: Dict):
    module_run = MemoryRunInput(**module_run)
    module_run.inputs = InputSchema(**module_run.inputs)
    episodic_memory = EpisodicMemory(module_run.deployment)
    method = getattr(episodic_memory, module_run.inputs.func_name, None)
    return await method(module_run.inputs.func_input_data)

if __name__ == "__main__":
    import asyncio
    from naptha_sdk.client.naptha import Naptha
    from naptha_sdk.configs import setup_module_deployment
    import os

    naptha = Naptha()

    deployment = asyncio.run(setup_module_deployment("memory", "episodic_memory/configs/deployment.json", node_url = os.getenv("NODE_URL")))

    inputs_dict = {
        "init": {
            "func_name": "init",
            "func_input_data": None,
        },
        "store_episode": {
            "func_name": "store_episode",
            "func_input_data": {
                "memory_id": "123",
                "task_query": "task_query",
                "cognitive_steps": [],
                "total_reward": 0,
                "strategy_update": "strategy_update",
                "metadata": None          
            },
        },
        "get_episodes": {
            "func_name": "get_episodes",
            "func_input_data": {"memory_id": "123"},
        },
        "delete_table": {
            "func_name": "delete_table",
            "func_input_data": {"table_name": "episodic_memory"},
        },
        "delete_episodes": {
            "func_name": "delete_episodes",
            "func_input_data": {"condition": {"memory_id": "123"}},
        },
    }

    module_run = {
        "inputs": inputs_dict["init"],
        "deployment": deployment,
        "consumer_id": naptha.user.id,
        "signature": sign_consumer_id(naptha.user.id, os.getenv("PRIVATE_KEY"))
    }

    response = asyncio.run(run(module_run))

    print("Response: ", response)