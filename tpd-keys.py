import base64
import hmac
import hashlib
import sys
import time

from bs4 import BeautifulSoup

if sys.version_info[0] >= 3:
    from urllib.parse import urlparse
else:
    from urlparse import urlparse

from pywidevine.cdm import Cdm
from pywidevine.device import Device
from pywidevine.pssh import PSSH
from base64 import b64encode
import re
import requests
import json
import random
import uuid
import httpx
import sqlite3
import DRMHeaders2
from requests.utils import dict_from_cookiejar
import http
from os import urandom

MyWVD = "google_aosp_on_ia_emulator_14.0.0_b206f572_4464_l3.wvd"

dbconnection = sqlite3.connect("database.db")
dbcursor = dbconnection.cursor()
dbcursor.execute(
    'CREATE TABLE IF NOT EXISTS "DATABASE" ( "pssh" TEXT, "keys" TEXT, PRIMARY KEY("pssh") )'
)
dbconnection.close()


class Settings:
    def __init__(self, userCountry: str = None, randomProxy: bool = False) -> None:
        self.randomProxy = randomProxy
        self.userCountry = userCountry
        self.ccgi_url = "https://client.hola.org/client_cgi/"
        self.ext_ver = self.get_ext_ver()
        self.ext_browser = "chrome"
        self.user_uuid = uuid.uuid4().hex
        self.user_agent = "Mozilla/5.0 (X11; Fedora; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"
        self.product = "cws"
        self.port_type_choice: str
        self.zoneAvailable = [
            "AR",
            "AT",
            "AU",
            "BE",
            "BG",
            "BR",
            "CA",
            "CH",
            "CL",
            "CO",
            "CZ",
            "DE",
            "DK",
            "ES",
            "FI",
            "FR",
            "GR",
            "HK",
            "HR",
            "HU",
            "ID",
            "IE",
            "IL",
            "IN",
            "IS",
            "IT",
            "JP",
            "KR",
            "MX",
            "NL",
            "NO",
            "NZ",
            "PL",
            "RO",
            "RU",
            "SE",
            "SG",
            "SK",
            "TR",
            "UK",
            "US",
            "GB",
        ]

    def get_ext_ver(self) -> str:
        about = httpx.get("https://hola.org/access/my/settings#/about").text
        if 'window.pub_config.init({"ver":"' in about:
            version = about.split('window.pub_config.init({"ver":"')[1].split('"')[0]
            return version

        # last know working version
        return "1.199.485"


class Engine:
    def __init__(self, Settings) -> None:
        self.settings = Settings

    def get_proxy(self, tunnels, tls=False) -> str:
        login = f"user-uuid-{self.settings.user_uuid}"
        proxies = dict(tunnels)
        protocol = "https" if tls else "http"
        for k, v in proxies["ip_list"].items():
            return "%s://%s:%s@%s:%d" % (
                protocol,
                login,
                proxies["agent_key"],
                k if tls else v,
                proxies["port"][self.settings.port_type_choice],
            )

    def generate_session_key(self, timeout: float = 10.0) -> json:
        post_data = {"login": "1", "ver": self.settings.ext_ver}
        return httpx.post(
            f"{self.settings.ccgi_url}background_init?uuid={self.settings.user_uuid}",
            json=post_data,
            headers={"User-Agent": self.settings.user_agent},
            timeout=timeout,
        ).json()["key"]

    def zgettunnels(
        self, session_key: str, country: str, timeout: float = 10.0
    ) -> json:
        qs = {
            "country": country.lower(),
            "limit": 1,
            "ping_id": random.random(),
            "ext_ver": self.settings.ext_ver,
            "browser": self.settings.ext_browser,
            "uuid": self.settings.user_uuid,
            "session_key": session_key,
        }

        return httpx.post(
            f"{self.settings.ccgi_url}zgettunnels", params=qs, timeout=timeout
        ).json()


class Hola:
    def __init__(self, Settings) -> None:
        self.myipUri: str = "https://hola.org/myip.json"
        self.settings = Settings

    def get_country(self) -> str:
        if not self.settings.randomProxy and not self.settings.userCountry:
            self.settings.userCountry = httpx.get(self.myipUri).json()["country"]

        if (
            not self.settings.userCountry in self.settings.zoneAvailable
            or self.settings.randomProxy
        ):
            self.settings.userCountry = random.choice(self.settings.zoneAvailable)

        return self.settings.userCountry


