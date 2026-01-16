SHELL := /bin/bash

.PHONY: db-up test test-int api migrate

db-up:
	$(MAKE) -C .. db-up

test:
	$(MAKE) -C .. test

test-int:
	$(MAKE) -C .. test-int

api:
	$(MAKE) -C .. api

migrate:
	$(MAKE) -C .. migrate
