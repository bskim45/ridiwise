VERSION ?= $(shell uv version --short --preview)

.PHONY: install
install:
	uv sync
	uv run pre-commit install
	uv run playwright install chromium

.PHONY: lint
lint:
	uv run ruff check src
	uv run pylint src

.PHONY: lint-fix
lint-fix:
	uv run ruff check --fix src

.PHONY: format
format:
# sort imports
	uv run ruff check --select I --fix src
# format code
	uv run ruff format --diff src || true
	uv run ruff format src

.PHONY: test
test:
	uv run pytest \
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
VERSION_IMAGE := $(DOCKER_REPO):$(VERSION)

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
	uv run bump-my-version bump $(BUMP_TYPE)

%:
	@:
