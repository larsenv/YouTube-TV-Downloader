import DRMHeaders
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

try:
    key_audio = output.split(b"\n")[-6].decode("utf-8")
except:
    key_audio = output.split(b"\n")[-2].decode("utf-8")

try:
    key_video = output.split(b"\n")[-8].decode("utf-8")
except:
    key_video = output.split(b"\n")[-4].decode("utf-8")

print("Video URL:", manifest_url)
print("Key Audio:", key_audio)
print("Key Video:", key_video)

print("\n")

print(manifest_url.replace("%", "%%"))

os.system(
    (".\\" if platform.system() == "Windows" else "")
    + "yt-dlp"
    + " "
    + "-f"
    + " "
    + '"'
    + "mp4"
    + '"'
    + " "
    + "--output"
    + " "
    + '"'
    + video_id
    + "-encrypted.mp4"
    + '"'
    + " "
    + "--allow-unplayable-formats"
    + " "
    + '"'
    + manifest_url
    + '"'
)
os.system(
    (".\\" if platform.system() == "Windows" else "")
    + "yt-dlp"
    + " "
    + "-f"
    + " "
    + '"'
    + "149:ChAKBWFjb250EgdwcmltYXJ5"
    + '"'
    + " "
    + "--output"
    + " "
    + '"'
    + video_id
    + "-encrypted.m4a"
    + '"'
    + " "
    + "--allow-unplayable-formats"
    + " "
    + '"'
    + manifest_url
    + '"'
)
os.system(
    (".\\" if platform.system() == "Windows" else "")
    + "yt-dlp"
    + " "
    + "-f"
    + " "
    + '"'
    + "m4a"
    + '"'
    + " "
    + "--output"
    + " "
    + '"'
    + video_id
    + "-encrypted.m4a"
    + '"'
    + " "
    + "--allow-unplayable-formats"
    + " "
    + '"'
    + manifest_url
    + '"'
)
os.system(
    (".\\" if platform.system() == "Windows" else "")
    + "yt-dlp"
    + " "
    + "-f"
    + " "
    + '"'
    + "149:ChIKBWFjb250EglzZWNvbmRhcnk"
    + '"'
    + " "
    + "--output"
    + " "
    + '"'
    + video_id
    + "-secondary-encrypted.m4a"
    + '"'
    + " "
    + "--allow-unplayable-formats"
    + " "
    + '"'
    + manifest_url
    + '"'
)
os.system(
    (".\\" if platform.system() == "Windows" else "")
    + "shaka-packager"
    + " "
    + "in="
    + video_id
    + "-encrypted.mp4"
    + ",stream=video,output="
    + video_id
    + "-decrypted.mp4"
    + " "
    + "--enable_raw_key_decryption"
    + " "
    + "--keys"
    + " "
    + "key_id="
    + key_video.split(":")[0]
    + ":key="
    + key_video.split(":")[1]
)
os.system(
    (".\\" if platform.system() == "Windows" else "")
    + "shaka-packager"
    + " "
    + "in="
    + video_id
    + "-encrypted.m4a"
    + ",stream=audio,output="
    + video_id
    + "-decrypted.m4a"
    + " "
    + "--enable_raw_key_decryption"
    + " "
    + "--keys"
    + " "
    + "key_id="
    + key_audio.split(":")[0]
    + ":key="
    + key_audio.split(":")[1]
)
os.system(
    (".\\" if platform.system() == "Windows" else "")
    + "shaka-packager"
    + " "
    + "in="
    + video_id
    + "-secondary-encrypted.m4a"
    + ",stream=audio,output="
    + video_id
    + "-secondary-decrypted.m4a"
    + " "
    + "--enable_raw_key_decryption"
    + " "
    + "--keys"
    + " "
    + "key_id="
    + key_audio.split(":")[0]
    + ":key="
    + key_audio.split(":")[1]
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
        caption_command[1].append(
            str(
                (3 if os.path.exists(video_id + "-secondary-decrypted.m4a") else 2)
                + caption_num
            )
        )
        caption_command[1].append("-c:s")
        caption_command[1].append("mov_text")
        caption_command[1].append("-metadata:s:s:" + str(caption_num))
        caption_command[1].append("language=" + c["languageCode"])
        caption_command[1].append("-metadata:s:s:" + str(caption_num))
        caption_command[1].append("title=" + '"' + c["trackName"] + '"')
        caption_num += 1
except:
    pass
if os.path.exists(video_id + "-secondary-decrypted.m4a"):
    os.system(
        (".\\" if platform.system() == "Windows" else "")
        + "ffmpeg"
        + " "
        + "-i"
        + " "
        + '"'
        + video_id
        + "-decrypted.mp4"
        + '"'
        + " "
        + "-i"
        + " "
        + '"'
        + video_id
        + "-decrypted.m4a"
        + '"'
        + " "
        + "-i"
        + " "
        + '"'
        + video_id
        + "-secondary-decrypted.m4a"
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
        + "0:v"
        + " "
        + "-map"
        + " "
        + "1:a"
        + " "
        + "-map"
        + " "
        + "2:a"
        + " "
        + " ".join(caption_command[1])
        + " "
        + '"'
        + title.translate(str.maketrans("", "", string.punctuation))
        + ".mp4"
        + '"'
    )
else:
    os.system(
        (".\\" if platform.system() == "Windows" else "")
        + "ffmpeg"
        + " "
        + "-i"
        + " "
        + '"'
        + video_id
        + "-decrypted.mp4"
        + '"'
        + " "
        + "-i"
        + " "
        + '"'
        + video_id
        + "-decrypted.m4a"
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
        + "0:v"
        + " "
        + "-map"
        + " "
        + "1:a"
        + " "
        + " ".join(caption_command[1])
        + " "
        + '"'
        + title.translate(str.maketrans("", "", string.punctuation))
        + ".mp4"
        + '"'
    )

os.system(("del" if platform.system() == "Windows" else "rm") + " " + video_id + "*")
