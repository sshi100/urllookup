
check:
	@if [ "x$(DOCKER_ORG_ID)" = "x" ]; then\
		echo "No DOCKER_ORG_ID defined";\
		exit 1;\
    fi
	@echo "docker org id: $(DOCKER_ORG_ID)"

build: check
	cd docker; \
	sed 's/sshi100/$(DOCKER_ORG_ID)/g' docker-compose.yaml > docker-compose-tmp.yaml; \
	docker-compose build

push: build
	@cd docker && docker-compose -f docker-compose-tmp.yaml push

local-run:
	@cd docer && docker-compose up -f docker-compose-tmp.yaml

k8s-run: push
	cd docker; \
	kubectl delete namespace urllookup; \
	kubectl create namespace urllookup; \
	kompose convert -f docker-compose-tmp.yaml --controller deployment --volumes configMap -o /tmp/k8s-tmp.yaml; \
	kubectl -n urllookup apply -f /tmp/k8s-tmp.yaml
	kubectl -n urllookup delete deployment/job
	kubectl -n urllookup apply -f job-deployment-k8s.yaml
