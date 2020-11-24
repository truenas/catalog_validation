import os
import yaml

from semantic_version import Version

from .exceptions import CatalogDoesNotExist, ValidationErrors
from .utils import WANTED_FILES_IN_ITEM_VERSION


def validate_catalog(catalog_path):
    if not os.path.exists(catalog_path):
        raise CatalogDoesNotExist(catalog_path)

    # We will be doing following steps to ensure a catalog is compliant:
    # 1) Each directory under root is a valid train further containing catalog items
    # 2)

    verrors = ValidationErrors()

    for file_dir in os.listdir(catalog_path):
        complete_path = os.path.join(catalog_path, file_dir)
        if file_dir.startswith('.') or not os.path.isdir(complete_path):
            continue

        try:
            validate_train(complete_path)
        except ValidationErrors as e:
            verrors.extend(e)

    verrors.check()


def validate_train(train_path):
    train = os.path.basename(train_path)
    verrors = ValidationErrors()
    for catalog_item in os.listdir(train_path):
        try:
            validate_catalog_item(os.path.join(train_path, catalog_item), f'{train}.{catalog_item}')
        except ValidationErrors as e:
            verrors.extend(e)

    verrors.check()


def validate_catalog_item(catalog_item_path, schema):
    # We should ensure that each catalog item has at least 1 version available
    # Also that we have item.yaml present
    verrors = ValidationErrors()
    item_name = os.path.join(catalog_item_path)
    files = []
    versions = []
    for file_dir in os.listdir(catalog_item_path):
        complete_path = os.path.join(catalog_item_path, file_dir)
        if os.path.isdir(complete_path):
            versions.append(complete_path)
        else:
            files.append(file_dir)

    if not versions:
        verrors.add(f'{schema}.versions', f'No versions found for {item_name} item.')

    if 'item.yaml' not in files:
        verrors.add(f'{schema}.item', 'Item configuration (item.yaml) not found')

    for version_path in versions:
        try:
            validate_catalog_item_version(version_path, f'{schema}.versions.{os.path.basename(version_path)}')
        except ValidationErrors as e:
            verrors.extend(e)

    verrors.check()


def validate_catalog_item_version(version_path, schema):
    verrors = ValidationErrors()
    version_name = os.path.basename(version_path)
    item_name = version_path.split('/')[-2]
    try:
        Version(version_name)
    except ValueError:
        verrors.add(f'{schema}.name', f'{version_name!r} is not a valid version name.')

    files_diff = WANTED_FILES_IN_ITEM_VERSION ^ set(
        f for f in os.listdir(version_path) if f in WANTED_FILES_IN_ITEM_VERSION
    )
    if files_diff:
        verrors.add(f'{schema}.required_files', f'Missing {", ".join(files_diff)} required configuration files.')

    chart_version_path = os.path.join(version_path, 'Chart.yaml')
    if os.path.exists(chart_version_path):
        with open(chart_version_path, 'r') as f:
            chart_config = yaml.safe_load(f.read())

        if chart_config.get('name') != item_name:
            verrors.add(f'{schema}.item_name', 'Item name not correctly set in "Chart.yaml".')

        if chart_config.get('version') != version_name:
            verrors.add(
                f'{schema}.name', 'Configured version name in "Chart.yaml" does not match version directory name.'
            )

    verrors.check()
