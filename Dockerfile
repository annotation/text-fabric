FROM python:3.11

WORKDIR /var/text-fabric

ADD MANIFEST.in setup.cfg pyproject.toml .
ADD tf/ tf/

ENTRYPOINT bash
