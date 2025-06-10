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
PERCENTAGE_GRADING = 5.0
ADJ = 10

def loader_config():
    global line_thickness, text_size, text_bold, point_size, DISTANCE_THRESHOLD,PERCENTAGE_GRADING, ADJ
    cfg = load_config()
    line_thickness = int(cfg['Rendering']['line_thickness'])
    text_size = float(cfg['Rendering']['text_size'])
    text_bold = int(cfg['Rendering']['text_bold'])
    point_size = int(cfg['Rendering']['point_size'])
    DISTANCE_THRESHOLD = int(cfg['Grading']['distance_threshold'])
    PERCENTAGE_GRADING = float(cfg['Grading']['percentage_grading'])
    ADJ = int(cfg['Grading']['adj'])

def calculate_grade_by_distance(segment_info, segment_area):
    """
    red_pt คือจุดเฉลี่ยขอบ (x,y)
    blue_pt คือจุดกึ่งกลางเส้นขอบกรอบเขียว (x,y)
    """
    segment_info['left']['score'] = np.linalg.norm(np.array(segment_info['left']['red_pt']) - np.array(segment_info['left']['blue_pt']))
    segment_info['right']['score']= np.linalg.norm(np.array(segment_info['right']['red_pt']) - np.array(segment_info['right']['blue_pt']))
    segment_info['top']['score'] = np.linalg.norm(np.array(segment_info['top']['red_pt']) - np.array(segment_info['top']['blue_pt']))
    segment_info['bottom']['score'] = np.linalg.norm(np.array(segment_info['bottom']['red_pt']) - np.array(segment_info['bottom']['blue_pt']))

    segment_info['left']['grade'] = "C" if segment_area['left']['diff-percentage'] > PERCENTAGE_GRADING else "AB"
    segment_info['right']['grade'] = "C" if segment_area['right']['diff-percentage'] > PERCENTAGE_GRADING else "AB"

    max_score = max(segment_area['left']['diff-percentage'], segment_area['right']['diff-percentage'])

    if max_score > PERCENTAGE_GRADING:
        return "C", segment_info
    else:
        return "AB", segment_info

def draw_results(image, mask, bounding_box):
    global line_thickness, text_size, text_bold, point_size, ADJ
    # กำหนดค่าเริ่มต้นสำหรับ segment_info
    # blue_pt durain middle point
    # red_pt durain average point

    segment_info = {
        'left': {'grade': "C", 'score': 0.0,"red_pt": None,"blue_pt": None},
        'right': {'grade': "C", 'score': 0.0, "red_pt": None, "blue_pt": None},
        'top': {'grade': "C", 'score': 0.0, "red_pt": None, "blue_pt": None},
        'bottom': {'grade': "C", 'score': 0.0, "red_pt": None, "blue_pt": None}
        }

    segment_area = {
        'left': {'top': 0, 'bottom': 0,"diff": 0,"all": 0,"diff-percentage": 0.0},
        'right': {'top': 0, 'bottom': 0,"diff": 0,"all": 0,"diff-percentage": 0.0},
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
        

        # จุดกึ่งกลางเส้นขอบเขียว
        for p in [segment_info["top"]["blue_pt"], segment_info["bottom"]["blue_pt"], segment_info["left"]["blue_pt"], segment_info["right"]["blue_pt"]]:
            cv2.circle(image_with_alpha, p, point_size, (0, 0, 255, 255), -1)
        
        # วาดเส้นขอบน้ำเงินจุดกึ่งกลางเส้นขอบเขียว A
        cv2.line(image_with_alpha, segment_info["left"]["blue_pt"], segment_info["right"]["blue_pt"], (0, 0, 255, 255), line_thickness)

        # ตรวจหาและวาดจุดเฉลี่ยขอบลูก
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

    # คำนวณเส้นแบ่งแนวนอน (y) จากจุดกลาง top-bottom (blue line)
    center_line_y = (segment_info["top"]["blue_pt"][1] + segment_info["bottom"]["blue_pt"][1]) // 2
    center_x = (segment_info["left"]["blue_pt"][0] + segment_info["right"]["blue_pt"][0]) // 2

    # คำนวณพื้นที่ของแต่ละ segment
    ys, xs = np.where(mask > 0)
    for x_point, y_point in zip(xs, ys):
        if x_point < center_x:
            if y_point < center_line_y:
                segment_area['left']['top'] += 1
            else:
                segment_area['left']['bottom'] += 1
        else:
            if y_point < center_line_y:
                segment_area['right']['top'] += 1
            else:
                segment_area['right']['bottom'] += 1

    segment_area['left']['diff'] = abs(segment_area['left']['top'] - segment_area['left']['bottom'])
    segment_area['right']['diff'] = abs(segment_area['right']['top'] - segment_area['right']['bottom'])

    segment_area['left']['all'] = segment_area['left']['top'] + segment_area['left']['bottom']
    segment_area['right']['all'] = segment_area['right']['top'] + segment_area['right']['bottom']

    segment_area['left']['diff-percentage'] = (segment_area['left']['diff']) / (segment_area['left']['all']) * 100
    segment_area['right']['diff-percentage'] = ( segment_area['right']['diff']) / (segment_area['right']['all']) * 100
   
    grade, segment_info = calculate_grade_by_distance(segment_info, segment_area)

    colors = {
        'AB': (50, 255, 50, 100),
        'C': (50, 255, 255, 100),
    }

    for seg, m in [('left', left_mask), ('right', right_mask)]:
        overlay = np.zeros_like(image_with_alpha, dtype=np.uint8)
        overlay[m > 0] = colors[segment_info[seg]['grade']]
        image_with_alpha = cv2.addWeighted(image_with_alpha, 1.0, overlay, 0.5, 0)


    return image_with_alpha, segment_info, grade, segment_area

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

            result_image, segment_info, grade, segment_area = draw_results(image.copy(), binary_mask, (x1, y1, w, h))

            all_results.append({
                'image': result_image,
                'text': f"Durian {i+1}:\n"
                        f"  L-Grade: {segment_info['left']['grade']}\n"
                        f"  R-Grade: {segment_info['right']['grade']}\n"
                        f"  Segment Area:\n"
                        f"   - L-diff: {segment_area['left']['diff-percentage']:.2f}%\n"
                        f"   - R-diff: {segment_area['right']['diff-percentage']:.2f}%\n"
                        f"  Grade: {grade}"
            })

    if not all_results:
        return None, "No durians detected."

    # Return all results for batch processing
    if len(all_results) > 1:
        # If multiple durians detected in one image, return all results
        combined_text = "\n".join([r['text'] for r in all_results])
        # Check if any durian is grade C
        overall_grade = "C" if any("Grade: C" in r['text'] for r in all_results) else "AB"
        combined_text += f"\n\nOverall Grade: {overall_grade}"
        return all_results[0]['image'], combined_text
    else:
        # Return single result for backward compatibility
        return all_results[0]['image'], all_results[0]['text']
