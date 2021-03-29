
check:
	@if [ "x$(DOCKER_ORG_ID)" = "x" ]; then\
		echo "No DOCKER_ORG_ID defined";\
		exit 1;\
    fi
	@echo "docker org id: $(DOCKER_ORG_ID)"
	cd docker; \
	sed 's/sshi100/$(DOCKER_ORG_ID)/g' docker-compose.yaml > docker-compose-tmp.yaml; \
	sed 's/sshi100/$(DOCKER_ORG_ID)/g' docker-compose-k8s.yaml > docker-compose-k8s-tmp.yaml

local-run: check
	cd docker; \
	docker-compose -f docker-compose-tmp.yaml build; \
	docker-compose -f docker-compose-tmp.yaml push; \
	docker swarm init; \
	docker stack deploy --compose-file docker-compose-tmp.yaml urllookup; \

remote-push:
	cd docker; \
	docker-compose -f docker-compose-k8s-tmp.yaml build; \
	docker-compose -f docker-compose-k8s-tmp.yaml push

k8s-prep: check
	cd docker; \
	kubectl create namespace urllookup; \
	kompose convert -f docker-compose-k8s-tmp.yaml --controller deployment --volumes configMap -o /tmp/k8s-tmp.yaml;

k8s-deploy-from-local: k8s-prep remote-push
	cd docker; \
	kubectl -n urllookup apply -f /tmp/k8s-tmp.yaml
	kubectl -n urllookup apply -f job-deployment-k8s.yaml
