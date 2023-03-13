import os

from catalog_validation.items.utils import DEVELOPMENT_DIR


def get_ci_development_directory(catalog_path: str) -> str:
    return os.path.join(catalog_path, 'library', DEVELOPMENT_DIR)
