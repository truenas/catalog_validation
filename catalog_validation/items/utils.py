import contextlib
import git

from datetime import datetime
from typing import Optional

from catalog_validation.schema.migration_schema import MIGRATION_DIRS


TRAIN_IGNORE_DIRS = ['library', 'docs'] + MIGRATION_DIRS


def get_catalog_json_schema() -> dict:
    return {
        'type': 'object',
        'patternProperties': {
            '.*': {
                'type': 'object',
                'title': 'Train',
                'patternProperties': {
                    '.*': {
                        'type': 'object',
                        'title': 'Item',
                        'properties': {
                            'name': {
                                'type': 'string',
                                'title': 'Name',
                            },
                            'categories': {
                                'type': 'array',
                                'items': {
                                    'type': 'string'
                                },
                            },
                            'app_readme': {
                                'type': 'string',
                            },
                            'location': {
                                'type': 'string',
                            },
                            'healthy': {
                                'type': 'boolean',
                            },
                            'healthy_error': {
                                'type': ['string', 'null'],
                            },
                            'latest_version': {
                                'type': 'string',
                            },
                            'latest_app_version': {
                                'type': 'string',
                            },
                            'latest_human_version': {
                                'type': 'string',
                            },
                            'description': {
                                'type': ['string', 'null'],
                            },
                            'title': {
                                'type': 'string',
                            },
                            'icon_url': {
                                'type': ['string', 'null'],
                            }

                        },
                        'required': [
                            'name', 'categories', 'location', 'healthy', 'icon_url',
                            'latest_version', 'latest_app_version', 'latest_human_version'
                        ],
                    }
                }

            }
        }
    }


def get_last_updated_date(repo_path: str, folder_path: str) -> Optional[str]:
    with contextlib.suppress(Exception):
        # We don't want to fail querying items if for whatever reason this fails
        repo = git.Repo(repo_path)
        latest_commit = next(repo.iter_commits(paths=folder_path, max_count=1), None)
        if latest_commit:
            timestamp = datetime.fromtimestamp(latest_commit.committed_date)
            return timestamp.strftime('%Y-%m-%d %H:%M:%S')
        else:
            return None
