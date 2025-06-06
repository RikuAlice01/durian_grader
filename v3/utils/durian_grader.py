from ultralytics import YOLO
import cv2
import torch
import numpy as np
from utils.config_loader import load_config

# ตรวจสอบว่าใช้ GPU ได้หรือไม่
print("Using CUDA:", torch.cuda.is_available())
device = 'cuda' if torch.cuda.is_available() else 'cpu'

# โหลดโมเดล YOLO แบบ Segmentation
model = YOLO('yolo11n-seg.pt')
model.to(device)

line_thickness = 2
text_size = 0.5
text_bold = 1
point_size = 5
DISTANCE_THRESHOLD = 3
ADJ = 10

def loader_config():
    global line_thickness, text_size, text_bold, point_size, DISTANCE_THRESHOLD, ADJ
    cfg = load_config()
    line_thickness = int(cfg['Rendering']['line_thickness'])
    text_size = float(cfg['Rendering']['text_size'])
    text_bold = int(cfg['Rendering']['text_bold'])
    point_size = int(cfg['Rendering']['point_size'])
    DISTANCE_THRESHOLD = int(cfg['Grading']['distance_threshold'])
    ADJ = int(cfg['Grading']['adj'])

def calculate_grade_by_distance(segment_info):
    """
    red_pt คือจุดเฉลี่ยขอบ (x,y)
    blue_pt คือจุดกึ่งกลางเส้นขอบกรอบเขียว (x,y)
    คำนวณเกรดจากระยะห่าง
    AB = 0-3, C = > 3
    ถ้า score_left หรือ score_right > DISTANCE_THRESHOLD ให้เกรด C
    """
    print("segment_info['left']['red_pt']:", segment_info['left']['red_pt'])
    print("segment_info['left']['blue_pt']:", segment_info['left']['blue_pt'])
    print("segment_info['right']['red_pt']:", segment_info['right']['red_pt'])
    print("segment_info['right']['blue_pt']:", segment_info['right']['blue_pt'])

    segment_info['left']['score'] = np.linalg.norm(np.array(segment_info['left']['red_pt']) - np.array(segment_info['left']['blue_pt']))
    segment_info['right']['score']= np.linalg.norm(np.array(segment_info['right']['red_pt']) - np.array(segment_info['right']['blue_pt']))
    segment_info['top']['score'] = np.linalg.norm(np.array(segment_info['top']['red_pt']) - np.array(segment_info['top']['blue_pt']))
    segment_info['bottom']['score'] = np.linalg.norm(np.array(segment_info['bottom']['red_pt']) - np.array(segment_info['bottom']['blue_pt']))

    segment_info['left']['status'] = "C" if segment_info['left']['score'] > DISTANCE_THRESHOLD else "AB"
    segment_info['right']['status'] = "C" if segment_info['right']['score'] > DISTANCE_THRESHOLD else "AB"

    max_score = max(segment_info['left']['score'], segment_info['right']['score'])
    
    if max_score > DISTANCE_THRESHOLD:
        return "C", segment_info
    else:
        return "AB", segment_info

