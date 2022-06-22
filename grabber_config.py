import typing
import toml

from loguru import logger

config = {}

with open("config.toml", "r") as _config_file:
    try:
        config = toml.load(_config_file)
    except Exception as e:
        logger.error("Failed to load configuration.")
        raise e


def get_devices() -> typing.List:
    return config['devices']['device_list']


def save_device_firmware_info(device_identifier: str, ipsw_file_path: str, ipsw_hash: str):
    sanitised_device_identifier = sanitise_device_identifier(device_identifier)

    if 'saved_devices' not in config:
        config['saved_devices'] = {}

    device_data = {
        'ipsw_file_path': ipsw_file_path,
        'ipsw_hash': ipsw_hash
    }

    config['saved_devices'][sanitised_device_identifier] = device_data

    write_config()


def sanitise_device_identifier(device_identifier: str) -> str:
    return device_identifier.replace(",", "_")


def get_saved_firmwares() -> typing.List:
    try:
        return config['saved_devices']
    except KeyError:
        return []


def remove_data(device_identifier: str):
    sanitised_device_identifier = sanitise_device_identifier(device_identifier)

    if sanitised_device_identifier not in config['saved_devices']:
        return

    config['saved_devices'].pop(sanitised_device_identifier)

    write_config()


def write_config():
    with open("config.toml", "w") as config_file:
        config_file.write(toml.dumps(config))