def cache_key(cpssh: str, ckeys: str):
    dbconnection = sqlite3.connect("database.db")
    dbcursor = dbconnection.cursor()
    dbcursor.execute("INSERT or REPLACE INTO database VALUES (?, ?)", (cpssh, ckeys))
    dbconnection.commit()
    dbconnection.close()


def init_proxy(data):
    settings = Settings(
        data["zone"]
    )  # True if you want random proxy each request / "DE" for a proxy with region of your choice (German here) / False if you wish to have a proxy localized to your IP address
    settings.port_type_choice = data[
        "port"
    ]  # direct return datacenter ipinfo, peer "residential" (can fail sometime)

    hola = Hola(settings)
    engine = Engine(settings)

    userCountry = hola.get_country()
    session_key = engine.generate_session_key()
    #    time.sleep(10)
    tunnels = engine.zgettunnels(session_key, userCountry)

    return engine.get_proxy(tunnels)


def calculate_signature(method, url, headers, payload, timestamp=None):
    app_id = "SKYSHOWTIME-ANDROID-v1"
    signature_key = bytearray("jfj9qGg6aDHaBbFpH6wNEvN6cHuHtZVppHRvBgZs", "utf-8")
    sig_version = "1.0"

    if not timestamp:
        timestamp = int(time.time())

    if url.startswith("http"):
        parsed_url = urlparse(url)
        path = parsed_url.path
    else:
        path = url

    # print('path: {}'.format(path))

    text_headers = ""
    for key in sorted(headers.keys()):
        if key.lower().startswith("x-skyott"):
            text_headers += key + ": " + headers[key] + "\n"
    # print(text_headers)
    headers_md5 = hashlib.md5(text_headers.encode()).hexdigest()
    # print(headers_md5)

    if sys.version_info[0] > 2 and isinstance(payload, str):
        payload = payload.encode("utf-8")
    payload_md5 = hashlib.md5(payload).hexdigest()

    to_hash = (
        "{method}\n{path}\n{response_code}\n{app_id}\n{version}\n{headers_md5}\n"
        "{timestamp}\n{payload_md5}\n"
    ).format(
        method=method,
        path=path,
        response_code="",
        app_id=app_id,
        version=sig_version,
        headers_md5=headers_md5,
        timestamp=timestamp,
        payload_md5=payload_md5,
    )
    # print(to_hash)

    hashed = hmac.new(signature_key, to_hash.encode("utf8"), hashlib.sha1).digest()
    signature = base64.b64encode(hashed).decode("utf8")

    return 'SkyOTT client="{}",signature="{}",timestamp="{}",version="{}"'.format(
        app_id, signature, timestamp, sig_version
    )


allowed_countries = [
    "AR",
    "AT",
    "AU",
    "BE",
    "BG",
    "BR",
    "CA",
    "CH",
    "CL",
    "CO",
    "CZ",
    "DE",
    "DK",
    "ES",
    "FI",
    "FR",
    "GR",
    "HK",
    "HR",
    "HU",
    "ID",
    "IE",
    "IL",
    "IN",
    "IS",
    "IT",
    "JP",
    "KR",
    "MX",
    "NL",
    "NO",
    "NZ",
    "PL",
    "RO",
    "RU",
    "SE",
    "SG",
    "SK",
    "TR",
    "UK",
    "US",
    "GB",
]

print("Welcome to TPD-Keys! \n")
print("[Generic Services]")
print("1. Generic without any headers")
print("2. Generic with generic headers")
print("3. Generic with headers from DRMHeaders2.py")
print("4. JSON Widevine challenge, headers from DRMHeaders2.py \n")
print("[Specific Services]")
print("5. Canal+ Live TV")
print("6. YouTube VOD")
print("7. VDOCipher")
print("8. SkyShowTime\n")
selection = 6

