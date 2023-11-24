![example workflow](https://github.com/xljones/tuya-tray/actions/workflows/lint-and-test.yml/badge.svg)

# Tuya Tray

Tuya Tray is a taskbar application to control SmartLife/Tuya smart devices.

## Installation

### Configuration

First, configure a `.config.json` using the `tuya.sh` script, where
* `EMAIL` is the email address used to login to Tuya or SmartLife
* `PASSWORD` is the password used to login to Tuya or SmartLife
* `COUNTRY_CODE` is the phone code for the region where you are (`44` for the UK `1` for USA)
* `APPLICATION` is one of `tuya` or `smart_life`, depending on which service you use

```sh
./tuya.sh -c EMAIL PASSWORD COUNTRY_CODE APPLICATION
```

or you can manually configure a `.config.json`, based on the provided `config.example.json`

### Run the app

Now you can install the application (on the first run) and run it with:

```sh
./tuya.sh
```

This will do the following:
* install a local virtual environment `./venv`
* Install dependencies
* Login using your `.config.json` data
* Launch the menu bar application
* Save your session data for quick logins

or, you can manually install and run the application with

```sh
python -m pip install -r requirements.txt && python -m tuya
```

## Example

![image](https://github.com/xljones/tuya-tray/assets/9535852/a0b2c8d9-6227-4060-b5c3-d567e99f3d4a)


### Todos

* Light brightness
* Scene grouping
* Better, less manual login system
* Encode password in temporary files, or use Keychain
