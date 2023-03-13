import os
import yaml

from catalog_validation.exceptions import ValidationErrors
from catalog_validation.validation import validate_catalog_item_version, validate_chart_version


def validate_dev_directory_structure(catalog_path: str) -> None:
    verrors = ValidationErrors()
    verrors.check()


def validate_app(app_dir_path: str) -> None:
    app_name = os.path.basename(app_dir_path)
    error_schema = f'dev.{app_name}'
    chart_version_path = os.path.join(app_dir_path, 'Chart.yaml')
    verrors = validate_chart_version(ValidationErrors(), chart_version_path, error_schema, app_name)
    verrors.check()

    with open(chart_version_path, 'r') as f:
        chart_config = yaml.safe_load(f.read())

    validate_catalog_item_version(app_dir_path, error_schema, chart_config['version'])
