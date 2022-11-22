import concurrent.futures
import functools
import os
import typing

from catalog_validation.utils import VALID_TRAIN_REGEX

from .items_util import get_item_details, get_default_questions_context


def item_details(items: dict, location: str, questions_context: typing.Optional[dict], item_key: str) -> dict:
    train = items[item_key]
    item = item_key.removesuffix(f'_{train}')
    item_location = os.path.join(location, train, item)
    return {
        k: v for k, v in get_item_details(item_location, questions_context, {'retrieve_versions': True}).items()
        if k != 'versions'
    }


def retrieve_train_names(location: str, all_trains=True, trains_filter=None) -> list:
    train_names = []
    trains_filter = trains_filter or []
    for train in os.listdir(location):
        if (
            not (all_trains or train in trains_filter) or not os.path.isdir(
                os.path.join(location, train)
            ) or train.startswith('.') or train in ('library', 'docs') or not VALID_TRAIN_REGEX.match(train)
        ):
            continue
        train_names.append(train)
    return train_names


def get_items_in_trains(trains_to_traverse: list, catalog_location: str) -> dict:
    items = {}
    for train in trains_to_traverse:
        items.update({
            f'{i}_{train}': train for i in os.listdir(os.path.join(catalog_location, train))
            if os.path.isdir(os.path.join(catalog_location, train, i))
        })

    return items


def retrieve_trains_data(
    items: dict, catalog_location: str, preferred_trains: list,
    trains_to_traverse: list, job: typing.Any = None, questions_context: typing.Optional[dict] = None
) -> typing.Tuple[dict, set]:
    questions_context = questions_context or get_default_questions_context()
    trains = {
        'charts': {},
        'test': {},
        **{k: {} for k in trains_to_traverse},
    }
    unhealthy_apps = set()

    total_items = len(items)
    with concurrent.futures.ProcessPoolExecutor(max_workers=(5 if total_items > 10 else 2)) as exc:
        for index, result in enumerate(zip(items, exc.map(
            functools.partial(item_details, items, catalog_location, questions_context),
            items, chunksize=(10 if total_items > 10 else 5)
        ))):
            item_key = result[0]
            item_info = result[1]
            train = items[item_key]
            item = item_key.removesuffix(f'_{train}')
            if job:
                job.set_progress(
                    int((index / total_items) * 80) + 10,
                    f'Retrieved information of {item!r} item from {train!r} train'
                )
            trains[train][item] = item_info
            if train in preferred_trains and not trains[train][item]['healthy']:
                unhealthy_apps.add(f'{item} ({train} train)')

    return trains, unhealthy_apps
