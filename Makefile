build:
	docker compose build

up:
	docker compose up --detach --force-recreate

follow:
	docker compose logs --follow

debug:
	docker compose --file docker-compose.dev.yml up --force-recreate

down:
	docker compose down

clean:
	docker compose rm -f -s -v
	docker volume rm -f mission_control_search-db
	docker network rm -f mission_control_braingeneers-net

shell:
	docker compose exec \
		search /bin/bash
		# --user app --workdir /home/app/code \

sqlite-init:
	rm data/braingeneers.db
	sqlite3 -init create.sql data/braingeneers.db .quit

sqlite-console:
	# Shell using the installed sqlite3 vs. systems version
	$$(brew --prefix)/opt/sqlite/bin/sqlite3 data/braingeneers.db

streamlit:
	streamlit run app.py \
		--browser.gatherUsageStats=False \
		--client.toolbarMode="auto" \
		--logger.level="info"

list-bucket:
	aws --endpoint https://s3-west.nrp-nautilus.io s3 ls s3://braingeneers

list-experiment:
	aws --endpoint https://s3-west.nrp-nautilus.io --profile prp-braingeneers \
		s3 ls s3://braingeneers/ephys/2022-04-24-e-connectoids-chip11350/

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