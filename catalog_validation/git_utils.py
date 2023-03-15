import os
import subprocess

from catalog_validation.ci.utils import DEV_DIRECTORY_RELATIVE_PATH, get_ci_development_directory
from catalog_validation.items.utils import valid_train
from collections import defaultdict

from .exceptions import CatalogDoesNotExist
from .utils import CatalogItem


def get_changed_apps(catalog_path: str, base_branch: str = 'master') -> dict:
    if not os.path.exists(catalog_path):
        raise CatalogDoesNotExist(catalog_path)

    cp = subprocess.run(
        ['git', '-C', catalog_path, '--no-pager', 'diff', '--name-only', base_branch],
        capture_output=True, check=True,
    )
    dev_directory_path = get_ci_development_directory(catalog_path)
    to_check_apps = defaultdict(list)
    for file_path in filter(
        lambda path: path and path.startswith(f'{DEV_DIRECTORY_RELATIVE_PATH}/'),
        map(str.strip, cp.stdout.decode().split('\n'))
    ):
        dev_dir_relative_path = file_path.strip(f'{DEV_DIRECTORY_RELATIVE_PATH}/')
        train_name = dev_dir_relative_path.split('/', 1)[0]
        if not valid_train(train_name, os.path.join(dev_directory_path, train_name)):
            continue

        app_name = dev_dir_relative_path.split('/')[1]
        if not os.path.isdir(os.path.join(dev_directory_path, train_name, app_name)):
            continue

        if app_name not in to_check_apps[train_name]:
            to_check_apps[train_name].append(app_name)

    return to_check_apps


def get_affected_catalog_items_with_versions(catalog_path, base_branch='master'):
    if not os.path.exists(catalog_path):
        raise CatalogDoesNotExist(catalog_path)

    cp = subprocess.run(
        ['git', '-C', catalog_path, '--no-pager', 'diff', '--name-only', base_branch],
        capture_output=True, check=True,
    )
    items_to_be_checked = []
    for file_path in filter(bool, map(str.strip, cp.stdout.decode().split('\n'))):
        train_name = file_path.split('/', 1)[0]
        if not valid_train(train_name, os.path.join(catalog_path, train_name)):
            continue
        # Any file not being under a version directory is of no use to us and we can skip it as it's not enough
        # for us to test the catalog item in question
        # train_name/catalog_item_name/version_name/some_file_here_or_more_nested
        if len(file_path.split('/')) < 4:
            continue

        train, item, version, file_path_under_version = file_path.split('/', 3)

        if not os.path.exists(os.path.join(catalog_path, train, item, version)):
            # In case the version was deleted/removed and does not exist, we are not going to try and check that
            continue

        catalog_item = CatalogItem(train=train, item=item, version=version)
        if catalog_item in items_to_be_checked:
            continue

        file_name = os.path.basename(file_path)
        if file_name.startswith('.') or file_name.endswith('.md') or file_path_under_version == 'questions.yaml':
            continue

        items_to_be_checked.append(catalog_item)

    return items_to_be_checked
