FROM python:3.10.12

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

RUN pip install fastapi uvicorn

RUN pip install loguru

COPY ./api /code/api

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "80"]

VOLUME ["/code/api/docker/hostpipe"]

# CREATE VOLUME: ./scripts/host /code/scripts/host

# CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

#CMD ["uvicorn", "api.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "8001"]