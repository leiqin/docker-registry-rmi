# docker-registry-rmi

A script delete private docker registry images

You need set `storage.delete.enabled: true` in registry config. 

This program only delete tag, 
You need run registry gc in registry container delete real file. 

    docker exec <registry-container> registry garbage-collect /etc/docker/registry/config.yml

