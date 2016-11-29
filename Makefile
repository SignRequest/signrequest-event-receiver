ROOT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

CONTAINER_ENV := -e SIGNREQUEST_TOKEN=$${SIGNREQUEST_TOKEN} -e BAMBOO_TOKEN=$${BAMBOO_TOKEN} -e BAMBOO_SUBDOMAIN=$${BAMBOO_SUBDOMAIN}

DOCKER_REGISTRY_HOST := quay.io
DOCKER_REGISTRY_USER := signrequest
DOCKER_REGISTRY_PREFIX := $(DOCKER_REGISTRY_HOST)/$(DOCKER_REGISTRY_USER)
REPO_NAME := signrequest-event-receiver
DOCKER_IMAGE := $(DOCKER_REGISTRY_PREFIX)/$(REPO_NAME)

IMAGE_VERSION := `cat $(ROOT_DIR)/.docker_version`

.PHONY: default build run_dev
default: build

build :
	docker build --rm -t $(DOCKER_IMAGE):latest .

run_dev : build
	docker run -it -p 8888:8888 -v $(ROOT_DIR):/src -e SR_RECEIVER_DEBUG=1 $(CONTAINER_ENV) $(DOCKER_IMAGE):latest

run :
	docker run -it -p 8888:8888 -v $(ROOT_DIR):/src $(CONTAINER_ENV) $(DOCKER_IMAGE):latest

push : build
	docker push $(DOCKER_IMAGE):latest
	docker tag $(DOCKER_IMAGE):latest $(DOCKER_IMAGE):$(IMAGE_VERSION)
	docker push $(DOCKER_IMAGE):$(IMAGE_VERSION)
