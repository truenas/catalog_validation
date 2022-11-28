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
