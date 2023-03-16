import os

from catalog_validation.exceptions import ValidationErrors
from catalog_validation.validation import validate_catalog_item_version, validate_chart_version

from .utils import get_app_version, get_ci_development_directory, version_has_been_bumped


def validate_dev_directory_structure(catalog_path: str, to_check_apps: dict) -> None:
    verrors = ValidationErrors()
    dev_directory = get_ci_development_directory(catalog_path)
    for train_name in filter(
        lambda name: name in to_check_apps and os.path.isdir(os.path.join(dev_directory, name)),
        os.listdir(dev_directory)
    ):
        validate_train(
            catalog_path, os.path.join(dev_directory, train_name), f'dev.{train_name}', to_check_apps[train_name]
        )
    verrors.check()


def validate_train(catalog_path: str, train_path: str, schema: str, to_check_apps: list) -> None:
    verrors = ValidationErrors()
    train_name = os.path.basename(train_path)
    for app_name in filter(
        lambda name: os.path.isdir(os.path.join(train_path, name)), os.listdir(train_path)
    ):
        if app_name not in to_check_apps:
            continue

        app_path = os.path.join(train_path, app_name)
        try:
            validate_app(app_path, f'{schema}.{app_name}')
        except ValidationErrors as ve:
            verrors.extend(ve)
        else:
            published_train_app_path = os.path.join(catalog_path, train_name, app_name)
            if not os.path.exists(published_train_app_path):
                # The application is new and we are good
                continue

            if not version_has_been_bumped(published_train_app_path, get_app_version(app_path)):
                verrors.add(
                    f'{schema}.{app_name}.version',
                    'Version must be bumped as app has been changed but version has not been updated'
                )

        verrors.check()


def validate_app(app_dir_path: str, schema: str) -> None:
    app_name = os.path.basename(app_dir_path)
    chart_version_path = os.path.join(app_dir_path, 'Chart.yaml')
    verrors = validate_chart_version(ValidationErrors(), chart_version_path, schema, app_name)
    verrors.check()

    validate_catalog_item_version(app_dir_path, schema, get_app_version(app_dir_path), app_name)
