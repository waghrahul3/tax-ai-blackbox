from core.config import STORAGE_TYPE
from storage.local_storage import LocalStorage
from storage.zoho_storage import ZohoStorage


def get_storage():

    if STORAGE_TYPE == "zoho":
        return ZohoStorage()

    return LocalStorage()