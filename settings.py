import json
from enum import Enum


class AuthLevel(Enum):
    ADMIN = 100
    MOD = 50
    USER = 20
    UNAUTHORIZED = -1

version = 1.5
api_token: str = "1"
chat_ids: dict
forward_rules: list
contacts: list
new_rule: dict = {}

def load_json_settings(json_path):
    """ return Settings if loaded queue successfully from disk"""
    print("🕐 Loading settings from `{}`".format(json_path))
    try:
        with open(json_path, 'r') as f:
            data_j = json.load(f)
            global api_token, chat_ids, forward_rules, contacts
            api_token = data_j['api']
            chat_ids = data_j['chat_ids']
            forward_rules = data_j['forwards']
            contacts = data_j['contacts']
            print("  ✅ Settings loaded with {} forward rules and {} contacts".format(len(forward_rules), len(contacts)))
            return data_j
    except Exception as e:
        print("  ❌ ERROR: Can not load settings from `{}`:\n {}".format(json_path, str(e)))
        return None


def save_json_settings(json_path):
    """ return True if loaded queue successfully from disk"""
    print("🕐 Loading settings from `{}`".format(json_path))
    try:
        global api_token, chat_ids, forward_rules, contacts
        with open(json_path, 'w') as f:
            json.dump({
                "api": api_token,
                "chat_ids": chat_ids,
                "forwards": forward_rules,
                "contacts": contacts
            }, f, sort_keys=True)
            print("  ✅ Settings saved with {} contacts".format(len(contacts)))
            return True
    except Exception as e:
        print("  ❌ ERROR: Can not save settings from `{}`:\n {}".format(json_path, str(e)))
        return False
