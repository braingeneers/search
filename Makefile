up:
	docker compose up --detach --build --force-recreate

down:
	docker compose down

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
