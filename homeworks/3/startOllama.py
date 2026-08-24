import docker

CONTAINER_NAME = "ollama"
IMAGE_NAME = "ollama/ollama"
PORT = 11434

client = docker.from_env()

try:
    container = client.containers.get(CONTAINER_NAME)

    if container.status != "running":
        container.start()
        print("Ollama container started")
    else:
        print("Ollama container is already running")

except docker.errors.NotFound:
    container = client.containers.run(
        IMAGE_NAME,
        name=CONTAINER_NAME,
        ports={"11434/tcp": PORT},
        detach=True,
    )

    print("Ollama container created and started")