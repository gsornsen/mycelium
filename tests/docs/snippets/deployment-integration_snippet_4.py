# Source: deployment-integration.md
# Line: 159
# Valid syntax: True
# Has imports: True
# Has assignments: True

import asyncio
from concurrent.futures import ThreadPoolExecutor


async def generate_deployment_async(
    config: MyceliumConfig,
    method: DeploymentMethod
) -> GenerationResult:
    """Generate deployment asynchronously."""
    loop = asyncio.get_event_loop()

    def _generate():
        generator = DeploymentGenerator(config)
        return generator.generate(method)

    # Run in thread pool to avoid blocking
    with ThreadPoolExecutor() as executor:
        result = await loop.run_in_executor(executor, _generate)

    return result

# Usage with FastAPI
from fastapi import BackgroundTasks, FastAPI

app = FastAPI()

@app.post("/deploy/{project_name}")
async def create_deployment(
    project_name: str,
    config: dict,
    background_tasks: BackgroundTasks
):
    """API endpoint to generate deployment."""
    # Validate config
    mycelium_config = MyceliumConfig(
        project_name=project_name,
        **config
    )

    # Generate asynchronously
    result = await generate_deployment_async(
        mycelium_config,
        DeploymentMethod.DOCKER_COMPOSE
    )

    return {
        "success": result.success,
        "output_dir": str(result.output_dir),
        "files": [str(f) for f in result.files_generated]
    }
