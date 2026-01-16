# coding: utf-8

import os
import sys
import subprocess
from pytesser_pro.pytesser_pro import *
import Image, ImageEnhance, ImageFilter



# 二值化并转格式
def binary(image_name, binary_image_name):
    # 白底黑字
    args = "convert -monochrome "+image_name+" "+binary_image_name
    # print args
    proc = subprocess.Popen(args, shell=True)
    proc.wait()
    im = Image.open(binary_image_name)
    w, h = im.size
    data = list(im.getdata())
    if (data[0], data[w-1], data[(h-1)*w], data[h*w-1]) == (0, 0, 0, 0): # 0-黑色，255-白色
        # 若非白底黑字则灰度反转
        args1 = "convert -negate "+binary_image_name+" "+binary_image_name
        proc1 = subprocess.Popen(args1, shell=True)
        proc1.wait()

# 计算范围内点的个数
def numpoint(im):
    """Count black pixels - optimized with sum() instead of nested loops"""
    data = im.getdata()
    # Count black pixels (value 0) using sum with generator expression
    return sum(1 for pixel in data if pixel == 0)

# 投影法去干扰线
def pointmidu(binary_image_name, midu_image_name):
    im = Image.open(binary_image_name)
    w, h = im.size
    step = 5

    # Load pixel data once for faster access
    pixels = im.load()

    # Process in chunks - clear low-density regions
    for x in range(0, w, step):
        box = (x, 0, min(x + step, w), h)
        im_box = im.crop(box)
        num = numpoint(im_box)
        if num < 20:
            # Use pixels directly instead of putpixel for better performance
            for i in range(x, min(x + step, w)):
                for j in range(h):
                    pixels[i, j] = 255

    # Calculate column density in a single pass
    data = list(im.getdata())
    data_column = [
        sum(1 for y in range(h) if data[y * w + x] == 0)
        for x in range(w)
    ]

    # Find content boundaries
    start = next((i for i, val in enumerate(data_column) if val != 0), 0)
    end = next((i for i in range(w - 1, -1, -1) if data_column[i] != 0), w - 1)

    # Crop and save
    box_new = (start, 0, end + 1, h)
    im_box_new = im.crop(box_new)
    im_box_new.save(midu_image_name)

# 图像增强
def filter_enhance(midu_image_name, midu_image_name_pro1):
    im = Image.open(midu_image_name)
    # 去噪
    im = im.filter(ImageFilter.MedianFilter())
    # 亮度加强
    enhancer = ImageEnhance.Contrast(im)
    im = enhancer.enhance(2)
    im = im.convert('1')
    # im.show()
    im.save(midu_image_name_pro1)

# 字符分割
def seg(midu_image_name_pro1, midu_image_name_pro2, num):
    im = Image.open(midu_image_name_pro1)
    w, h = im.size
    # print w, h, w/num
    len = 2
    for i in range(num-1):
        start = (i+1)*w/num
        end = start+len
        for m in range(start, end+1):
            for n in range(h):
                im.putpixel((m, n), 255) # 0-黑色，255-白色
    im.save(midu_image_name_pro2)

def get_aim1_point(im):
    """Find first black pixel from top in each column"""
    w, h = im.size
    data = list(im.getdata())
    aim = []
    for x in range(w):
        for y in range(h):
            if data[y * w + x] == 0:
                aim.append((x, y))
                break
    return aim


def get_aim2_point(im):
    """Find first black pixel from bottom in each column"""
    w, h = im.size
    data = list(im.getdata())
    aim = []
    for x in range(w):
        for y in range(h - 1, -1, -1):
            if data[y * w + x] == 0:
                aim.append((x, y))
                break
    return aim


if __name__=='__main__':

    if len(sys.argv) == 1:
        image_name = "./pic/get_random.jpg" # 验证码图片名称
        digits = False
        # image_name = "./pic/get_price_img.png" # 价格图片名称
        # digits = True
    elif len(sys.argv) == 2:
        if sys.argv[1].find("get_random") != -1:
            image_name = sys.argv[1]
            digits = False
        elif sys.argv[1].find("get_price_img") != -1:
            image_name = sys.argv[1]
            digits = True
        else:
            print "Please Input the Correct Image Name!"
            sys.exit(0)
    else:
        print "Too Many Arguments!"
        sys.exit(0)


    # 二值化并转格式
    binary_image_name = os.path.splitext(image_name)[0]+"_binary.png"
    binary(image_name, binary_image_name)

    im = Image.open(binary_image_name)
    print im.format, im.size, im.mode


    if digits:
        text = image_file_to_string(binary_image_name, bool_digits=digits)
        print text.replace("\n", "")
    else:
        # 投影法去干扰线
        fpathandname , fext = os.path.splitext(binary_image_name)
        midu_image_name = fpathandname+"_midu"+fext
        pointmidu(binary_image_name, midu_image_name)


        fpathandname , fext = os.path.splitext(midu_image_name)

        # 去干扰线
        # im = Image.open(midu_image_name)
        # w, h = im.size
        # data = list(im.getdata())
        # aim1 = get_aim1_point(im)
        # for x, y in aim1:
        #     curr = data[y*w+x]
        #     prev = data[(y-1)*w+x]
        #     next = data[(y+1)*w+x]
        #
        #     if prev == 0 and next == 0: # 0-黑色，255-白色
        #         continue
        #     if prev == 0:
        #         im.putpixel((x, y), 255)
        #         im.putpixel((x, y-1), 255)
        #     elif next == 0:
        #         im.putpixel((x, y), 255)
        #         im.putpixel((x, y+1), 255)
        #     else:
        #         im.putpixel((x, y), 255)
        # data = list(im.getdata())
        # aim2 = get_aim2_point(im)
        # for x, y in aim2:
        #     curr = data[y*w+x]
        #     prev = data[(y-1)*w+x]
        #     next = data[(y+1)*w+x]
        #
        #     if prev == 0 and next == 0: # 0-黑色，255-白色
        #         continue
        #     if prev == 0:
        #         im.putpixel((x, y), 255)
        #         im.putpixel((x, y-1), 255)
        #     elif next == 0:
        #         im.putpixel((x, y), 255)
        #         im.putpixel((x, y+1), 255)
        #     else:
        #         im.putpixel((x, y), 255)
        # midu_image_name_new = fpathandname+"_new"+fext
        # im.save(midu_image_name_new)


        # 图像增强
        midu_image_name_pro1 = fpathandname+"_pro1"+fext
        filter_enhance(midu_image_name, midu_image_name_pro1)
        # 字符分割
        # num = 4
        # midu_image_name_pro2 = fpathandname+"_pro2"+fext
        # seg(midu_image_name_pro1, midu_image_name_pro2, num)

        # im = Image.open(midu_image_name)
        # text = image_to_string(im)
        # print text.replace("\n", "")
        text = image_file_to_string(midu_image_name_pro1, bool_digits=digits)
        print text.replace("\n", "")