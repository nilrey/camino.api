# docker create --name cdockerapi -p 8002:80  -v /var/run/docker.sock:/var/run/docker.sock idockerapi

FROM python:3.10.12

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

RUN pip install fastapi uvicorn

RUN apt-get update && apt-get install -y docker.io

COPY ./api /code/api

#VOLUME [ "/code/export", "/code/weights" ]

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "80"]