if selection == 1:
    print("")
    print("Generic without headers.")
    ipssh = input("PSSH: ")
    pssh = PSSH(ipssh)
    device = Device.load(MyWVD)
    cdm = Cdm.from_device(device)
    session_id = cdm.open()
    challenge = cdm.get_license_challenge(session_id, pssh)
    ilicurl = input("License URL: ")
    country_code = input("Proxy? (2 letter country code or N for no): ")
    if len(country_code) == 2 and country_code.upper() in allowed_countries:
        proxy = init_proxy({"zone": country_code, "port": "peer"})
        proxies = {"http": proxy}
        print(f"Using proxy {proxies['http']}")
        licence = requests.post(ilicurl, proxies=proxies, data=challenge)
    else:
        print("Proxy-less request.")
        licence = requests.post(ilicurl, data=challenge)
    licence.raise_for_status()
    cdm.parse_license(session_id, licence.content)
    fkeys = ""
    for key in cdm.get_keys(session_id):
        if key.type != "SIGNING":
            fkeys += key.kid.hex + ":" + key.key.hex() + "\n"
    cache_key(ipssh, fkeys)
    print("")
    print(fkeys)
    cdm.close(session_id)

elif selection == 2:
    print("")
    print("Generic with generic headers.")
    ipssh = input("PSSH: ")
    pssh = PSSH(ipssh)
    device = Device.load(MyWVD)
    cdm = Cdm.from_device(device)
    session_id = cdm.open()
    challenge = cdm.get_license_challenge(session_id, pssh)
    ilicurl = input("License URL: ")
    country_code = input("Proxy? (2 letter country code or N for no): ")
    generic_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
    }
    if len(country_code) == 2 and country_code.upper() in allowed_countries:
        proxy = init_proxy({"zone": country_code, "port": "peer"})
        proxies = {"http": proxy}
        print(f"Using proxy {proxies['http']}")
        licence = requests.post(
            ilicurl, data=challenge, headers=generic_headers, proxies=proxies
        )
    else:
        print("Proxy-less request.")
        licence = requests.post(ilicurl, data=challenge, headers=generic_headers)
    licence.raise_for_status()
    cdm.parse_license(session_id, licence.content)
    fkeys = ""
    for key in cdm.get_keys(session_id):
        if key.type != "SIGNING":
            fkeys += key.kid.hex + ":" + key.key.hex() + "\n"
    cache_key(ipssh, fkeys)
    print("")
    print(fkeys)
    cdm.close(session_id)

elif selection == 3:
    print("")
    print("Generic with headers from DRMHeaders2.py")
    ipssh = input("PSSH: ")
    pssh = PSSH(ipssh)
    device = Device.load(MyWVD)
    cdm = Cdm.from_device(device)
    session_id = cdm.open()
    challenge = cdm.get_license_challenge(session_id, pssh)
    ilicurl = input("License URL: ")
    country_code = input("Proxy? (2 letter country code or N for no): ")
    if len(country_code) == 2 and country_code.upper() in allowed_countries:
        proxy = init_proxy({"zone": country_code, "port": "peer"})
        proxies = {"http": proxy}
        print(f"Using proxy {proxies['http']}")
        licence = requests.post(
            ilicurl, data=challenge, headers=DRMHeaders2.headers, proxies=proxies
        )
    else:
        print("Proxy-less request.")
        licence = requests.post(ilicurl, data=challenge, headers=DRMHeaders2.headers)
    licence.raise_for_status()
    cdm.parse_license(session_id, licence.content)
    fkeys = ""
    for key in cdm.get_keys(session_id):
        if key.type != "SIGNING":
            fkeys += key.kid.hex + ":" + key.key.hex() + "\n"
    cache_key(ipssh, fkeys)
    print("")
    print(fkeys)
    cdm.close(session_id)

