from requests.exceptions import HTTPError


def augmented_raise_for_status(response):
    """Wrap the standard `requests.response.raise_for_status()` method and return reason"""
    try:
        response.raise_for_status()
    except HTTPError as e:
        if response.text:
            raise HTTPError(f"{e}. Response text: {response.text}")
        else:
            raise e
