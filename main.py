import hashlib
import os
import httpx
import asyncio
import ipsw_api
import grabber_config

from tqdm import tqdm
from loguru import logger
from urllib.parse import urlparse

HASH_BLOCK_SIZE = 1024 * 64


async def main():
    for device_identifier in grabber_config.get_devices():
        logger.info(f"Getting latest available IPSW for device identifier {device_identifier}.")
        ipsw_data = await ipsw_api.get_ipsw_list(device_identifier, limit=1)

        try:
            ipsw_data = ipsw_data[0]
        except KeyError:
            logger.error(f"No IPSWs available for device {device_identifier}. This device might only support OTA updates.")
            continue

        firmware_version = ipsw_data['version']

        logger.info(f"Latest firmware version for {device_identifier} is {firmware_version}.")

        # Is there any IPSW already saved for this device?
        sanitised_device_identifier = grabber_config.sanitise_device_identifier(device_identifier)
        saved_devices = grabber_config.get_saved_firmwares()

        if sanitised_device_identifier in saved_devices:
            saved_firmware_info = saved_devices[sanitised_device_identifier]

            # Does it match the current version, and does the file still exist?
            if ipsw_data['sha1sum'] == saved_firmware_info['ipsw_hash']:

                if os.path.exists(saved_firmware_info['ipsw_file_path']):
                    logger.info(f"Firmware {firmware_version} for device {device_identifier} is already downloaded "
                                f"(file name: {saved_firmware_info['ipsw_file_path']}).")
                    continue
                else:
                    logger.info(f"Redownloading firmware {firmware_version} for device {device_identifier}")

            else:
                logger.info(f"A newer firmware version was found for device {device_identifier}.")

        else:
            logger.info(f"No saved firmware for device {device_identifier}.")

        # Get the IPSW output filename.
        output_filename = os.path.basename(urlparse(ipsw_data['url']).path)

        # Download the IPSW file.
        with httpx.stream("GET", ipsw_data['url']) as response, open(output_filename, "wb") as output_file:
            download_progress_bar = tqdm(total=ipsw_data['filesize'], desc=f"Downloading {output_filename}", unit='iB', unit_scale=True)
            for data in response.iter_bytes():
                download_progress_bar.update(len(data))
                output_file.write(data)

        # Verify the file against the SHA1 hash in the API response.
        verify_progress_bar = tqdm(total=ipsw_data['filesize'], desc=f"Verifying {output_filename}", unit='iB', unit_scale=True)
        file_hash = hashlib.sha1()
        with open(output_filename, "rb") as output_file:
            block = output_file.read(HASH_BLOCK_SIZE)
            while len(block) > 0:
                file_hash.update(block)
                verify_progress_bar.update(len(block))
                block = output_file.read(HASH_BLOCK_SIZE)

        # If it doesn't match, delete it.
        if file_hash.hexdigest() != ipsw_data['sha1sum']:
            logger.error(f"Downloaded file hash {file_hash.hexdigest()} does not match expected hash {ipsw_data['sha1sum']}.")
            os.remove(output_filename)
            continue

        # If it matches, save the IPSW data
        grabber_config.save_device_firmware_info(sanitised_device_identifier, output_filename, ipsw_data['sha1sum'])


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