elif selection == 4:
    print("")
    print("JSON Widevine challenge, headers from DRMHeaders2.py")
    ipssh = input("PSSH: ")
    pssh = PSSH(ipssh)
    device = Device.load(MyWVD)
    cdm = Cdm.from_device(device)
    session_id = cdm.open()
    challenge = cdm.get_license_challenge(session_id, pssh)
    request = b64encode(challenge)
    ilicurl = input("License URL: ")
    pid = input("releasePid: ")
    country_code = input("Proxy? (2 letter country code or N for no): ")
    if len(country_code) == 2 and country_code.upper() in allowed_countries:
        proxy = init_proxy({"zone": country_code, "port": "peer"})
        proxies = {"http": proxy}
        print(f"Using proxy {proxies['http']}")
        licence = requests.post(
            ilicurl,
            headers=DRMHeaders2.headers,
            proxies=proxies,
            json={
                "getRawWidevineLicense": {
                    "releasePid": pid,
                    "widevineChallenge": str(request, "utf-8"),
                }
            },
        )
    else:
        print("Proxy-less request.")
        licence = requests.post(
            ilicurl,
            headers=DRMHeaders2.headers,
            json={
                "getRawWidevineLicense": {
                    "releasePid": pid,
                    "widevineChallenge": str(request, "utf-8"),
                }
            },
        )
    licence.raise_for_status()
    cdm.parse_license(session_id, licence.content)
    fkeys = ""
    for key in cdm.get_keys(session_id):
        if key.type != "SIGNING":
            fkeys += key.kid.hex + ":" + key.key.hex() + "\n"
    cache_key(ipssh, fkeys)
    print("")
    print(fkeys)
    cdm.close(session_id)

elif selection == 5:
    print("")
    print("Canal+ Live TV")
    ipssh = input("PSSH: ")
    channel = input("Channel: ")
    live_token = input("Live Token: ")
    pssh = PSSH(ipssh)
    device = Device.load(MyWVD)
    cdm = Cdm.from_device(device)
    session_id = cdm.open()
    challenge = cdm.get_license_challenge(session_id, pssh)
    request = b64encode(challenge)
    ilicurl = "https://secure-browser.canalplus-bo.net/WebPortal/ottlivetv/api/V4/zones/cpfra/devices/31/apps/1/jobs/GetLicence"
    country_code = input("Proxy? (2 letter country code or N for no): ")
    if len(country_code) == 2 and country_code.upper() in allowed_countries:
        proxy = init_proxy({"zone": country_code, "port": "peer"})
        proxies = {"http": proxy}
        print(f"Using proxy {proxies['http']}")
        licence = requests.post(
            ilicurl,
            headers=DRMHeaders2.headers,
            proxies=proxies,
            json={
                "ServiceRequest": {
                    "InData": {
                        "EpgId": channel,
                        "LiveToken": live_token,
                        "UserKeyId": "_sdivii9vz",
                        "DeviceKeyId": "1676391356366-a3a5a7d663de",
                        "ChallengeInfo": f"{base64.b64encode(challenge).decode()}",
                        "Mode": "MKPL",
                    },
                },
            },
        )
    else:
        print("Proxy-less request.")
        licence = requests.post(
            ilicurl,
            headers=DRMHeaders2.headers,
            json={
                "ServiceRequest": {
                    "InData": {
                        "EpgId": channel,
                        "LiveToken": live_token,
                        "UserKeyId": "_jprs988fy",
                        "DeviceKeyId": "1678334845207-61e4e804264c",
                        "ChallengeInfo": f"{base64.b64encode(challenge).decode()}",
                        "Mode": "MKPL",
                    },
                },
            },
        )
    licence.raise_for_status()
    cdm.parse_license(
        session_id, licence.json()["ServiceResponse"]["OutData"]["LicenseInfo"]
    )
    fkeys = ""
    for key in cdm.get_keys(session_id):
        if key.type != "SIGNING":
            fkeys += key.kid.hex + ":" + key.key.hex() + "\n"
    cache_key(ipssh, fkeys)
    print("")
    print(fkeys)
    cdm.close(session_id)

