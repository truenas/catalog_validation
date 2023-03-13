import os

from catalog_validation.exceptions import ValidationErrors
from catalog_validation.validation import validate_catalog_item_version, validate_chart_version

from .utils import get_app_version


def validate_dev_directory_structure(catalog_path: str) -> None:
    verrors = ValidationErrors()
    verrors.check()


def validate_train(catalog_path: str, train_path: str, schema: str) -> None:
    verrors = ValidationErrors()
    train_name = os.path.basename(train_path)
    for app_name in filter(os.path.isdir, os.listdir(train_path)):
        app_path = os.path.join(train_path, app_name)
        try:
            validate_app(app_path, f'{schema}.{app_name}')
        except ValidationErrors as ve:
            verrors.extend(ve)
        else:
            train_app_path = os.path.join(catalog_path, train_name, app_name)
            if not os.path.exists(train_app_path):
                # The application is new and we are good
                continue

            if get_app_version(app_path) in os.listdir(train_path):
                verrors.add(
                    f'{schema}.{app_name}.version',
                    'Version must be bumped as app has been changed but version has not been updated'
                )


def validate_app(app_dir_path: str, schema: str) -> None:
    app_name = os.path.basename(app_dir_path)
    chart_version_path = os.path.join(app_dir_path, 'Chart.yaml')
    verrors = validate_chart_version(ValidationErrors(), chart_version_path, schema, app_name)
    verrors.check()

    validate_catalog_item_version(app_dir_path, schema, get_app_version(app_dir_path))
