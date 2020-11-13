.PHONY: build
build:
	@docker-compose build

.PHONY: tests
tests:
	@docker-compose run --rm app
