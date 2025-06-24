from fastapi import FastAPI
from api.routes import projects
# from api.routes import docker
from api.routes import docker_images
from api.routes import docker_containers
from api.routes import ann
from api.routes import virtual_machines
from api.routes import videos
from api.settings.metadata_fastapi import tags_metadata


app = FastAPI( openapi_tags = tags_metadata )

app.include_router(projects.router_projects)

# app.include_router(docker.router_docker)

app.include_router(docker_images.router_images)

app.include_router(docker_containers.router_containers)

app.include_router(ann.router_ann)

app.include_router(virtual_machines.router_vm)

app.include_router(videos.router_video)
