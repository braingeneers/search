FROM python:3.12-bullseye

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
   && apt-get -y install sqlite3 cron libhdf5-dev awscli \
   && apt-get autoremove -y && apt-get clean -y

# Install before code so we don't re-install on every code change
RUN pip install --upgrade pip
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt && rm /tmp/requirements.txt

COPY crawl.cron /etc/cron.d/crawl.cron
RUN chmod 0777 /etc/cron.d/crawl.cron
RUN crontab /etc/cron.d/crawl.cron

WORKDIR /root

COPY . .

CMD ["python main.py"]