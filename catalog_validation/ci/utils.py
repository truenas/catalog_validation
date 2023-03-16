import os
import yaml

from catalog_validation.items.utils import DEVELOPMENT_DIR
from semantic_version import Version


DEV_DIRECTORY_RELATIVE_PATH: str = os.path.join('library', DEVELOPMENT_DIR)
OPTIONAL_METADATA_FILES = ['upgrade_info.json', 'upgrade_strategy']
REQUIRED_METADATA_FILES = ['item.yaml']


def get_app_version(app_path: str) -> str:
    # This assumes that file exists and version is specified and is good
    with open(os.path.join(app_path, 'Chart.yaml'), 'r') as f:
        return yaml.safe_load(f.read())['version']


def get_ci_development_directory(catalog_path: str) -> str:
    return os.path.join(catalog_path, DEV_DIRECTORY_RELATIVE_PATH)


def version_has_been_bumped(app_path: str, new_version: str) -> bool:
    if not os.path.isdir(app_path):
        return True

    versions = [
        Version(version) for version in filter(lambda v: os.path.isdir(os.path.join(app_path, v)), os.listdir(app_path))
    ]
    return not versions or Version(new_version) > versions[-1]
