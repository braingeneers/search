docker-build:
	docker build -t $(USER)/search .

docker-run:
	docker run -it --rm \
	--user $(id -u):$(id -g) \
	--workdir /app \
	--volume $(PWD):/app \
	$(USER)/search /bin/bash

docker-compose-prune:
	docker compose rm --stop --volumes

build:
	docker-compose build

up:
	docker-compose -p $(USER) up --force-recreate

down:
	docker-compose -p $(USER) down --volumes

list-bucket:
	aws --endpoint https://s3-west.nrp-nautilus.io s3 ls --no-verify-ssl s3://braingeneers

list-inventories:
	aws --endpoint https://s3-west.nrp-nautilus.io s3 ls --no-verify-ssl \
		s3://braingeneers/services/data-lifecycle/aws-inventory/