elif selection == 6:
    print("")
    print("YouTube")
    ipssh = "AAAAQXBzc2gAAAAA7e+LqXnWSs6jyCfc1R0h7QAAACEiGVlUX01FRElBOjZlMzI4ZWQxYjQ5YmYyMWZI49yVmwY="
    ilicurl = "https://tv.youtube.com/youtubei/v1/player/get_drm_license?alt=json&key=AIzaSyD-L7DIyuMgBk-B4DYmjJZ5UG-D6Y-vkMc"
    pssh = PSSH(ipssh)
    device = Device.load(MyWVD)
    cdm = Cdm.from_device(device)
    session_id = cdm.open()
    challenge = cdm.get_license_challenge(session_id, pssh)
    country_code = "N"
    json_data = DRMHeaders2.json_data
    json_data["videoId"] = sys.argv[1]
    json_data["drmParams"] = sys.argv[2]
    json_data["licenseRequest"] = base64.b64encode(challenge).decode("utf-8")
    if len(country_code) == 2 and country_code.upper() in allowed_countries:
        proxy = init_proxy({"zone": country_code, "port": "peer"})
        proxies = {"http": proxy}
        print(f"Using proxy {proxies['http']}")
        licence = requests.post(
            ilicurl,
            cookies=DRMHeaders2.cookies,
            headers=DRMHeaders2.headers,
            proxies=proxies,
            json=json_data,
        )
    else:
        print("Proxy-less request.")
        licence = requests.post(
            ilicurl,
            cookies=DRMHeaders2.cookies,
            headers=DRMHeaders2.headers,
            json=json_data,
        )

    licence.raise_for_status()
    cdm.parse_license(
        session_id, licence.json()["license"].replace("-", "+").replace("_", "/")
    )
    fkeys = ""
    for key in cdm.get_keys(session_id):
        if key.type != "SIGNING":
            fkeys += key.kid.hex + ":" + key.key.hex() + "\n"
    cache_key(ipssh, fkeys)
    print("")
    print(fkeys)
    cdm.close(session_id)

elif selection == 7:
    url = input("\nEnter the URL: ")

    headers = {
        "accept": "*/*",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
        ## Comment this line out if using for anything other than https://www.vdocipher.com/blog/2014/12/add-text-to-videos-with-watermark/
        "Origin": f"https://{urandom(8).hex()}.com",
    }

    response = requests.get(url, cookies=DRMHeaders2.cookies, headers=headers)

    try:
        otp_match = re.findall(r"otp: '(.*)',", response.text)[0]
        playbackinfo_match = re.findall(r"playbackInfo: '(.*)',", response.text)[0]
    except IndexError:
        try:
            otp_match = re.findall(r"otp=(.*)&", response.text)[0]
            playbackinfo_match = re.findall(r"playbackInfo=(.*)", response.text)[0]
        except IndexError:
            print("\nAn error occured while getting otp/playback")
            exit()

    video_id = json.loads(base64.b64decode(playbackinfo_match).decode())["videoId"]

    response = requests.get(
        f"https://dev.vdocipher.com/api/meta/{video_id}", headers=headers
    )

    try:
        lic_url = response.json()["dash"]["licenseServers"][
            "com.widevine.alpha"
        ].rsplit(":", 1)[0]
        mpd = response.json()["dash"]["manifest"]
    except KeyError:
        print("\n An error occured while getting mpd/license url")

    response = requests.get(mpd, headers=headers)

    pssh = re.search(r"<cenc:pssh>(.*)</cenc:pssh>", response.text).group(1)
    device = Device.load(MyWVD)
    cdm = Cdm.from_device(device)
    session_id = cdm.open()
    challenge = cdm.get_license_challenge(session_id, PSSH(pssh))

    token = {
        "otp": otp_match,
        "playbackInfo": playbackinfo_match,
        "href": url,
        "tech": "wv",
        "licenseRequest": f"{base64.b64encode(challenge).decode()}",
    }

    json_data = {
        "token": f'{base64.b64encode(json.dumps(token).encode("utf-8")).decode()}',
    }

    response = requests.post(lic_url, headers=headers, json=json_data)

    try:
        lic_b64 = response.json()["license"]
    except KeyError:
        print(f'An error occured while getting license: {response.json()["message"]}')
        exit()

    cdm.parse_license(session_id, lic_b64)
    fkeys = ""

    print(f"\nMPD Link:")
    print(f"{mpd}\n")

    for key in cdm.get_keys(session_id):
        if key.type != "SIGNING":
            fkeys += key.kid.hex + ":" + key.key.hex() + "\n"
    cache_key(pssh, fkeys)
    print("")
    print(fkeys)
    cdm.close(session_id)

