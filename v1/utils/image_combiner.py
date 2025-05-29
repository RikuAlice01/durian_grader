import cv2
import numpy as np

def combine_images_grid(images, grid_size=(2, 3), image_size=(320, 240)):
    """
    รวมภาพเป็นตาราง (grid) จาก list ของภาพ
    :param images: list ของภาพ (numpy.ndarray) หรือ None
    :param grid_size: (rows, cols)
    :param image_size: ขนาดภาพย่อยที่ resize ก่อนรวม
    :return: ภาพรวม (numpy.ndarray)
    """
    rows, cols = grid_size
    total_slots = rows * cols
    canvas_height = rows * image_size[1]
    canvas_width = cols * image_size[0]
    
    canvas = np.zeros((canvas_height, canvas_width, 3), dtype=np.uint8)

    for idx, img in enumerate(images[:total_slots]):
        row = idx // cols
        col = idx % cols
        x = col * image_size[0]
        y = row * image_size[1]
        
        if img is not None:
            resized = cv2.resize(img, image_size)
            canvas[y:y + image_size[1], x:x + image_size[0]] = resized
        else:
            # หากกล้องไม่มีภาพ ให้เติมสีเทา
            canvas[y:y + image_size[1], x:x + image_size[0]] = (80, 80, 80)

    return canvas
