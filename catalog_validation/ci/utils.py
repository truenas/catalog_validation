import os
import yaml

from catalog_validation.items.utils import DEVELOPMENT_DIR


def get_app_version(app_path: str) -> str:
    # This assumes that file exists and version is specified and is good
    with open(os.path.join(app_path, 'Chart.yaml'), 'r') as f:
        return yaml.safe_load(f.read())['version']


def get_ci_development_directory(catalog_path: str) -> str:
    return os.path.join(catalog_path, 'library', DEVELOPMENT_DIR)
