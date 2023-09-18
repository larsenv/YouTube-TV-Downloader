# YouTube TV Downloader

This'll let you download YouTube TV content which is recorded or on demand by running youtubetv.py. You will need a YouTube TV account and a Widevine L3 CDM.

You will have to install the requirements by running "pip install -r requirements.txt", then you can run youtubetv.py by running "python youtubetv.py <video ID>".

Furthermore, you will have to input your credentials.

1. Go to YouTube TV and play some recording or something which is on video on demand."
2. Open developer mode of your browser. Search for "get_drm_license" on Network. Do a right-click on the URL -> Copy -> Copy as cURL.
3. Go to https://curlconverter.com/ and paste the content. Select Python in the options of the output, then copy everything except the first line and everything after and including the line starting with "response = requests.post". Paste it into DRMHeaders.py of TPD-Keys."

TPD94 created his ripper named TPD-Keys which this uses in order to download.