elif selection == 8:
    print("")
    print("SkyShowTime")

    token_url = "https://ovp.skyshowtime.com/auth/tokens"
    vod_url = "https://ovp.skyshowtime.com/video/playouts/vod"

    cookies = DRMHeaders2.cookies
    region = cookies["activeTerritory"]

    # Getting tokens
    headers = {
        "accept": "application/vnd.tokens.v1+json",
        "content-type": "application/vnd.tokens.v1+json",
    }

    post_data = {
        "auth": {
            "authScheme": "MESSO",
            "authIssuer": "NOWTV",
            "provider": "SKYSHOWTIME",
            "providerTerritory": region,
            "proposition": "SKYSHOWTIME",
        },
        "device": {
            "type": "MOBILE",
            "platform": "ANDROID",
            "id": "Z-sKxKApSe7c3dAMGAYtVU8NmWKDcWrCKobKpnVTLqc",  # Value seems to be irrelavant
            "drmDeviceId": "UNKNOWN",
        },
    }
    post_data = json.dumps(post_data)
    headers["x-sky-signature"] = calculate_signature(
        "POST", token_url, headers, post_data
    )
    userToken = json.loads(
        requests.post(
            token_url, cookies=cookies, headers=headers, data=post_data
        ).content
    )["userToken"]
    del headers
    del post_data

    # Getting license and manifest url
    video_url = input("Enter SkyShowTime video url: ")
    content_id = video_url.split("/")[6]
    provider_variant_id = video_url.split("/")[7][:36]

    post_data = {
        "providerVariantId": provider_variant_id,
        "device": {
            "capabilities": [
                {
                    "transport": "DASH",
                    "protection": "NONE",
                    "vcodec": "H265",
                    "acodec": "AAC",
                    "container": "ISOBMFF",
                },
                {
                    "transport": "DASH",
                    "protection": "WIDEVINE",
                    "vcodec": "H265",
                    "acodec": "AAC",
                    "container": "ISOBMFF",
                },
                {
                    "transport": "DASH",
                    "protection": "NONE",
                    "vcodec": "H264",
                    "acodec": "AAC",
                    "container": "ISOBMFF",
                },
                {
                    "transport": "DASH",
                    "protection": "WIDEVINE",
                    "vcodec": "H264",
                    "acodec": "AAC",
                    "container": "ISOBMFF",
                },
            ],
            "model": "SM-N986B",
            "maxVideoFormat": "HD",
            "hdcpEnabled": "false",
            "supportedColourSpaces": ["SDR"],
        },
        "client": {"thirdParties": ["COMSCORE", "CONVIVA", "FREEWHEEL"]},
        "personaParentalControlRating": 9,
    }
    post_data = json.dumps(post_data)

    headers = {
        "accept": "application/vnd.playvod.v1+json",
        "content-type": "application/vnd.playvod.v1+json",
        "x-skyott-activeterritory": region,
        "x-skyott-agent": "skyshowtime.mobile.android",
        "x-skyott-country": region,
        "x-skyott-device": "MOBILE",
        "x-skyott-platform": "ANDROID",
        "x-skyott-proposition": "SKYSHOWTIME",
        "x-skyott-provider": "SKYSHOWTIME",
        "x-skyott-territory": region,
        "x-skyott-usertoken": userToken,
    }
    headers["x-sky-signature"] = calculate_signature(
        "POST", vod_url, headers, post_data
    )

    vod_request = json.loads(
        requests.post(vod_url, headers=headers, data=post_data).content
    )

    license_url = vod_request["protection"]["licenceAcquisitionUrl"]
    manifest_url = vod_request["asset"]["endpoints"][0]["url"]

    # Getting pssh

    manifest = requests.get(manifest_url).content
    pssh = PSSH(BeautifulSoup(manifest, "html.parser").findAll("cenc:pssh")[1].text)

    # CDM processing

    device = Device.load(MyWVD)
    cdm = Cdm.from_device(device)
    session_id = cdm.open()
    challenge = cdm.get_license_challenge(session_id, pssh)

    headers = {
        "Content-Type": "application/octet-stream",
    }

    licence = requests.post(license_url, headers=headers, data=challenge)
    licence.raise_for_status()
    cdm.parse_license(session_id, licence.content)

    fkeys = ""

    print(f"\nMPD Link:")
    print(f"{manifest_url}\n")

    for key in cdm.get_keys(session_id):
        if key.type != "SIGNING":
            fkeys += key.kid.hex + ":" + key.key.hex()
    cache_key(str(pssh), fkeys)
    print(fkeys)
    cdm.close(session_id)

else:
    print("Invalid selection")
