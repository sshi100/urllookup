
check:
	@if [ "x$(DOCKER_ORG_ID)" = "x" ]; then\
		echo "No DOCKER_ORG_ID defined";\
		exit 1;\
    fi
	@echo "docker org id: $(DOCKER_ORG_ID)"

build: check
	cd docker; \
	docker-compose build

push: build
	@cd docker && docker-compose -f docker-compose-tmp.yaml push

local-run:
	@cd docker && docker-compose up -f docker-compose-tmp.yaml

k8s-run:
	cd docker; \
	kubectl delete namespace urllookup; \
	kubectl create namespace urllookup; \
	sed 's/sshi100/$(DOCKER_ORG_ID)/g' docker-compose.yaml > docker-compose-tmp.yaml; \
	/usr/local/bin/kompose convert -f docker-compose-tmp.yaml --volumes configMap -o /tmp/k8s-tmp.yaml; \
	kubectl -n urllookup apply -f /tmp/k8s-tmp.yaml
	kubectl -n urllookup delete deployment/job
	kubectl -n urllookup apply -f job-deployment-k8s.yaml
