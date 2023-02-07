# docker-registry-rmi

A script delete private docker registry images

You need set `storage.delete.enabled: true` in registry config. 

This program only delete tag, 
You need run registry gc in registry container delete real file. 

    docker exec <registry-container> registry garbage-collect /etc/docker/registry/config.yml

### Usage

    docker_registry_rmi.py --host <host:port>

    DRRMI>help
    DRRMI>tree
    DRRMI>ls
    DRRMI>tags <name> 
    DRRMI>rmi <name> <version>...
    DRRMI>exit

Default will use `/etc/docker/certs.d/{host}/ca.crt` ca file, 
You can set it by `--ca-path` or disable ca file by `--verify` or `--no-verify`

Default will get username and password from docker-credential-pass, 
You can change it use `--pass-store=secretservice`, 
or set `--username` and `--password` in cmdline
