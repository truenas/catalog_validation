import concurrent.futures
import os
import typing

from catalog_validation.utils import VALID_TRAIN_REGEX

from .items_util import get_item_details


def item_details(items: dict, location: str, questions_context: typing.Optional[dict], item_key: str):
    train = items[item_key]
    item = item_key.removesuffix(f'_{train}')
    item_location = os.path.join(location, train, item)
    return {
        k: v for k, v in get_item_details(item_location, questions_context, {'retrieve_versions': True}).items()
        if k != 'versions'
    }


def retrieve_train_names(self, location, all_trains=True, trains_filter=None):
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
