# import dependencies
import os
from pywidevine import PSSH
from pywidevine import Cdm
from pywidevine import Device
import requests
import glob
import DRMHeaders2
import base64

# Get the current working directory
main_directory = os.getcwd()

# Making sure a .wvd file exists and using that as the extracted device
try:
    extracted_device = glob.glob("*.wvd")[0]
except:
    extracted_cdm = None
    print(f"Please place a WVD in {main_directory}")


# Defining decrypt function
def decrypt_content(license_url, video_id, drmparams):

    # prepare pssh
    pssh = PSSH(
        "AAAAQXBzc2gAAAAA7e+LqXnWSs6jyCfc1R0h7QAAACEiGVlUX01FRElBOjZlMzI4ZWQxYjQ5YmYyMWZI49yVmwY="
    )

    # load device
    device = Device.load(extracted_device)

    # load CDM from device
    cdm = Cdm.from_device(device)

    # open CDM session
    session_id = cdm.open()

    # Generate the challenge
    challenge = cdm.get_license_challenge(session_id, pssh)

    DRMHeaders2.json_data["videoId"] = video_id
    DRMHeaders2.json_data["drmParams"] = drmparams
    DRMHeaders2.json_data["licenseRequest"] = base64.b64encode(challenge).decode()

    # send license challenge
    license = requests.post(
        url=license_url,
        cookies=DRMHeaders2.cookies,
        headers=DRMHeaders2.headers,
        json=DRMHeaders2.json_data,
    )

    # Replace invalid characters
    try:
        license = license.json()["license"].replace("-", "+").replace("_", "/")
        
        # Parse the license
        cdm.parse_license(session_id, license)
    
        # assign variable for returned keys
        returned_keys = ""
        for key in cdm.get_keys(session_id):
            if key.type != "SIGNING":
                returned_keys += f"{key.kid.hex}:{key.key.hex()}\n"
    
        # close session, disposes of session data
        cdm.close(session_id)
    except:
        print("Error grabbing license / keys. Try copying the license again")
        print("If the problem persists, it's possible that your Widevine CDM is bad")
        print("Or this content might be using L1 Widevine which is not tested on this script")

    # Return the keys
    return returned_keys
