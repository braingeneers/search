FROM python:3.10-bullseye

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
   && apt-get -y install postgresql-client \
   && apt-get autoremove -y && apt-get clean -y

# Add non-root user
ARG USERNAME=app
RUN groupadd --gid 1000 $USERNAME && \
   useradd --uid 1000 --gid 1000 -m $USERNAME
ENV PATH="/home/${USERNAME}/.local/bin:${PATH}"
USER $USERNAME

RUN pip install --upgrade pip
COPY --chown=app:1000 requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt && \
   rm /tmp/requirements.txt

WORKDIR /home/${USERNAME}

COPY . code

# CMD ["flask", "--app", "code/server.py", "run", "--host", "0.0.0.0"] 

CMD ["streamlit", "--server.address", "0.0.0.0", "--server.port", "5000"] 