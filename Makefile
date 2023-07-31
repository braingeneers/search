up:
	docker compose up --detach --force-recreate

down:
	docker compose down

clean:
	docker compose rm -f -s -v
	docker volume rm $(USER)-braingeneers-search_postgres

debug:
	docker compose up --build --force-recreate

shell:
	docker compose exec \
		--user app --workdir /home/app/code \
		app /bin/bash

serve:
	flask --app server.py --debug run --host 0.0.0.0 

list-bucket:
	aws --endpoint https://s3-west.nrp-nautilus.io s3 ls --no-verify-ssl s3://braingeneers

list-inventories:
	aws --endpoint https://s3-west.nrp-nautilus.io s3 ls --no-verify-ssl \
		s3://braingeneers/services/data-lifecycle/aws-inventory/

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