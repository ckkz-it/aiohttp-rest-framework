.PHONY: build_image
build_image:
	@docker-compose build

.PHONY: tests
tests:
	@docker-compose run --rm app

.PHONY: build_package
build_package:
	@python setup.py sdist bdist_wheel --universal

.PHONY: deploy_package
deploy_package:
	@twine upload dist/* -r pypi
