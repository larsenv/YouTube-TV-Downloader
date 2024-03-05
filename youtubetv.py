import DRMHeaders
import os
import platform
import requests
import sys
import subprocess
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
    ]


print("YouTube TV Downloader by Larsenv\n")

if len(sys.argv) != 2:
    print("Usage: youtubetv.py <video_id>")

    sys.exit(1)

video_id = sys.argv[1]
video_url = get_manifest_url(video_id)
param = video_url[0]
manifest_url = video_url[1]

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
        + '"'
        + video_id
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
        + "-c"
        + " "
        + '"'
        + "copy"
        + '"'
        + " "
        + '"'
        + video_id
        + ".mp4"
        + '"'
    )
os.system(
    ("del" if platform.system() == "Windows" else "rm")
    + " "
    + '"'
    + video_id
    + "-encrypted.mp4"
    + '"'
)
os.system(
    ("del" if platform.system() == "Windows" else "rm")
    + " "
    + '"'
    + video_id
    + "-encrypted.m4a"
    + '"'
)
os.system(
    ("del" if platform.system() == "Windows" else "rm")
    + " "
    + '"'
    + video_id
    + "-secondary-encrypted.m4a"
    + '"'
)
os.system(
    ("del" if platform.system() == "Windows" else "rm")
    + " "
    + '"'
    + video_id
    + "-decrypted.mp4"
    + '"'
)
os.system(
    ("del" if platform.system() == "Windows" else "rm")
    + " "
    + '"'
    + video_id
    + "-decrypted.m4a"
    + '"'
)
os.system(
    ("del" if platform.system() == "Windows" else "rm")
    + " "
    + '"'
    + video_id
    + "-secondary-decrypted.m4a"
    + '"'
)

print("Done.")
