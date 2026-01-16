SHELL := /bin/bash

.PHONY: db-up test test-int api migrate lint format format-check typecheck check

db-up:
	$(MAKE) -C .. db-up

test:
	$(MAKE) -C .. test

test-int:
	$(MAKE) -C .. test-int

lint:
	$(MAKE) -C .. lint

format:
	$(MAKE) -C .. format

format-check:
	$(MAKE) -C .. format-check

typecheck:
	$(MAKE) -C .. typecheck

check:
	$(MAKE) -C .. check

api:
	$(MAKE) -C .. api

migrate:
	$(MAKE) -C .. migrate
