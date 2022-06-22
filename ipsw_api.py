import httpx
import typing

from tqdm import tqdm

IPSW_ME_BASE_URL = "https://api.ipsw.me"
IPSW_ME_GET_FIRMWARES_FOR_DEVICE = "/v4/device/$device"


async def get_ipsw_list(device_identifier: str, limit: int = 0) -> typing.List:
    if limit < 0:
        raise Exception(f"Expected a limit value of 0 or greater, got {limit}.")

    async with httpx.AsyncClient() as client:
        response: httpx.Response = await client.get(IPSW_ME_BASE_URL + IPSW_ME_GET_FIRMWARES_FOR_DEVICE
                                                    .replace("$device", device_identifier),
                                                    params={
                                                        "type": "ipsw"
                                                    })

        if response.status_code is 404:
            raise Exception(f"Invalid device identifier \"{device_identifier}\".")
        elif response.status_code is not 200:
            raise Exception(f"Error fetching IPSWs for device \"{device_identifier}\".")

        if limit is not 0:
            return response.json()['firmwares'][0:limit]
        else:
            return response.json()['firmwares']


async def download_file(output_filename: str, firmware_data: typing.Dict):
    with httpx.stream("GET", firmware_data['url']) as response, open(output_filename, "wb") as output_file:
        download_progress_bar = tqdm(total=firmware_data['filesize'], desc=f"Downloading {output_filename}", unit='iB',
                                     unit_scale=True)
        for data in response.iter_bytes():
            download_progress_bar.update(len(data))
            output_file.write(data)
