# YouTube TV Downloader

This'll let you download YouTube TV content which is recorded or on demand by running youtubetv.py. You will need a YouTube TV account and a Widevine CDM L3.

You will have to install the requirements by running `pip install -r requirements.txt`, then you can run youtubetv.py by running `python youtubetv.py <video ID>`.

A WVD of your Widevine CDM L3 needs to be in the directory. If your CDM isn't in that format, you can run `pywidevine create-device -k "/PATH/TO/device_private_key" -c "/PATH/TO/device_client_id_blob" -t "ANDROID" -l 3`.

Furthermore, you will have to input your credentials.

1. Go to YouTube TV and play some recording or something which is on video on demand."
2. Open developer mode of your browser. Search for `player` on Network. Do a right-click on the URL -> Copy -> Copy as cURL.
3. Go to https://curlconverter.com/ and paste the content. Select Python in the options of the output, then copy everything except the first line and the code starting with the line with `response = requests.post`. Paste it into a new file called DRMHeaders.py.
4. Repeat Steps 2 and 3 but search `get_drm_headers` and paste the converted contents into a new file called DRMHeaders2.py.

TPD94 created his ripper named TPD-Keys which this uses in order to download
