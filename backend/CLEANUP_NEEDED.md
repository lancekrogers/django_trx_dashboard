# Cleanup Needed

The following files/directories should be removed as they are no longer needed in a uv project:

## Files to Remove:
- `requirements/` directory (including base.txt and development.txt)
- `setup.sh`
- `setup_django.sh`

## Why:
- We're now using `pyproject.toml` as the single source of truth for dependencies
- uv manages dependencies through `pyproject.toml`, not requirements files
- Setup is now handled through the Makefile using `uv sync`

## To Remove:
```bash
rm -rf requirements/
rm setup.sh setup_django.sh
```

After cleanup, the project will be a proper uv project with all dependencies defined in `pyproject.toml`.