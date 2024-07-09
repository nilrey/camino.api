# docker create --name cdockerapi -p 8002:80  -v /var/run/docker.sock:/var/run/docker.sock -v /home/sadmin/Work/dockermanager:/code/api/docker/hostpipe idockerapi

FROM python:3.10.12

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

RUN pip install fastapi uvicorn

RUN pip install loguru

RUN apt-get update && apt-get install -y docker.io

COPY ./api /code/api

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "80"]

VOLUME ["/var/run/docker.sock","/code/api/docker/hostpipe"]

# CREATE VOLUME: ./scripts/host /code/scripts/host

# CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

#CMD ["uvicorn", "api.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "8001"]
