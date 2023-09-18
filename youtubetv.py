import DRMHeaders
import glob
import json
import platform
import requests
import sys
import subprocess


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

output = subprocess.check_output(["python3.9", "tpd-keys.py", video_id, param])

key_audio = output.split(b"\n")[-3].decode("utf-8")
key_video = output.split(b"\n")[-5].decode("utf-8")

print(output)

print("Video URL:", manifest_url)
print("Key Audio:", key_audio)
print("Key Video:", key_video)

print("\n")

if platform.system() != "Windows":
    print("Saving script to download video into file called run.sh.")

    with open("run.sh", "w") as f:
        f.write(
            "yt-dlp"
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
            + "\n"
        )
        f.write(
            "yt-dlp"
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
            + "\n"
        )
        f.write(
            "mp4decrypt --key"
            + " "
            + '"'
            + key_video
            + '"'
            + " "
            + '"'
            + video_id
            + "-encrypted.mp4"
            + '"'
            + " "
            + '"'
            + video_id
            + "-decrypted.mp4"
            + '"'
            + "\n"
        )
        f.write(
            "mp4decrypt --key"
            + " "
            + '"'
            + key_audio
            + '"'
            + " "
            + '"'
            + video_id
            + "-encrypted.m4a"
            + '"'
            + " "
            + '"'
            + video_id
            + "-decrypted.m4a"
            + '"'
            + "\n"
        )
        f.write("rm" + " " + '"' + video_id + "-encrypted.mp4" + '"' + "\n")
        f.write("rm" + " " + '"' + video_id + "-encrypted.m4a" + '"' + "\n")
        f.write(
            "ffmpeg"
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
            + "\n"
        )
        f.write("rm" + " " + '"' + video_id + "-decrypted.mp4" + '"' + "\n")
        f.write("rm" + " " + '"' + video_id + "-decrypted.m4a" + '"' + "\n")

    print("Running run.sh.")

    subprocess.call(["sh", "./run.sh"])

    print("Done.")

else:
    print("Saving script to download video into file called run.bat.")

    with open("run.bat", "w") as f:
        f.write(
            ".\yt-dlp"
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
            + manifest_url.replace("%", "%%")
            + '"'
            + "\n"
        )
        f.write(
            ".\yt-dlp"
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
            + manifest_url.replace("%", "%%")
            + '"'
            + "\n"
        )
        f.write(
            ".\mp4decrypt --key"
            + " "
            + '"'
            + key_video
            + '"'
            + " "
            + '"'
            + video_id
            + "-encrypted.mp4"
            + '"'
            + " "
            + '"'
            + video_id
            + "-decrypted.mp4"
            + '"'
            + "\n"
        )
        f.write(
            ".\mp4decrypt --key"
            + " "
            + '"'
            + key_audio
            + '"'
            + " "
            + '"'
            + video_id
            + "-encrypted.m4a"
            + '"'
            + " "
            + '"'
            + video_id
            + "-decrypted.m4a"
            + '"'
            + "\n"
        )
        f.write("del" + " " + '"' + video_id + "-encrypted.mp4" + '"' + "\n")
        f.write("del" + " " + '"' + video_id + "-encrypted.m4a" + '"' + "\n")
        f.write(
            ".\\ffmpeg"
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
            + "\n"
        )
        f.write("del" + " " + '"' + video_id + "-decrypted.mp4" + '"' + "\n")
        f.write("del" + " " + '"' + video_id + "-decrypted.m4a" + '"' + "\n")

    print("Running run.bat.")

    subprocess.call(["run.bat"])

    print("Done.")
