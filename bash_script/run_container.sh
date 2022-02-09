#!/bin/bash

docker run -v "${PWD}":/app/fotos -t --rm mosaico_docker

for i in `ls`
do 
    sudo chmod 777 $i
done
