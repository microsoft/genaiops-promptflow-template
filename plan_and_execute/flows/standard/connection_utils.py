from promptflow.connections import CustomStrongTypeConnection
from promptflow.contracts.types import Secret

class CustomConnection(CustomStrongTypeConnection):
    """
    :param aoai_api_key: The api key for Azure Open AI.
    :type aoai_api_key: Secret
    :param bing_api_key: The api key for the Bing Search.
    :type bing_api_key: Secret
    :param aoai_model_gpt4: The deployment name for the GPT-4 model.
    :type aoai_model_gpt4: String
    :param aoai_model_gpt35: The deployment name for the GPT-3.5 model.
    :type aoai_model_gpt35: String
    :param aoai_base_url: The base url for the Azure Open AI.
    :type aoai_base_url: String
    :param aoai_api_version: The api version for the Azure Open AI.
    :type aoai_api_version: String
    :param bing_endpoint: The endpoint for the Bing Search.
    :type bing_endpoint: String
    """
    aoai_api_key: Secret
    bing_api_key: Secret
    aoai_model_gpt4: str
    aoai_model_gpt35: str
    aoai_base_url: str
    aoai_api_version: str
    bing_endpoint: str

class ConnectionInfo(object):
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(ConnectionInfo, cls).__new__(cls)
        return cls.instance