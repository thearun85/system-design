# Loadbalancer
This project is to demonstrate loadbalancers, the various categories and other aspects of it.

## v1 - 
a service created which can be run as multiple instances on different ports.

## v2 - a round robin load balancer created, which serves as the front end and distributes traffic to the backends. There is no real health check. If the url's are down, the request will still be forwarded to them which responds with a service error

## v3 - dockerized the project. 
1. Dockerfile.service - image for the backend service - will listen on 5000
2. Dockerfile.lb - image for the load balancer service. will listen on 8080
3. docker-compose.yml - this will orchestrate the entire setup. It will create the images and spawn 3 instances of the backend services and one instance of the load balancer.The 3 instances will be exposed on 5001, 5002 & 5003

4. Changes are made in both .py files to obtain the variables from environment rather the command line arguments.

5. docker-compose up will spin up the instances for you. Load balancer can be tested at http://localhost:8080

## v4 - Simple round robin loadbalancer with a healthcheck
