from paths import resolve_under


def download_path(root, requested):
    return resolve_under(root, requested)
