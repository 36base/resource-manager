import os
import socket
import zipfile
import requests
from pathlib import Path
import pyjson5
from datetime import datetime

from tqdm import tqdm
from tqdm.contrib.concurrent import thread_map

from urllib import request
from urllib.error import URLError

from logger_tt import logger

update_check_url = 'https://api.github.com/repos/gf-data-tools/gf-resource-downloader/releases'
resdata_url = 'https://github.com/gf-data-tools/gf-resource-downloader/releases/download/ResData/resdata.zip'
ab_keys = ['BaseAssetBundles', 'AddAssetBundles', 'passivityAssetBundles']

def singleDownload(url: str, path: str, max_retry: int = 3, timeout_sec: float = 30):
    socket.setdefaulttimeout(timeout_sec)
    fname = os.path.split(path)[-1]
    # logger.info(f"Downloading {url} - {fname}")

    for _ in range(max_retry):
        try:
            if not os.path.exists(path):
                request.urlretrieve(url, path)
        except KeyboardInterrupt as e:
            raise e
        except (URLError, TimeoutError, ConnectionResetError):
            continue
        else:
            break
    else:
        tqdm.write(f"failed to download {fname}")
        return False
    
    return True

class Downloader:
    def __init__(self, out_dir: str = './result'):
        os.makedirs(out_dir, exist_ok=True)
        self.tasks = []
        self.out_dir = out_dir

    def download(self, region: str = 'ch', download_keys: list[int] = [0, 1, 2]):
        logger.info(f'checking new version...')
        with open('./resdata_update_time.txt', 'r+') as f:
            written_time = f.read()
            last_update_time = datetime.min if written_time == '' else datetime.strptime(written_time, '%Y-%m-%dT%H:%M:%SZ')
            latest_online_time = requests.get(update_check_url).json()[0]['published_at']
            latest_time = datetime.strptime(latest_online_time, '%Y-%m-%dT%H:%M:%SZ')
            if latest_time > last_update_time:
                logger.info(f'an update has been found!')
                Path('resdata.zip').unlink(missing_ok=True)
                if singleDownload(url = resdata_url, path = './resdata.zip'):
                    f.seek(0)
                    f.write(latest_online_time)
                    f.truncate()
                    zipfile.ZipFile('resdata.zip').extractall('./resdata')

        with open(f'resdata/{region}_resdata.json', 'r', encoding='utf-8') as f:
            res_data = pyjson5.load(f)

        res_url = res_data['resUrl']

        for d in download_keys:
            key = ab_keys[d]
            for bundle in res_data[key]:
                resname = bundle['resname'] + '.ab'
                abname = bundle['assetBundleName'] + '.ab'
                size = bundle['sizeOriginal']
                res_path = os.path.join(self.out_dir, abname)
                if os.path.exists(res_path):
                    if os.path.getsize(res_path) == size:
                        continue
                    else:
                        os.remove(res_path)
                self.tasks.append([res_url + resname, res_path])

        for bundle in res_data['bytesData']:
            if bundle['fileInABC'] in download_keys:
                resname = bundle['resname'] + '.bytes'
                abname = bundle['fileName'] + '.bytes'
                size = bundle['sizeCompress']
                res_path = os.path.join(self.out_dir, abname)
                if os.path.exists(res_path):
                    if os.path.getsize(res_path) == size:
                        continue
                    else:
                        os.remove(res_path)
                self.tasks.append([res_url + resname, res_path])
    
        if len(self.tasks) == 0:
            logger.info(f'all files are latest version.')
        else:
            logger.info(f'beginning download...')
            thread_map(lambda t: singleDownload(*t), self.tasks, max_workers = 10)