import os
from logger_tt import setup_logging

from functions.downloader import Downloader
from functions.extractor import Extractor

# ch, tw, kr, us, jp
# choose one!
region = 'ch'

out_dir = './assets'
extract_out_dir = './result'

# you can choose what to download.
download = [0, 1]
#0 / BaseAssetBundles = minimal game file needs to boot.
#1 / AddAssetBundles = contains extra assets which requires full-game experience.
#2 / passivityAssetBundles = contains voice, 2K images for hi-res device.

if __name__ == '__main__':
    setup_logging(config_path='./log_config.json')

    downloader = Downloader(out_dir = out_dir)
    extractor = Extractor(out_dir = extract_out_dir)

    downloader.download(region = region, download_keys = download)
    extractor.extract()

    os.system('pause')