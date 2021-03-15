# **URL Lookup Service**

There is an HTTP proxy that is scanning traffic looking for malware URLs. Before allowing HTTP connections to be made, this proxy asks a service that maintains several databases of malware   URLs if the resource being requested is known to contain malware. Write a small web service,   in the language/framework your choice, that responds to GET requests where the caller passes   in a URL and the service responds with some information about that URL. The GET requests look   like this:

```GET /urlinfo/1/{hostname_and_port}/{original_path_and_query_string}```

The caller wants to know if it is safe to access that URL or not. As the implementer you get to choose the response format and structure. These lookups are blocking users from accessing the URL until the caller receives a response from your service. The service must be containerized.

Give some thought to the following:
1. The size of the URL list could grow infinitely, how might you scale this beyond the memory capacity of this VM?
2. The number of requests may exceed the capacity of this VM, how might you solve that?
3. What are some strategies you might use to update the service with new URLs? Updates may be as much as 5 thousand URLs a day with updates arriving every 10 minutes.

## **Proposal**

For #1, put URL list in a memory data store, where can be persistent and scalable
For #2, introducing 3-layered scalable architecture with Load Balancer <-> Web Lookup Cluster <-> Data Store Cluster.
For #3, use another backend job to do batch update every 10 minutes for new URLs.


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


## **Installation**

1. checkout code from https://github.com/sshi100/urllookup
2. build and deploy
  - ```cd docker; docker-compose build; docker swarm init; docker stack deploy --compose-file docker-compose.yml urllookup```
  - ```docker service list```
3. check
  - ```curl http://127.0.0.1/```


## **URL lookup**
  - ```curl http://localhost/urlinfo/1/updat120.clanteam.com/ie7.htm```


## **Blacklist update**
TBD


## **Debugging**

check service logs:
- ```docker service logs <service>```
