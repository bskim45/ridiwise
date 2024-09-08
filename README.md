# ridiwise

Sync Ridibooks book notes to Readwise.io

## Installation

### Docker

```bash
# Docker Hub (docker.io)
$ docker run --rm -it bskim45/ridiwise --help
# Github Container Registry (ghcr.io)
$ docker run --rm -it ghcr.io/bskim45/ridiwise --help
```

### Pip/Pipx

Prerequisites:

- Python 3.10 or later
- [Playwright](https://playwright.dev/python/docs/intro)

Install playwright:

```bash
# with pip
pip install playwright

# or with pipx
pipx install playwright

# install browser
playwright install chromium
```

Install ridiwise:

```bash
# with pip
pip install git+https://github.com/bskim45/ridiwise.git

# or with pipx
pipx install git+https://github.com/bskim45/ridiwise.git
```

## Usage

```bash
$ ridiwise --help
 Usage: ridiwise [OPTIONS] COMMAND [ARGS]...  

 ridiwise: Sync Ridibooks book notes to Readwise.io

 (...)
```

## License

The code is released under the MIT license. See [LICENSE](LICENSE) for details.
