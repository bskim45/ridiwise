VENV := ./.venv/bin
VERSION ?= $(shell rye version)

.PHONY: install
install:
	rye sync
	$(VENV)/pre-commit install
	$(VENV)/playwright install chromium

.PHONY: lint
lint:
	$(VENV)/ruff check src
	$(VENV)/pylint src

.PHONY: lint-fix
lint-fix:
	$(VENV)/ruff check --fix src

.PHONY: format
format:
# sort imports
	$(VENV)/ruff check --select I --fix src
# format code
	$(VENV)/ruff format --diff src || true
	$(VENV)/ruff format src

.PHONY: test
test:
	$(VENV)/pytest \
		--cov-report term-missing:skip-covered \
		--cov-report html \
		--cov-report xml \
		--junitxml=junit.xml \
		-vvv \
		--pyargs ridiwise \
		--cov src \
		| tee pytest-coverage.txt

clean:
	rm -rf .coverage htmlcov coverage.xml pytest-coverage.txt junit.xml

### Docker
DOCKER_REPO ?= bskim45/ridiwise
LATEST_IMAGE := $(DOCKER_REPO):latest
VERSION_IMAGE := $(DOCKER_REPO):$(shell rye version)

.PHONY: docker-build
docker-build:
	docker build \
		-t $(LATEST_IMAGE) -t $(VERSION_IMAGE) \
		--build-arg VERSION=$(VERSION) \
		--build-arg REVISION=$(shell git rev-parse HEAD) \
		.

.PHONY: docker-buildx
docker-buildx:
	docker buildx build \
		-t $(LATEST_IMAGE) -t $(VERSION_IMAGE) \
		--platform linux/amd64,linux/arm64 \
		--build-arg VERSION=$(VERSION) \
		--build-arg REVISION=$(shell git rev-parse HEAD) \
		--output="type=image" \
		.

.PHONY: docker-push
push: build
	docker push $(LATEST_IMAGE)
	docker push $(VERSION_IMAGE)


.PHONY: bump-version
BUMP_TYPE ?= minor
bump-version:
	$(VENV)/bump-my-version bump $(BUMP_TYPE)

%:
	@:
