# -*- coding: utf-8 -*-
"""
Created on Sat May 16 15:25:34 2020

@author: john
"""

import cv2
import numpy as np
import math
from os import walk, path



def get_fileNames(rootdir):
    data = []
    prefix = []
    for root, dirs, files in walk(rootdir, topdown=True):
        for name in files:
            pre, ending = path.splitext(name)
            if ending != ".jpg" and ending != ".jepg" and ending != ".png":
                continue
            else:
                data.append(path.join(root, name))
                prefix.append(pre)
    return data, prefix

def NLmean(img,ds,Ds,sigma):
    '''
    ds：块半径
    Ds：搜索半径
    '''
    h1,w1 = img.shape
    #图像输入类型为uint8，需转为int32，否则在后续距离计算中会出现溢出等现象
    paddedImg = np.pad(img,((Ds+ds+1,Ds+ds+1),(Ds+ds+1,Ds+ds+1)),'symmetric').astype(np.int32)
    print(paddedImg.dtype)
    denoisedImg = np.zeros((h1,w1))
    d2 = (2*ds+1)*(2*ds+1)
    h = 0.4 * sigma
    h2 = h*h
    for i in range(h1):
        for j in range(w1):
            i1 = i+ds
            j1 = j+ds
            W1 = paddedImg[i1-ds:i1+ds+1,j1-ds:j1+ds+1]
            wmax=0
            average=0
            sweight=0
            #搜索域遍历范围
            rmin = max(i1-Ds,ds)
            rmax = min(i1+Ds,h1+Ds)
            smin = max(j1-Ds,ds)
            smax = min(j1+Ds,w1+Ds)
            for r in range(rmin,rmax+1):
                for s in range(smin,smax+1):
                    if (r==i1 and s==j1):
                        continue
                    else:
                        W2 = paddedImg[r-ds:r+ds+1,s-ds:s+ds+1]
                        #计算平均距离
                        distance = np.sum(np.square(W1-W2))/d2
                        w = np.exp(-max(distance-2*sigma**2,0.0)/h2)
                        if(w>wmax):
                            wmax =w
                        sweight = sweight + w
                        average = average + w*paddedImg[r,s]
            average = average + wmax*paddedImg[i1,j1]
            sweight = sweight + wmax
            denoisedImg[i,j]= average/sweight
    return np.uint8(denoisedImg)

#...........................................................................................
def calc_sigt(I,threshval):
	M,N = I.shape
	ulim = np.uint8(np.max(I))
	N1 = np.count_nonzero(I>threshval)
	N2 = np.count_nonzero(I<=threshval)
	w1 = np.float64(N1)/(M*N)
	w2 = np.float64(N2)/(M*N)
	#print N1,N2,w1,w2
	try:
		u1 = np.sum(i*np.count_nonzero(np.multiply(I>i-0.5,I<=i+0.5))/N1 for i in range(threshval+1,ulim))
		u2 = np.sum(i*np.count_nonzero(np.multiply(I>i-0.5,I<=i+0.5))/N2 for i in range(threshval+1))
		uT = u1*w1+u2*w2
		sigt = w1*w2*(u1-u2)**2
		#print u1,u2,uT,sigt
	except:
		return 0
	return sigt
# ...........................................................................................
def get_threshold(I):
    max_sigt = 0
    opt_t = 0
    ulim = np.uint8(np.max(I))
    #print(ulim)
    for t in range(ulim + 1):
        sigt = calc_sigt(I, t)
        # print t, sigt
        if sigt > max_sigt:
            max_sigt = sigt
            opt_t = t
    #print('optimal high threshold: ', opt_t)
    return opt_t


# 画线
def drawlines(img,lines):
    try:
        length=len(lines)
    except:
        return img
    else:
        for line in lines:
            rho, theta = line[0]
            a = np.cos(theta)
            b = np.sin(theta)
            x0 = rho * a
            y0 = rho * b
            # k1*k2=-1 ==> k2=-1/k1
            # k1 = tan(θ) ==> k2 = -1/tan(θ)=-cot(θ)
            x1 = int(x0 + 1000 * (-b))
            y1 = int(y0 + 1000 * a)
            x2 = int(x0 - 1000 * (-b))
            y2 = int(y0 - 1000 * a)
            # 画线
            cv2.line(img, (x1, y1), (x2, y2), (0, 0, 255), 1)
    return img

