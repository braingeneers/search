build:
	docker compose build

up:
	docker compose up --detach --force-recreate

follow:
	docker compose logs --follow

debug:
	# docker compose --file docker-compose.dev.yml up --build --force-recreate
	docker compose --file docker-compose.dev.yml up --force-recreate

down:
	docker compose down

clean:
	docker compose rm -f -s -v
	docker volume rm mission_control_search-db
	docker network rm mission_control_braingeneers-net

shell:
	docker compose exec \
		--user app --workdir /home/app/code \
		search /bin/bash

ipython-shell:
	docker compose exec \
		--user app --workdir /home/app/code \
		search python -m IPython --no-autoindent

serve:
	flask --app server.py --debug run --host 0.0.0.0 

streamlit:
	streamlit run ui.py --server.port 8888

jupyter:
	# Use URL that it prints to connect to from vscode via select kernel
	jupyter notebook --port=8888 --no-browser --ip=0.0.0.0 --allow-root

# Connect to existing notebook kernel to inspect via command line
jupyter-console:
	jupyter console --existing

list-bucket:
	aws --endpoint https://s3-west.nrp-nautilus.io s3 ls --no-verify-ssl s3://braingeneers

list-inventories:
	aws --endpoint https://s3-west.nrp-nautilus.io s3 ls --no-verify-ssl \
		s3://braingeneers/services/data-lifecycle/aws-inventory/

		s3://braingeneers/2023-04-02-e-hc328_unperturbed/

	2023-04-02-e-hc328_unperturbed
	2023-05-10-e-hc52_18790_unperturbed

list-experiment:
	aws --endpoint https://s3-west.nrp-nautilus.io s3 ls --no-verify-ssl \
		s3://braingeneers/archive/2023-04-02-e-hc328_unperturbed/

mqtt-local:
	docker run --init -it --rm --name mqtt \
	--mount type=bind,source="$(pwd)"/emqx.conf,target=/opt/emqx/etc/emqx.conf \
	--mount type=bind,source="$(pwd)"/emqx.conf,target=/opt/emqx/etc/emqx.conf \
	emqx/emqx:5.1.0

mqtt-cli:
	docker run -it --rm emqx/mqttx-cli

	mqttx conn -h 'braingeneers.gi.ucsc.edu' -p 1883
	mqttx sub -t 'hello' -h 'braingeneers.gi.ucsc.edu' -p 1883
	mqttx pub -t 'hello' -h 'braingeneers.gi.ucsc.edu' -p 1883 -m 'from MQTTX CLI'
