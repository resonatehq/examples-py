# prompt-checking

How to run. Install [ollama](https://ollama.com) and download the [llama3.1](https://ollama.com/library/llama3.1) model

## How to run

### Using [rye](https://rye.astral.sh) (Recommended)

1. Setup project's virtual environment and install dependencies
```zsh
rye sync
```

2. Run tests
```zsh
rye test
```

### Using pip

1. Install dependencies
```zsh
pip install -r requirements-dev.lock
```

4. Run tests
```zsh
pytest
```
