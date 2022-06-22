import httpx
import typing

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

        if response.status_code == 404:
            raise Exception(f"Invalid device identifier \"{device_identifier}\".")
        elif response.status_code != 200:
            raise Exception(f"Error fetching IPSWs for device \"{device_identifier}\".")

        if limit != 0:
            return response.json()['firmwares'][0:limit]
        else:
            return response.json()['firmwares']
