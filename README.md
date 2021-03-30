# **URL Lookup Service**

There is an HTTP proxy that is scanning traffic looking for malware URLs. Before allowing HTTP connections to be made, this proxy asks a service that maintains several databases of malware   URLs if the resource being requested is known to contain malware. Write a small web service, that responds to GET requests where the caller passes in a URL and the service responds with some information about that URL. The GET requests look like this:

   ```GET /urlinfo/1/{hostname_and_port}/{original_path_and_query_string}```

The caller wants to know if it is safe to access that URL or not. As the implementer you get to choose the response format and structure. These lookups are blocking users from accessing the URL until the caller receives a response from your service. The service must be containerized.

Give some thought to the following:
1. The size of the URL list could grow infinitely, how might you scale this beyond the memory capacity of this VM?
2. The number of requests may exceed the capacity of this VM, how might you solve that?
3. What are some strategies you might use to update the service with new URLs? Updates may be as much as 5 thousand URLs a day with updates arriving every 10 minutes.

## **Proposal**

- For #1, put URL list in a memory data store, where can be persistent and scalable
- For #2, introducing scalable architecture with `Load Balancer -> Web Lookup Cluster -> Data Store Cluster <- Updater <- Scheduled Job`.
- For #3, use another backend job to do batch update every 10 minutes for new URLs.


## **Solution**

- Take python based FastAPI framework (https://fastapi.tiangolo.com/), reasons:
  - fast: saying high performance with async support, can be compared with Golang and NodeJS
  - community: a lot of projects, plugins
  - integration: easy to connect with redis and database etc. fully leverage exisiting Python stuffs
  - modern: designed for RESTful web service, with mordern openAPI, can be used to take over Django and Flask 

- Take docker based infrastructure, with:
  - nginx as Load Balancer to direct traffics to Web
  - redis as Data Store to store URL blacklist
  - docker composer
  - docker swarm cluster


# **Deployment**

## **To Docker Swarm**
Use docker compose and swarm to create this application stack.

1. checkout code from https://github.com/sshi100/urllookup

2. build and deploy
  run ```make local-run```

3. service validate
  run `curl http://127.0.0.1/`, it should return `{"ping":"PONG"}`

Now, the stack has been deployed successfully, and confirm with `docker service list`:
  ```
ID             NAME                     MODE         REPLICAS   IMAGE                  PORTS
iwnj2x3iz3d2   urllookup_datastore1     replicated   1/1        redis:latest
wvt4n7c9fd9j   urllookup_datastore2     replicated   1/1        redis:latest
lei17vm1gurq   urllookup_datastore3     replicated   1/1        redis:latest
kokfai41tpkm   urllookup_job            replicated   1/1        ofelia:latest
wapn4p3biv7l   urllookup_loadbalancer   replicated   1/1        nginx:alpine           *:80->80/tcp
81ndumrl6rud   urllookup_lookup         replicated   2/2        lookupservice:latest   *:8081->8081/tcp
kcilbdyxrzyh   urllookup_updater        replicated   1/1        updater:latest         *:8082->8082/tcp
  ```

*Note: to re-deploy the services, you may run `docker stack rm urllookup` and for debugging you may run `docker service logs service`.

For more detailed information about docker swarm deployment, please check https://docs.docker.com/get-started/swarm-deploy/  

## **To Kubernetes**
Use kocompose to convert docker-compose file to kubernetes compatible configuration.

Supposing you already have a Kubernetes cluster running under minikube/kind or public cloud, you can deploy in two ways:

1. from local
```make k8s-deploy-from-local```

2. from CircleCI
Please set the following enironment variables in your CircleCI project:
```
DOCKER_ORG_ID
DOCKERHUB_USER
DOCKERHUB_PASSWORD	
KUBECONFIG_DATA
```
in which, KUBECONFIG_DATA can be retrieved by running:
`k8 config view --minify --flatten | base64`


With either way, once done, confirm with `kubernetes -n urllookup get pods`:
```
NAME                            READY   STATUS      RESTARTS   AGE
datastore1-77876fb8d9-scm2q     1/1     Running     0          52m
datastore2-6f5dfb5c7c-zvlw6     1/1     Running     0          52m
datastore3-6d48c9b6bd-rb5lq     1/1     Running     0          52m
job-1617060600-hjk5c            0/1     Completed   0          14m
job-1617060900-sdgcj            0/1     Completed   0          9m36s
job-1617061200-bndnv            0/1     Completed   0          4m35s
loadbalancer-85db7977b7-75ggl   1/1     Running     0          52m
lookup-6b44ff5485-pt6j6         1/1     Running     0          52m
lookup-6b44ff5485-x7892         1/1     Running     0          52m
updater-5c9c887745-tt2x9        1/1     Running     0          52m
```

You may expose for local laptop access:
```kubectl -n urllookup port-forward service/loadbalancer 8080:80```

and confirm with `curl http://127.0.0.1:8080/`, it should return `{"ping":"PONG"}`


## **Stack insight**

Components:
  - urllookup_loadbalancer(1): load balancer service (by nginx), fast to dispatch to lookup services
  - urllookup_lookup(2): lookup service (by application cluster in python fastapi), to get data from data store service cluster
  - urllookup_datastore(3): data store service (by redis cluster, datastore1 is the master), to store more data in memory for quick response and persistent in disk
  - urllookup_updater(1): update service to update data store based on provided default or customized URL blacklist
  - urllookup_job(1): cronjob to monitor `arriving` blacklist and apply the changes every 5 minutes

Relationship: 
`Load Balancer -> Web Lookup Cluster -> Data Store Cluster <- Updater <- Scheduled Job`


# **Usage**

## **URL lookup**

To check if a URL is safe or not, follow `/urlinfo/1/<domain>/<path>` as below:
  - ```curl http://localhost/urlinfo/1/google.bad/item1.html``` which will return `{"is_safe": false}`


## **Blacklist update**
Provide two RESTful APIs `/urlupdate/` and `/urlupdate_batch/` for blacklist update.

The `job` service is configured to send `/urlupdate_batch/1/archiving` request to `updater` service every 5 minutes.

Note: it is confirmed that it takes around 0.6 seconds to get 1000 URL items into data store (redis).

If you are interested in manual access, you can:
- To add a single URL to blacklist:
  - ```curl -X POST localhost/urlupdate/1/default/google.bad/item1.html```

- To do a batch URL update on default blacklist (data/blacklist/default.txt):
  - ```curl -X POST localhost/urlupdate_batch/1/default```

- To do a batch URL with a customized blacklist, create a new blacklist file as `mylist.txt` and put it into folder `data/blacklist`, and run:
  - ```curl -X POST localhost/urlupdate_batch/1/mylist```



# **TODO**
- deploy as Service Mesh
