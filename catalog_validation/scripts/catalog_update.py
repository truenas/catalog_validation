#!/usr/bin/env python
import argparse
import contextlib
import json
import os
import shutil

from catalog_validation.ci.utils import (
    get_app_version, get_ci_development_directory, OPTIONAL_METADATA_FILES,
    REQUIRED_METADATA_FILES, version_has_been_bumped,
)
from catalog_validation.items.catalog import get_items_in_trains, retrieve_train_names, retrieve_trains_data
from catalog_validation.utils import CACHED_CATALOG_FILE_NAME
from collections import defaultdict


def get_trains(location: str) -> dict:
    preferred_trains: list = []

    trains_to_traverse = retrieve_train_names(location)
    items = get_items_in_trains(trains_to_traverse, location)

    return retrieve_trains_data(items, location, preferred_trains, trains_to_traverse)[0]


def get_apps_to_publish(catalog_path: str) -> dict:
    ci_dev_dir = get_ci_development_directory(catalog_path)
    to_publish_apps = defaultdict(list)
    for train_name in os.listdir(ci_dev_dir):
        train_path = os.path.join(ci_dev_dir, train_name)
        if not os.path.isdir(train_path):
            continue

        for app_name in os.listdir(train_path):
            app_path = os.path.join(train_path, app_name)
            if not os.path.isdir(app_path):
                continue

            app_current_version = get_app_version(app_path)
            if version_has_been_bumped(os.path.join(catalog_path, train_name, app_name), app_current_version):
                to_publish_apps[train_name].append({'name': app_name, 'version': app_current_version})

    return to_publish_apps


def publish_updated_apps(catalog_path: str) -> None:
    ci_dev_directory = get_ci_development_directory(catalog_path)
    if not os.path.isdir(ci_dev_directory):
        return

    for train_name, apps in get_apps_to_publish(catalog_path).items():
        dev_train_path = os.path.join(ci_dev_directory, train_name)
        publish_train_path = os.path.join(catalog_path, train_name)
        os.makedirs(publish_train_path, exist_ok=True)

        for app in apps:
            app_name, app_version = app['name'], app['version']
            dev_app_path = os.path.join(dev_train_path, app_name)
            publish_app_path = os.path.join(publish_train_path, app_name)
            publish_app_version_path = os.path.join(publish_app_path, app_version)
            os.makedirs(publish_app_path, exist_ok=True)

            dev_item_yaml_path = os.path.join(dev_app_path, 'item.yaml')
            publish_item_yaml_path = os.path.join(publish_app_path, 'item.yaml')
            shutil.copy(dev_item_yaml_path, publish_item_yaml_path)
            shutil.copytree(dev_app_path, publish_app_version_path)

            for file_name in OPTIONAL_METADATA_FILES + REQUIRED_METADATA_FILES:
                with contextlib.suppress(OSError):
                    os.unlink(os.path.join(publish_app_version_path, file_name))

            for version in os.listdir(publish_app_path):
                version_path = os.path.join(publish_app_path, version)
                if not os.path.isdir(version_path):
                    continue

                if version != app_version:
                    shutil.rmtree(version_path)

            print(
                f'[\033[92mOK\x1B[0m]\tPublished {app_name!r} having {app_version!r} version '
                f'to {train_name!r} train successfully!'
            )


def update_catalog_file(location: str) -> None:
    catalog_file_path = os.path.join(location, CACHED_CATALOG_FILE_NAME)
    with open(catalog_file_path, 'w') as f:
        f.write(json.dumps(get_trains(location), indent=4))

    print(f'[\033[92mOK\x1B[0m]\tUpdated {catalog_file_path!r} successfully!')


def update_catalog(catalog_path: str) -> None:
    publish_updated_apps(catalog_path)
    update_catalog_file(catalog_path)


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='sub-command help', dest='action')

    parser_setup = subparsers.add_parser('update', help='Update TrueNAS catalog')
    parser_setup.add_argument('--path', help='Specify path of TrueNAS catalog')

    args = parser.parse_args()
    if args.action == 'update':
        update_catalog(args.path)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
