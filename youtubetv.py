import DRMHeaders
import DRMHeaders2
import os
import platform
import re
import requests
import shutil
import subprocess
import string
import sys
import tpdyoutube


def get_manifest_url(video_id):
    response = requests.post(
        "https://tv.youtube.com/youtubei/v1/player",
        params=DRMHeaders.params,
        cookies=DRMHeaders.cookies,
        headers=DRMHeaders.headers,
        json=DRMHeaders.json_data,
    )

    return [
        response.json()["streamingData"]["drmParams"],
        response.json()["streamingData"]["dashManifestUrl"],
        (
            response.json()["captions"]["playerCaptionsTracklistRenderer"][
                "captionTracks"
            ]
            if "captions" in response.json()
            else None
        ),
        response.json()["videoDetails"]["title"],
    ]


print("YouTube TV Downloader by Larsenv\n")

video_id = DRMHeaders2.json_data["videoId"]
video_url = get_manifest_url(video_id)
param = video_url[0]
manifest_url = video_url[1]
caption = video_url[2]
title = video_url[3]

output = tpdyoutube.decrypt_content(
    "https://tv.youtube.com/youtubei/v1/player/get_drm_license?alt=json&key=AIzaSyD-L7DIyuMgBk-B4DYmjJZ5UG-D6Y-vkMc",
    video_id,
    param,
).encode("utf-8")

print("Video URL:", manifest_url, "\n")

print("Key:\n\n" + output.decode("utf-8"))

os.system(
    (".\\" if platform.system() == "Windows" else "")
    + "N_m3u8DL-RE"
    + " "
    + '"'
    + manifest_url
    + '"'
    + " "
    + "--save-name"
    + " "
    + '"'
    + video_id
    + '"'
    + " "
    + "--auto-select"
    + " "
    + "--mux-after-done"
    + " "
    + "format=mp4"
    + " "
    + "--decryption-engine"
    + " "
    + "mp4decrypt"
    + " "
    + "--key"
    + " "
    + " --key ".join(output.decode("utf-8").split("\n"))[:-7]
)

shutil.move(
    video_id + ".mp4",
    title.translate(str.maketrans("", "", string.punctuation)) + ".mp4",
)

caption_num = 0

try:
    for c in caption:
        with open(
            title.translate(str.maketrans("", "", string.punctuation))
            + "-"
            + str(caption_num)
            + ".xml",
            "wb",
        ) as f:
            f.write(requests.get(c["baseUrl"]).content)

        try:
            subprocess.run(
                [
                    sys.executable,
                    "convertsrt.py",
                    title.translate(str.maketrans("", "", string.punctuation))
                    + "-"
                    + str(caption_num)
                    + ".xml",
                ],
                check=True,  # This will raise an error if the command fails
            )

        except:
            continue

        if not os.path.exists(
            title.translate(str.maketrans("", "", string.punctuation))
            + "-"
            + str(caption_num)
            + ".srt"
        ):
            continue

        caption_num += 1
except:
    pass

os.system(("del" if platform.system() == "Windows" else "rm") + " " + "*.xml")
