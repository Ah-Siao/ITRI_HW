import pickle
from PIL import Image
import PIL.ImageOps
import numpy as np
from pathlib import Path
from tensorflow.keras.preprocessing import image
import pandas as pd
import os
import re
directory = Path(__file__).resolve().parent

label = {0: '1000g合進麵線の味關廟麵',
         1: '58°金門高粱酒',
         2: 'FMC 小分子檸檬氣泡水',
         3: 'FMC 小分子氣泡水',
         4: 'FMC鹼性離子水',
         5: '元本山味付海苔',
         6: '咖啡因洗髮精',
         7: '大豆沙拉油(1L)',
         8: '安心豚原味貢丸 360克',
         9: '安心豚梅花肉片200公克',
         10: '安心豚海苔芝麻肉酥 200克',
         11: '安心豚白玉五花肉片200公克',
         12: '安心豚紅麴肉酥 200克',
         13: '安心豚葵花油肉酥 200克',
         14: '安心豚里肌火鍋肉片200公克',
         15: '愛之味純濃燕麥(天然原味)',
         16: '春風抽取式衛生紙',
         17: '核桃杏香酥',
         18: '桃花輕盈沐浴乳',
         19: '橘子工坊五合一洗衣金球',
         20: '歐萊德保濕護髮素(木蘭香)',
         21: '泡舒植物強效洗潔精965ml(1000g)',
         22: '泰山TWIST WATER環保包裝水(包裝飲用水)',
         23: '淨毒五郎蔬果清潔劑補充瓶(1000ml)',
         24: '生活泡沫奶茶 300ml',
         25: '生活泡沫紅茶 300ml',
         26: '生活泡沫綠茶 300ml',
         27: '生活運動飲料 300ml',
         28: '白御粉絲(3kg)',
         29: '福壽100％芝麻油',
         30: '竹萃保濕護髮素',
         31: '米',
         32: '紅龍牌日正粉絲(3kg)',
         33: '紐西蘭天然無水奶油10KG',
         34: '紐西蘭天然無水奶油900G',
         35: '素媽媽-川味朝天椒香烤肉片',
         36: '統一陽光陽光黃金豆豆漿',
         37: '統一麵肉燥風味特大號(85g)',
         38: '茶樹洗手乳',
         39: '茶花控油洗髮精',
         40: '蒲公英環保抽取式擦手紙巾',
         41: '蒲公英環保抽取式衛生紙',
         42: '蛋',
         43: '野菽家營養棒-蜂蜜檸檬',
         44: '金獎鳳黃酥',
         45: '雀巢金牌濾掛咖啡100％阿拉比卡柑橘果香',
         46: '香豬油王-調合豬油',
         47: '麥香奶茶TP300ml',
         48: '麥香紅茶TP300ml',
         49: '麥香綠茶TP300ml',
         50: '黑松FIN補給飲料',
         51: '黑松沙士',
         52: '黑松茶花綠茶'}


# def convert_unit(x):
#     if 'kg' in x:
#         numbers = re.findall(r'\d+\.\d+', x)
#         return float(numbers[0])*1000
#     else:
#         numbers = re.findall(r'\d+\.\d+', x)
#         return float(numbers[0])


def recog_pic(pic_name):
    with open(directory/"cnn_model53_SGD.pickle", 'rb') as f:
        clf_load = pickle.load(f)
    test_image = image.load_img(directory/"../static/uploaded/" /
                                pic_name, target_size=(150, 150))
    test_image = image.img_to_array(test_image)
    test_image = np.expand_dims(test_image, axis=0)
    result = clf_load.predict(test_image/255)
    model_label = int(np.argmax(result, axis=1))

    mypic = Image.open(directory/"../static/uploaded/"/pic_name)
    max_size = 500
    width, height = mypic.size
    if width > height:
        new_width = max_size
        new_height = int(height * (max_size / width))
    else:
        new_height = max_size
        new_width = int(width * (max_size / height))
    resized_image = mypic.resize((new_width, new_height))
    resized_image.save(directory/"../static/uploaded/"/pic_name)

    return model_label


# open the image file