def draw_results(image, mask, bounding_box):
    global line_thickness, text_size, text_bold, point_size, DISTANCE_THRESHOLD, ADJ
    # กำหนดค่าเริ่มต้นสำหรับ segment_info
    # blue_pt durain middle point
    # red_pt durain average point

    segment_info = {
        'left': {'status': "C", 'score': 0.0,"red_pt": None,"blue_pt": None},
        'right': {'status': "C", 'score': 0.0, "red_pt": None, "blue_pt": None},
        'top': {'status': "C", 'score': 0.0, "red_pt": None, "blue_pt": None},
        'bottom': {'status': "C", 'score': 0.0, "red_pt": None, "blue_pt": None}
        }
            
    image_with_alpha = cv2.cvtColor(image, cv2.COLOR_RGB2BGRA)
    x, y, w, h = bounding_box
    center_x = x + w // 2
    cv2.line(image_with_alpha, (center_x, y), (center_x, y + h), (0, 0, 255, 255), line_thickness)
    
    left_mask = np.zeros_like(mask, dtype=np.uint8)
    right_mask = np.zeros_like(mask, dtype=np.uint8)
    left_mask[:, :center_x] = mask[:, :center_x]
    right_mask[:, center_x:] = mask[:, center_x:]

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(image_with_alpha, contours, -1, (255, 255, 255, 255), 1)

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        cv2.rectangle(image_with_alpha, (x, y), (x + w, y + h), (0, 255, 0, 255), line_thickness)

        points = cnt.squeeze()
        segment_info["top"]["blue_pt"] = ((x + x + w) // 2, y)
        segment_info["bottom"]["blue_pt"] = ((x + x + w) // 2, y + h)
        segment_info["left"]["blue_pt"] = (x, (y + y + h) // 2)
        segment_info["right"]["blue_pt"] = (x + w, (y + y + h) // 2)

        # เส้นกรอบเขียว
        cv2.line(image_with_alpha, segment_info["top"]["blue_pt"], segment_info["right"]["blue_pt"], (0, 255, 0, 255), line_thickness)
        cv2.line(image_with_alpha, segment_info["right"]["blue_pt"], segment_info["bottom"]["blue_pt"], (0, 255, 0, 255), line_thickness)
        cv2.line(image_with_alpha, segment_info["bottom"]["blue_pt"], segment_info["left"]["blue_pt"], (0, 255, 0, 255), line_thickness)
        cv2.line(image_with_alpha, segment_info["left"]["blue_pt"], segment_info["top"]["blue_pt"], (0, 255, 0, 255), line_thickness)
        

        # จุดกึ่งกลางเส้นขอบ
        for p in [segment_info["top"]["blue_pt"], segment_info["bottom"]["blue_pt"], segment_info["left"]["blue_pt"], segment_info["right"]["blue_pt"]]:
            cv2.circle(image_with_alpha, p, point_size, (0, 0, 255, 255), -1)

        # ตรวจหาและวาดจุดเฉลี่ยขอบ
        left_points = points[points[:, 0] < x + ADJ]
        if len(left_points) > 0:
            left_avg_y = np.mean(left_points[:, 1])
            left_point = (x, int(left_avg_y))
            segment_info["left"]["red_pt"] = left_point
            cv2.circle(image_with_alpha, left_point, point_size, (255, 0, 0, 255), -1)

        right_points = points[points[:, 0] > x + w - ADJ]
        if len(right_points) > 0:
            right_avg_y = np.mean(right_points[:, 1])
            right_point = (x + w, int(right_avg_y))
            segment_info["right"]["red_pt"] = right_point
            cv2.circle(image_with_alpha, right_point, point_size, (255, 0, 0, 255), -1)

        bottom_points = points[points[:, 1] > y + h - ADJ]
        if len(bottom_points) > 0:
            bottom_avg = np.mean(bottom_points[:, 1])
            bottom_point = (x + w // 2, int(bottom_avg))
            segment_info["bottom"]["red_pt"] = bottom_point
            cv2.circle(image_with_alpha, bottom_point, point_size, (255, 0, 0, 255), -1)

        top_points = points[points[:, 1] < y + ADJ]
        if len(top_points) > 0:
            top_avg = np.mean(top_points[:, 1])
            top_point = (x + w // 2, int(top_avg))
            segment_info["top"]["red_pt"] = top_point
            cv2.circle(image_with_alpha, top_point, point_size, (255, 0, 0, 255), -1)

        # เส้นขอบดำจุดเฉลี่ยขอบ
        cv2.line(image_with_alpha, segment_info["right"]["red_pt"], segment_info["right"]["blue_pt"], (0, 0, 0, 255), line_thickness)
        cv2.line(image_with_alpha, segment_info["left"]["red_pt"], segment_info["left"]["blue_pt"], (0, 0, 0, 255), line_thickness)
    
    grade,segment_info = calculate_grade_by_distance(segment_info)
    cv2.putText(image_with_alpha, f"Left: ({segment_info['left']['score']:.0f})",
                (x, y - 100), cv2.FONT_HERSHEY_SIMPLEX, text_size, (0, 0, 0, 255), text_bold)
    cv2.putText(image_with_alpha, f"Right:({segment_info['right']['score']:.0f})",
                (x+1000, y - 100), cv2.FONT_HERSHEY_SIMPLEX, text_size, (0, 0, 0, 255), text_bold)

    colors = {
        'AB': (50, 255, 50, 100),
        'C': (50, 255, 255, 100),
    }

    for seg, m in [('left', left_mask), ('right', right_mask)]:
        overlay = np.zeros_like(image_with_alpha, dtype=np.uint8)
        overlay[m > 0] = colors[segment_info[seg]['status']]
        image_with_alpha = cv2.addWeighted(image_with_alpha, 1.0, overlay, 0.5, 0)
   
    return image_with_alpha, segment_info, grade

def process_image(image_path):
    loader_config()
    image = cv2.imread(image_path)
    if image is None:
        return None, "Error: Cannot load image."

    image_height, image_width = image.shape[:2]
    results = model(image, device=device)[0]

    all_results = []

    if results.masks is not None:
        masks = results.masks.data
        for i, (seg_mask, box) in enumerate(zip(masks, results.boxes)):
            resized_mask = torch.nn.functional.interpolate(
                seg_mask.unsqueeze(0).unsqueeze(0),
                size=(image_height, image_width),
                mode='bilinear',
                align_corners=False
            ).squeeze().cpu().numpy()

            binary_mask = (resized_mask > 0.5).astype(np.uint8) * 255

            x1, y1, x2, y2 = box.xyxy.cpu().numpy()[0].astype(int)
            w, h = x2 - x1, y2 - y1

            result_image, segment_info, grade = draw_results(image.copy(), binary_mask, (x1, y1, w, h))
            all_results.append({
                'image': result_image,
                'text': f"Durian {i+1}:\n"
                        f"  Left: ({segment_info['left']['score']:.0f})\n"
                        f"  Right: ({segment_info['right']['score']:.0f})\n"
                        f"  Grade: {grade}"
            })

    if not all_results:
        return image, "No durians detected."

    return all_results[0]['image'], all_results[0]['text']
