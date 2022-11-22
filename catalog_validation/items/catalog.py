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




