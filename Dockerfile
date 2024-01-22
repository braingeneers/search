FROM python:3.12-bullseye

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
   && apt-get -y install sqlite3 \
   && apt-get autoremove -y && apt-get clean -y

WORKDIR /root

COPY . .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["streamlit", "--server.address", "0.0.0.0"] 