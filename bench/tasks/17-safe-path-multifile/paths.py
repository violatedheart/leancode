from pathlib import Path


def resolve_under(root, requested):
    return (Path(root) / requested).resolve()
