import DRMHeaders
import DRMHeaders2
import os
import platform
import re
import requests
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

print("Keys:\n\n" + output.decode("utf-8"))

os.system(
    (".\\" if platform.system() == "Windows" else "")
    + "N_m3u8DL-RE"
    + " "
    + '"'
    + manifest_url
    + '"'
    + " "
    + "--decryption-engine"
    + " "
    + "shaka_packager"
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
    + "--key"
    + " "
    + " --key ".join(output.decode("utf-8").split("\n"))[:-7]
)
caption_num = 0
caption_command = [[], []]
try:
    for c in caption:
        with open(video_id + str(caption_num) + ".xml", "wb") as f:
            f.write(requests.get(c["baseUrl"]).content)

        try:
            subprocess.run(
                [sys.executable, "convertsrt.py", video_id + str(caption_num) + ".xml"],
                check=True,  # This will raise an error if the command fails
            )

        except:
            continue

        if not os.path.exists(video_id + str(caption_num) + ".srt"):
            continue

        caption_command[0].append("-i")
        caption_command[0].append(video_id + str(caption_num) + ".srt")
        caption_command[1].append("-map")
        caption_command[1].append("1")
        caption_command[1].append("-c:s")
        caption_command[1].append("mov_text")
        caption_command[1].append("-metadata:s:s:" + str(caption_num))
        caption_command[1].append("language=" + c["languageCode"])
        caption_command[1].append("-metadata:s:s:" + str(caption_num))
        caption_command[1].append("title=" + '"' + c["trackName"] + '"')
        caption_num += 1
except:
    pass
if os.path.exists(video_id + "0.srt"):
    os.system(
        (".\\" if platform.system() == "Windows" else "")
        + "ffmpeg"
        + " "
        + "-i"
        + " "
        + '"'
        + video_id
        + ".mp4"
        + '"'
        + " "
        + " ".join(caption_command[0])
        + " "
        + "-c"
        + " "
        + '"'
        + "copy"
        + '"'
        + " "
        + "-map"
        + " "
        + "0"
        + " "
        + " ".join(caption_command[1])
        + " "
        + '"'
        + title.translate(str.maketrans("", "", string.punctuation))
        + ".mp4"
        + '"'
    )
