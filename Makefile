.PHONY: build_image
build_image:
	@docker-compose build

.PHONY: tests
tests:
	@docker-compose run --rm tests

.PHONY: lint
lint:
	@docker-compose run --rm tests sh -c 'flake8'

.PHONY: sort_imports
sort_imports:
	@docker-compose run --rm tests sh -c 'isort .'

.PHONY: build_package
build_package:
	@rm -rf build dist && docker-compose run \
		--rm \
		--no-deps \
		tests \
		sh -c 'rm -rf build dist && python setup.py sdist bdist_wheel --universal'

.PHONY: deploy_package
deploy_package:
	@docker-compose run --rm --no-deps tests sh -c 'twine upload dist/* -r pypi'
