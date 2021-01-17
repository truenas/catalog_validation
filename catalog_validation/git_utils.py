import os
import subprocess

from .exceptions import CatalogDoesNotExist
from .utils import CatalogItem


def get_affected_catalog_items_with_versions(catalog_path, base_branch='master'):
    if not os.path.exists(catalog_path):
        raise CatalogDoesNotExist(catalog_path)

    cp = subprocess.run(
        ['git', '-C', catalog_path, '--no-pager', 'diff', '--name-only', base_branch],
        capture_output=True, check=True,
    )
    items_to_be_checked = []
    for file_path in filter(bool, map(str.strip, cp.stdout.decode().split('\n'))):
        if file_path.startswith(('.', 'library/')):
            continue
        # Any file not being under a version directory is of no use to us and we can skip it as it's not enough
        # for us to test the catalog item in question
        # train_name/catalog_item_name/version_name/some_file_here_or_more_nested
        if len(file_path.split('/')) < 4:
            continue

        train, item, version, file_path_under_version = file_path.split('/', 3)
        catalog_item = CatalogItem(train=train, item=item, version=version)
        if catalog_item in items_to_be_checked:
            continue

        file_name = os.path.basename(file_path)
        if file_name.startswith('.') or file_name.endswith('.md') or file_path_under_version == 'questions.yaml':
            continue

        items_to_be_checked.append(catalog_item)

    return items_to_be_checked
