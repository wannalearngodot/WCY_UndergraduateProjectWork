import os
import sys
import random
import math
import skimage.io
from skimage.measure import find_contours
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import patches,  lines
from matplotlib.patches import Polygon
import cv2
import scipy
import mrcnn.model as modellib
from mrcnn import utils
from mrcnn import visualize
from mrcnn.config import Config



class InferenceConfig(Config):   #继承自Config类，统一模型配置参数
    NAME = "manchu"#配置类的识别符
    # Set batch size to 1 since we'll be running inference on
    # one image at a time. Batch size = GPU_COUNT * IMAGES_PER_GPU
    GPU_COUNT = 1
    IMAGES_PER_GPU = 1
    NUM_CLASSES = 1 + 1 #根据自己类别修改
    #?
    IMAGE_MIN_DIM = 512  #图片的最小边长（根据自己图像修改，必须被64整除）
    IMAGE_MAX_DIM = 960  #图片的最大边长
    RPN_ANCHOR_SCALES = (8, 16, 32, 64, 128)

def display_instances(imglist, image, boxes, masks, class_ids, class_names,
                      scores=None, title="",
                      figsize=(16, 16), ax=None,
                      show_mask=True, show_bbox=True,
                      colors=None, captions=None):
    """
    boxes: [num_instance, (y1, x1, y2, x2, class_id)] in image coordinates.
    masks: [height, width, num_instances]
    class_ids: [num_instances]
    class_names: list of class names of the dataset
    scores: (optional) confidence scores for each box
    title: (optional) Figure title
    show_mask, show_bbox: To show masks and bounding boxes or not
    figsize: (optional) the size of the image
    colors: (optional) An array or colors to use with each object
    captions: (optional) A list of strings to use as captions for each object
    """

    # Number of instances
    N = boxes.shape[0]
    if not N:
        print("\n*** No instances to display *** \n")
    else:
        assert boxes.shape[0] == masks.shape[-1] == class_ids.shape[0]

    # If no axis is passed, create one and automatically call show()
    auto_show = False
    if not ax:
        _, ax = plt.subplots(1, figsize=figsize)
        auto_show = True

    # Generate random colors
    #colors = colors or random_colors(N)

    # Show area outside image boundaries.
    height, width = image.shape[:2]
    ax.set_ylim(height + 10, -10)
    ax.set_xlim(-10, width + 10)
    ax.axis('off')
    ax.set_title(title)

    masked_image = image.astype(np.uint32).copy()
    #list_centerx = []
    #list_centery = []
    list_center = []
    vert_set = []
    rect_set = []
    box_set = []
    for i in range(N):
        #color = colors[i]

        # Bounding box
        if not np.any(boxes[i]):
            # Skip this instance. Has no bbox. Likely lost in image cropping.
            continue
        y1, x1, y2, x2 = boxes[i]
        if show_bbox:
            p1 = patches.Rectangle((x1, y1), x2 - x1, y2 - y1, angle=0.0, linewidth=2,
                                  alpha=0.7, linestyle="solid",
                                  edgecolor="None", facecolor='none')  # 此处edgecolor可以去掉检测框
            ax.add_patch(p1)

        # Label
        if not captions:
            class_id = class_ids[i]
            score = scores[i] if scores is not None else None
            label = class_names[class_id]
            x = random.randint(x1, (x1 + x2) // 2)
            caption = "{} {:.3f}".format(label, score) if score else label
        else:
            caption = captions[i]
        ax.text(x1, y1 + 8, caption,
                color="None", size=11, backgroundcolor="None")  # 此处可设置标签颜色等

        # Mask
        mask = masks[:, :, i]
        # if show_mask:
        # masked_image = apply_mask(masked_image, mask, color)

        # Mask Polygon
        # Pad to ensure proper polygons for masks that touch image edges.
        padded_mask = np.zeros(
            (mask.shape[0] + 2, mask.shape[1] + 2), dtype=np.uint8)
        padded_mask[1:-1, 1:-1] = mask
        contours = find_contours(padded_mask, 0.5)
        # print(111111111)
        #print(contours)
        ####
        ####往txt里写掩码边界坐标
        #result2txt = str(contours)
        #f = open("./result2/%5s.txt" % (str(imglist[0:5])), 'a',
                 #encoding='utf-8')  ##ffilename可以是原来的txt文件，也可以没有然后把写入的自动创建成txt文件
        #f.write(result2txt)
        #f.write('\n')
        ####

        for verts in contours:
            # Subtract the padding and flip (y, x) to (x, y)
            verts = np.fliplr(verts) - 1
            verts=verts.tolist()
            vert_set.append(verts)
            # p = Polygon(verts, facecolor=color, edgecolor=color)  #facecolor可设置掩膜内是否有颜色
            p = Polygon(verts, facecolor="Blue", edgecolor="None")  # facecolor可设置掩膜内是否有颜色
            ax.add_patch(p)

            verts=np.array(verts,dtype=np.int0)
            rect=cv2.minAreaRect(verts)
            rotate_box=cv2.boxPoints(rect)
            rotate_box=np.int0(rotate_box)
            box_set.append(rotate_box)
            rect_set.append(rect)
            (w,h)=rect[1]
            rotate=rect[2]
            #rotate=math.atan((rotate_box[3][0]-rotate_box[3][1])/(rotate_box[0][1]-rotate_box[0][0]))/3.1415926*180
            #height=math.sqrt(math.pow(rotate_box[0][0]-rotate_box[1][0],2)+math.pow(rotate_box[0][1]-rotate_box[1][1],2))
            #width=math.sqrt(math.pow(rotate_box[0][0] - rotate_box[3][0], 2) + math.pow(rotate_box[0][1] - rotate_box[3][1], 2))
            #list_centerx.append(np.mean(rotate_box[:,0]))
            #list_centery.append(np.mean(rotate_box[:,1]))
            list_center.append((np.mean(rotate_box[:,0]),np.mean(rotate_box[:,1])))
            p2 = patches.Rectangle(rotate_box[1], abs(w), abs(h), angle=rotate, linewidth=2,
                                  alpha=1, linestyle="solid",
                                  edgecolor="Red", facecolor='none')
            ax.add_patch(p2)
            ax.text(rotate_box[3][0], rotate_box[3][1], str(rotate)+'degree',
                    color="Green", size=11, backgroundcolor="None")  # 此处可设置标签颜色等

            p3 = patches.Circle([np.mean(rotate_box[:,0]),np.mean(rotate_box[:,1])], radius=1, color='Red',
                                   alpha=1, linestyle="solid")
            ax.add_patch(p3)
    return vert_set, rect_set, box_set, list_center
    #centery=np.array(list_centery,dtype=np.int0)
    #centerx=np.array(list_centerx,dtype=np.int0)
    #print('length=' + str(len(centerx)))
    #spacey=np.linspace(min(centery),max(centery),500)
    #f_yx=scipy.interpolate.interp1d(centery,centerx, kind='cubic')
    #spacex=f_yx(spacey)
    #for curve_count in range(0,len(spacex)):
        #p_curve = patches.Circle([spacex[curve_count],spacey[curve_count]], radius=1, color='Red',
                                   #alpha=1, linestyle="solid")
        #ax.add_patch(p_curve)


        #if auto_show:
            #plt.savefig("./result1/%5s.png" % (str(imglist[0:5])))  # 在result1文件夹直接输出mask的边界图

    #ax.imshow(masked_image.astype(np.uint8))
    #if auto_show:
        #plt.savefig("./result/%5s.png" % (str(imglist[0:5])))
        # plt.show()

def mask_detect(img, model_path, weight_path):
    print("mask rcnn detect")
    config = InferenceConfig()
    config.display()
    # Create model object in inference mode.
    model = modellib.MaskRCNN(mode="inference", model_dir=model_path, config=config)
    # Load weights trained on MS-COCO
    model.load_weights(weight_path, by_name=True)
    class_names = ['BG', 'vertebral_segment']
    results = model.detect([img], verbose=1)
    r = results[0]
    # 这一步是画mask和写坐标的关键
    vert_set, rect_set, box_set, list_center=display_instances('result_img', img, r['rois'], r['masks'], r['class_ids'], class_names, r['scores'])
    return vert_set, rect_set, box_set, list_center

#设置函数参数
#ROOT_DIR = os.path.abspath("../")
# Directory to save logs and trained model--->model_path
#MODEL_DIR = os.path.join(ROOT_DIR, "mrcnndetect/logs/manchu20200526T2143")  # （改成自己生成的模型文件路径）
# Local path to trained weights file--->weight_path
#COCO_MODEL_PATH = os.path.join(MODEL_DIR, "mask_rcnn_manchu_0020.h5")  # （改成自己模型的文件名称）
#image to detect --->img
#img=cv2.imread('00021.jpg')

#运行函数
#返回三个值分别是：mask轮廓，最小外接矩形信息和最小外接矩形的顶点。其中最小外接矩形信息包括长宽和旋转角度，没有参与绘制，主要为了后面计算方便
#vert_set, rect_set, box_set=mask_detect(img,MODEL_DIR,COCO_MODEL_PATH)

#绘制图形
#用蓝色画mask轮廓并用红色填充，需要tolist转化为列表
#for i in range(0,len(vert_set)):
    #vert=np.empty((len(vert_set[i]),2),dtype=np.int32)
    #for j in range(0,len(vert_set[i])):
        #cv2.circle(img,(round(vert_set[i][j][0]),round(vert_set[i][j][1])),1,(255,0,0),-1)
        #vert[j, 0] = round(vert_set[i][j][0])
        #vert[j, 1] = round(vert_set[i][j][1])
    #cv2.fillPoly(img,[vert],(0,0,255))
#用绿色画mask的最小外接矩形
#for k in range(0,len(box_set)):
    #cv2.drawContours(img,[box_set[k]],0,(0,255,0),2)

#显示结果
#cv2.imshow('result',img)
#cv2.imwrite('resultimg.jpg',img)
#cv2.waitKey()


