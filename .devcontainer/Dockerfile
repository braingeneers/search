FROM mcr.microsoft.com/vscode/devcontainers/python:3.10-bullseye

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
   && apt-get -y install postgresql-client \
   && apt-get autoremove -y && apt-get clean -y
