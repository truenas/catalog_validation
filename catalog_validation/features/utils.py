import requests


def retrieve_features():
    try:
        req = requests.get(
            'https://raw.githubusercontent.com/truenas/charts/master/features_capability.json', timeout=30
        )
    except requests.exceptions.RequestException:
        return {}
    else:
        if req.status_code != 200:
            return {}
        else:
            return req.json()
