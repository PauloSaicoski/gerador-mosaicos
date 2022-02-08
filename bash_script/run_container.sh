#!/bin/bash

docker run -v "${PWD}":/app/fotos -t --rm mosaico_docker
