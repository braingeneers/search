FROM python:3.12-bullseye

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
   && apt-get -y install sqlite3 cron \
   && apt-get autoremove -y && apt-get clean -y


# Install before code so we don't re-install on every code change
RUN pip install --upgrade pip
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt && rm /tmp/requirements.txt

WORKDIR /root

COPY . .

RUN echo "* */12 * * * root /usr/local/bin/python crawl.py -c 5 > /proc/1/fd/1 2>/proc/1/fd/2" > /etc/crontab

CMD ["streamlit"]