def drawoneline(img,lines):
    try:
        length=len(lines)
    except:
        return img
    else:
        line=lines[0]
        rho, theta = line[0]
        a = np.cos(theta)
        b = np.sin(theta)
        x0 = rho * a
        y0 = rho * b
        # k1*k2=-1 ==> k2=-1/k1
        # k1 = tan(θ) ==> k2 = -1/tan(θ)=-cot(θ)
        x1 = int(x0 + 1000 * (-b))
        y1 = int(y0 + 1000 * a)
        x2 = int(x0 - 1000 * (-b))
        y2 = int(y0 - 1000 * a)
        # 画线
        cv2.line(img, (x1, y1), (x2, y2), (0, 0, 255), 1)
    return img

def drawonePline(img,lines):
    try:
        length=len(lines)
    except:
        return img
    else:
        line=lines[0]
        # 画线
        cv2.line(img, (line[0][0], line[0][1]), (line[0][2], line[0][3]), (0, 0, 255), 1)
    return img

images, preifx = get_fileNames("D:/pyproject/20191102m-7/cut/NoMask-21/")  # 得到指定文件夹下的图片，例如.jpg，.jepg或.png等，可根据上述代码更改


def EndAnalyse(img,edge_t,edge_l):
    lineNum=0
    denoise=cv2.fastNlMeansDenoising(img, None, 15, 2, 5)
    clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(2, 2))
    cl1 = clahe.apply(denoise)
    th = get_threshold(cl1)
    edge1 = cv2.Canny(cl1, th / 3, th)
    x = edge1.shape[0]
    y = edge1.shape[1]
    crossline = math.sqrt(x * x + y * y)
    # 霍夫变换检测直线
    for j in range(100, 20, -1):
        lines = cv2.HoughLinesP(edge1, 1, np.pi / 180, j, minLineLength=int(0.75 * y), maxLineGap=int(0.1 * crossline))
        try:
            length = len(lines)
        except:
            j = j
        else:
            if length < 2:
                break
    try:
        length=len(lines)
    except:
        lineNum=0
        line=[[0,0,0,0]]
    else:
        lineNum=length
        line=lines[0]
    return lineNum, line[0][0]+edge_t, line[0][1]+edge_l, line[0][2]+edge_t, line[0][3]+edge_l

for i in range(len(images)):
    img = cv2.imread(images[i], 0)
    #NLM滤波去除噪声
    img = cv2.fastNlMeansDenoising(img, None, 15, 2, 5)
    #img = NLmean(img, 2, 5, 15)
    #获得均值化后的图像
    #默认值：clahe=cv2.createCLAHE(clipLimit=4.0,tileGridSize=(8,8))
    clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(2, 2))
    cl1 = clahe.apply(img)
    #cv2.imwrite("D:/pyproject/20191102m-7/cut/cl1/{}.jpg".format(preifx[i]), cl1)
    #边缘检测
    th = get_threshold(cl1)
    edge1=cv2.Canny(cl1,th/3,th)
    x = edge1.shape[0]
    y = edge1.shape[1]
    crossline=math.sqrt(x*x+y*y)
    #霍夫变换检测直线
    for j in range(100,20,-1):
        lines = cv2.HoughLinesP(edge1, 1, np.pi / 180, j,minLineLength=int(0.75*y),maxLineGap=int(0.1*crossline))
        try:
            length=len(lines)
        except:
            j=j
        else:
            if length<2:
                break
    line1=drawonePline(img,lines)
    #自适应的阈值确定的方法：大津算法
    #ret1, th1 = cv2.threshold(img, 0, 255, cv2.THRESH_OTSU)  # 方法选择为THRESH_OTSU
    #保存文件
    cv2.imwrite("D:/pyproject/20191102m-7/cut/{}.jpg".format(preifx[i]), line1)

