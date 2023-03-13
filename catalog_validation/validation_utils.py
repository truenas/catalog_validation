import os
import yaml

from .exceptions import ValidationErrors


def validate_chart_version(
    verrors: ValidationErrors, chart_version_path: str, schema: str, item_name: str, version_name: str,
) -> ValidationErrors:
    if os.path.exists(chart_version_path):
        with open(chart_version_path, 'r') as f:
            try:
                chart_config = yaml.safe_load(f.read())
            except yaml.YAMLError:
                verrors.add(schema, 'Must be a valid yaml file')
            else:
                if not isinstance(chart_config, dict):
                    verrors.add(schema, 'Must be a dictionary')
                else:
                    if chart_config.get('name') != item_name:
                        verrors.add(f'{schema}.item_name', 'Item name not correctly set in "Chart.yaml".')

                    if chart_config.get('version') != version_name:
                        verrors.add(
                            f'{schema}.version',
                            'Configured version in "Chart.yaml" does not match version directory name.'
                        )
    else:
        verrors.add(schema, 'Missing chart version file')

    return verrors
