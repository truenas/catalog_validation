#!/usr/bin/env python
import argparse
import json
import os

from catalog_validation.items.catalog import get_items_in_trains, retrieve_train_names, retrieve_trains_data


def get_trains(location: str) -> dict:
    preferred_trains: list = []

    trains_to_traverse = retrieve_train_names(location)
    items = get_items_in_trains(trains_to_traverse, location)

    return retrieve_trains_data(items, location, preferred_trains, trains_to_traverse)[0]


def update_catalog_file(location: str) -> None:
    catalog_file_path = os.path.join(location, 'catalog.json')
    with open(catalog_file_path, 'w') as f:
        f.write(json.dumps(get_trains(location), indent=4))

    print(f'[\033[92mOK\x1B[0m]\tUpdated {catalog_file_path!r} successfully!')


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='sub-command help', dest='action')

    parser_setup = subparsers.add_parser('update', help='Update TrueNAS catalog')
    parser_setup.add_argument('--path', help='Specify path of TrueNAS catalog')

    args = parser.parse_args()
    if args.action == 'update':
        update_catalog_file(args.path)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
