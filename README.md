# ipsw-grabber
Python script to download and verify IPSWs for a given set of device identifiers, using the IPSW.me API

Requires Python >= 3.8 for the `async` keyword.

## Setup

- Create a virtual environment, if you wish. You don't have to, but it makes things a bit easier.
- `pip3 install -r requirements.txt` to install the dependencies.
- Make a copy of `config.example.toml` called `config.toml`.
- In `config.toml`, populate `device_list` with a comma-separated list of device identifiers. If you don't know what the device identifier is for your specific device, you can use [IPSW.me](https://ipsw.me) to find it.
- Run `main.py`.

## Limitations and TODOs

- [ ] OTA update support.
  - As it stands, this tool cannot download OTA updates for devices which support them (or for devices which Apple does not publish IPSWs for).
- [ ] Code refactor.
  - The structure of main.py isn't great, I wrote this tool in a bit of a hurry and it could do with refactoring.