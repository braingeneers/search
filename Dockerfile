FROM python:3.10-bullseye

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
   && apt-get -y install postgresql-client \
   && apt-get autoremove -y && apt-get clean -y

# Add non-root user
ARG USERNAME=app
RUN groupadd --gid 1000 $USERNAME && \
   useradd --uid 1000 --gid 1000 -m $USERNAME
## Make sure to reflect new user in PATH
ENV PATH="/home/${USERNAME}/.local/bin:${PATH}"
USER $USERNAME

## Pip dependencies
# Upgrade pip
RUN pip install --upgrade pip
# Install production dependencies
COPY --chown=app:1000 requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt && \
   rm /tmp/requirements.txt
# Install development dependencies
# COPY --chown=app:1000 requirements-dev.txt /tmp/requirements-dev.txt
# RUN pip install -r /tmp/requirements-dev.txt && \
#    rm /tmp/requirements-dev.txt