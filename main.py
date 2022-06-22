import os
import typing
import hashlib
import asyncio
import ipsw_api
import grabber_config

from tqdm import tqdm
from loguru import logger
from urllib.parse import urlparse

HASH_BLOCK_SIZE = 1024 * 64


async def fetch_firmwares(device_identifier: str) -> typing.Optional[typing.Dict]:
    firmware_data = await ipsw_api.get_ipsw_list(device_identifier, limit=1)

    try:
        firmware_data = firmware_data[0]
    except KeyError:
        return None

    return firmware_data


async def get_saved_device_info(device_identifier: str) -> typing.Optional[typing.Dict]:
    sanitised_device_identifier = grabber_config.sanitise_device_identifier(device_identifier)
    saved_devices = grabber_config.get_saved_firmwares()

    if sanitised_device_identifier in saved_devices:
        return saved_devices[sanitised_device_identifier]
    else:
        return None


def should_redownload(saved_firmware_info: typing.Dict, fetched_firmware_info: typing.Dict) -> bool:
    return not (fetched_firmware_info['sha1sum'] == saved_firmware_info['ipsw_hash']
                and os.path.exists(saved_firmware_info['ipsw_file_path']))


def delete_existing_data(device_identifier: str, saved_firmware_info: typing.Dict):
    ipsw_file_path = saved_firmware_info['ipsw_file_path']

    if os.path.exists(ipsw_file_path):
        os.remove(ipsw_file_path)

    grabber_config.remove_data(device_identifier)


async def verify_file_sha1(output_filename: str, fetched_firmware_info: typing.Dict) -> bool:
    verify_progress_bar = tqdm(total=fetched_firmware_info['filesize'], desc=f"Verifying {output_filename}", unit='iB',
                               unit_scale=True)
    file_hash = hashlib.sha1()
    with open(output_filename, "rb") as output_file:
        block = output_file.read(HASH_BLOCK_SIZE)
        while len(block) > 0:
            file_hash.update(block)
            verify_progress_bar.update(len(block))
            block = output_file.read(HASH_BLOCK_SIZE)

    return file_hash.hexdigest() == fetched_firmware_info['sha1']


async def main():
    for device_identifier in grabber_config.get_devices():
        logger.info(f"Getting latest available IPSW for device identifier {device_identifier}.")
        fetched_firmware_info = await fetch_firmwares(device_identifier)

        if fetched_firmware_info is None:
            logger.error(
                f"No IPSWs available for device {device_identifier}. This device might only support OTA updates.")
            continue

        firmware_version = fetched_firmware_info['version']

        logger.info(f"Latest firmware version for {device_identifier} is {firmware_version}.")

        # Is there any IPSW already saved for this device?
        saved_firmware_info = await get_saved_device_info(device_identifier)

        if saved_firmware_info:
            # Does it match the current version, and does the file still exist?
            if not should_redownload(saved_firmware_info, fetched_firmware_info):
                logger.info(f"Firmware {firmware_version} for device {device_identifier} is already downloaded "
                            f"(file name: {saved_firmware_info['ipsw_file_path']}).")
                continue
            else:
                delete_existing_data(device_identifier, saved_firmware_info)
                logger.info(f"Redownloading firmware {firmware_version} for device {device_identifier}")
        else:
            logger.info(f"No saved firmware for device {device_identifier}.")

        # Get the IPSW output filename.
        output_filename = os.path.basename(urlparse(fetched_firmware_info['url']).path)

        # Download the IPSW file.
        await ipsw_api.download_file(output_filename, fetched_firmware_info)

        # Verify the file against the SHA1 hash in the API response.
        hash_matches = await verify_file_sha1(output_filename, fetched_firmware_info)

        # If it doesn't match, delete it.
        if not hash_matches:
            logger.error(f"Downloaded file hash does not match expected hash.")
            os.remove(output_filename)
            continue

        # If it matches, save the IPSW data
        grabber_config.save_device_firmware_info(device_identifier, output_filename, fetched_firmware_info['sha1sum'])

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
