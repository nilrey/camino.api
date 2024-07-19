#!/bin/bash
docker stop cdockerapi
docker build -t idockerapi .
docker run -d --rm --name cdockerapi -p 8002:80  -v /var/run/docker.sock:/var/run/docker.sock  -v /home/sadmin/Work/dockermanager:/code/api/docker/hostpipe idockerapi