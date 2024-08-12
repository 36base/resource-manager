import os
import time
import cv2
import numpy as np
import UnityPy

from tqdm import tqdm
from tqdm.contrib.concurrent import thread_map
from logger_tt import logger

def getTexture2D(data):
    return data.m_RD.texture.read().image

def combineAlphaChannel(rgb, alpha, file):
    rgb = np.array(rgb)
    rgb_height, rgb_width, rgb_channel = rgb.shape

    a = np.array(alpha)
    alpha_height, alpha_width, _ = a.shape

    #RGB24
    if rgb_channel == 3:
        rgb = cv2.cvtColor(rgb, cv2.COLOR_RGB2RGBA)

    if a.shape[:2] != rgb.shape[:2]:
        a = cv2.resize(a, None, fx=rgb_width / alpha_width, fy=rgb_height / alpha_height)
    
    rgb[:, :, [0, 1, 2]] = rgb[:, :, [2, 1, 0]]
    rgb[:, :, 3] = a[:, :, 3]
    cv2.imencode(".png", rgb)[1].tofile(file)

def assetExtract(file_path: str, out_dir: str):
    #icontemplate 항목은 무조건 에러가 나서, 그냥 버림
    if 'icontemplate' in file_path:
        return True
    
    env = UnityPy.load(file_path)
    for path, obj in env.container.items():
        try:
            if obj.type.name == 'Sprite':
                data = obj.read()
                dest = os.path.join(out_dir, *path.split('/'))
                os.makedirs(os.path.dirname(dest), exist_ok = True)
                dest, _ = os.path.splitext(dest)

                #이미지가 이미 있으면 그냥 넘어감.
                if os.path.exists(dest + '.png'):
                    continue

                #ETC_RGB4는 alpha 이미지가 있으므로 합쳐줘야 함
                if '_alpha' in dest:
                    file = path.replace('_alpha', '')
                    original = getTexture2D(env.container.get(file).read())
                    alpha = getTexture2D(data)

                    combineAlphaChannel(original, alpha, dest.replace('_alpha', '') + '.png')
                    continue
                else:
                    dest = dest + '.png'
                    data.image.save(dest)
            if obj.type.name == 'TextAsset':
                data = obj.read()
                dest = os.path.join(out_dir, *path.split('/'))
                os.makedirs(os.path.dirname(dest), exist_ok = True)
                dest, _ = os.path.splitext(dest)
                dest = dest + '.txt'
                with open(dest, 'wb') as f:
                    f.write(bytes(data.script))
        except Exception as e:
            tqdm.write(f'failed to extract {file_path} - {data.name} ({e})')
            continue

    return True

class Extractor:
    def __init__(self, in_dir: str = './assets', out_dir: str = './result'):
        self.tasks = []
        self.in_dir = in_dir
        self.out_dir = out_dir

    def extract(self):
        logger.info('extracting ab files... this will take some time.')
        start_time = time.time()

        for root, _, files in os.walk(self.in_dir):
            for file_name in files:
                # logger.info(f'{file_name}')
                file_path = os.path.join(root, file_name)

                if 'ab' in file_name:
                    self.tasks.append([file_path, self.out_dir])

        thread_map(lambda t: assetExtract(*t), self.tasks, max_workers = 10)

        end_time = time.time()
        logger.info(f'extraction complete. elapsed time: {end_time - start_time}')