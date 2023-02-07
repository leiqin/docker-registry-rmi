#!/usr/bin/python3

import argparse
import subprocess
import json
import requests
import cmd
import collections

CATALOG_URL = 'https://{host}/v2/_catalog'
TAGLIST_URL = 'https://{host}/v2/{name}/tags/list'
DIGEST_URL = 'https://{host}/v2/{name}/manifests/{tag}'

DOCKER_CA_PATH = '/etc/docker/certs.d/{host}/ca.crt'

HELP_TXT = """Dorker Registry rmi. 
You need set `storage.delete.enabled: true` in registry config. 
This program only delete tag, You need run registry gc in registry container delete real file. 
`docker exec <registry-container> registry garbage-collect /etc/docker/registry/config.yml`
"""

session = requests.Session()

def get_username(host, passStore):
    cp = subprocess.run([f"docker-credential-{passStore}", "get"], input=args.host.encode('utf8'), capture_output=True)
    j = json.loads(cp.stdout)
    username = j.get('Username')
    password = j.get('Secret')
    return (username, password)

def get_capath(host):
    return DOCKER_CA_PATH.format(host=host)

def registry_catalog(host):
    res = session.get(CATALOG_URL.format(host=host))
    return res.json()['repositories']

def tags_list(host, name):
    res = session.get(TAGLIST_URL.format(host=host, name=name))
    return res.json()['tags']

def get_digest(host, name, tag):
    res = session.head(DIGEST_URL.format(host=host, name=name, tag=tag), 
            headers={'Accept': 'application/vnd.docker.distribution.manifest.v2+json'})
    return res.headers.get('docker-content-digest')

def rmi(host, name, digest):
    res = session.delete(DIGEST_URL.format(host=host, name=name, tag=digest))
    return res.status_code == 202


class DockerRegistryRMI(cmd.Cmd):

    intro = HELP_TXT
    prompt = 'DRRMI>'
    use_rawinput = True

    def __init__(self, host):
        super().__init__()
        self.host = host

        self.repositories = []
        self.tags = collections.defaultdict(list)

    def do_tree(self, arg):
        'list all repositories and tags'
        self.repositories = registry_catalog(self.host)
        for name in self.repositories:
            print(name)
            tags = tags_list(self.host, name)
            if tags:
                tags.sort()
                self.tags[arg] = tags
                for tag in tags:
                    print(f'    {tag}')

    def do_ls(self, arg):
        'list exists repositories'
        self.repositories = registry_catalog(self.host)
        print(*self.repositories)

    def do_tags(self, arg):
        'list repository tags. TAGS <name>'
        if arg not in self.repositories:
            return
        tags = tags_list(self.host, arg)
        if tags:
            tags.sort()
            self.tags[arg] = tags
        print(*tags)

    def complete_tags(self, text, line, begidx, endidx):
        arr = line.split()
        if len(arr) >= 3:
            return []
        if len(arr) == 2 and len(text) == 0 and line.endswith(' '):
            return []

        last = text if len(arr) == 1 else arr.pop()
        l = filter(lambda s: s.startswith(last), self.repositories)
        i = len(last) - len(text)
        l = map(lambda s: s[i:], l)
        return list(l)

    def do_rmi(self, arg):
        'remove image tag. RMI <name> <tag>...'
        arr = arg.split()
        if len(arr) <= 1:
            return
        name = arr.pop(0)
        for tag in arr:
            digest = get_digest(self.host, name, tag)
            if digest:
                deleted = rmi(self.host, name, digest)
                if deleted:
                    print('rmi', name, tag)

    def complete_rmi(self, text, line, begidx, endidx):
        arr = line.split()
        if len(arr) < 2:
            return self.complete_tags(text, line, begidx, endidx)
        if len(arr) == 2 and not line.endswith(' '):
            return self.complete_tags(text, line, begidx, endidx)

        name = arr[1]
        last = text if len(text) == 0 else arr.pop()
        tags = self.tags.get(name)
        if len(tags) == 0:
            return tags
        l = filter(lambda s: s.startswith(last) and line.find(' {} '.format(s)) == -1, tags)
        i = len(last) - len(text)
        l = map(lambda s: s[i:], l)
        return list(l)

    def do_exit(self, args):
        'exit'
        return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=HELP_TXT)

    parser.add_argument('--host', type=str, required=True, help='docker registry host. host:port')
    parser.add_argument('--username', type=str, required=False, default=None, help='username')
    parser.add_argument('--password', type=str, required=False, default=None, help='password')
    parser.add_argument('--ca-path', type=str, required=False, default=None, help=f'default use {DOCKER_CA_PATH}')
    parser.add_argument('--verify', action=argparse.BooleanOptionalAction, required=False, default=None, help="default use ca-path to requests verify, if you don't want use a ca file, set --verify or --no-verify")
    parser.add_argument('--pass-store', type=str, required=False, default='pass', help='if not give username and password use pass store get it, default use pass')
    args = parser.parse_args()

    if args.username is None or args.password is None:
        username, password = get_username(args.host, args.pass_store)
    else:
        username = args.username
        password = args.password
    session.auth = (username, password)

    if args.verify is not None:
        verify = args.verify
    else:
        if args.ca_path is not None:
            verify = args.ca_path
        else:
            verify = get_capath(args.host)
    session.verify = verify

    DockerRegistryRMI(args.host).cmdloop()

