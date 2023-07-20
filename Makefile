up:
	docker compose up --build --force-recreate

shell:
	docker compose exec \
		--user app --workdir /home/app/code \
		app /bin/bash

list-bucket:
	aws --endpoint https://s3-west.nrp-nautilus.io s3 ls --no-verify-ssl s3://braingeneers

list-inventories:
	aws --endpoint https://s3-west.nrp-nautilus.io s3 ls --no-verify-ssl \
		s3://braingeneers/services/data-lifecycle/aws-inventory/
