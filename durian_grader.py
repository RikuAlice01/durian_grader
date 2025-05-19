from ultralytics import YOLO
import cv2
import matplotlib.pyplot as plt
import torch
import numpy as np

# ตรวจสอบว่าใช้ GPU ได้หรือไม่
print("Using CUDA:", torch.cuda.is_available())
device = 'cuda' if torch.cuda.is_available() else 'cpu'

# โหลดโมเดล YOLO แบบ Segmentation
model = YOLO('yolo11n-seg.pt')
model.to(device)

line_thickness = 10
text_size = 3
text_bold = 5
point_size = 10

def analyze_segment_fullness(mask, side, center_x, image_height, image_width):
    if side == 'left':
        segment_mask = mask[:, :center_x]
        x_start = 0
        x_end = center_x
    else:
        segment_mask = mask[:, center_x:]
        x_start = center_x
        x_end = image_width

    area = np.sum(segment_mask > 0)
    total_area = (x_end - x_start) * image_height
    expected_area = total_area * 0.3

    fullness_score = min(area / expected_area if expected_area > 0 else 0, 1.0)

    if fullness_score > 0.75:
        status = 'Full'
    elif fullness_score > 0.35:
        status = 'Half'
    else:
        status = 'Empty'
    
    return status, fullness_score

def calculate_grade(segment_info):
    score_table = {'Full': 2, 'Half': 1, 'Empty': 0}
    left_score = score_table[segment_info['left']['status']]
    right_score = score_table[segment_info['right']['status']]
    total_score = left_score + right_score

    if total_score >= 4:
        return "A"
    elif total_score >= 3:
        return "A-"
    elif total_score >= 2:
        return "B"
    elif total_score >= 1:
        return "B-"
    else:
        return "C"

def draw_results(image, mask, bounding_box, segment_info):
    image_with_alpha = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
    x, y, w, h = bounding_box
    center_x = x + w // 2
    cv2.line(image_with_alpha, (center_x, y), (center_x, y + h), (0, 0, 255, 255), line_thickness)
    
    left_mask = np.zeros_like(mask, dtype=np.uint8)
    right_mask = np.zeros_like(mask, dtype=np.uint8)
    left_mask[:, :center_x] = mask[:, :center_x]
    right_mask[:, center_x:] = mask[:, center_x:]

    colors = {
        'Full': (50, 255, 50, 100),
        'Half': (50, 255, 255, 100),
        'Empty': (50, 50, 255, 100)
    }

    for seg, m in [('left', left_mask), ('right', right_mask)]:
        overlay = np.zeros_like(image_with_alpha, dtype=np.uint8)
        overlay[m > 0] = colors[segment_info[seg]['status']]
        image_with_alpha = cv2.addWeighted(image_with_alpha, 1.0, overlay, 0.7, 0)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(image_with_alpha, contours, -1, (255, 255, 255, 255), 1)

    cv2.putText(image_with_alpha, f"Left: {segment_info['left']['status']} ({segment_info['left']['score']:.2f})",
                (x, y - 100), cv2.FONT_HERSHEY_SIMPLEX, text_size, (0, 0, 0, 255), text_bold)
    cv2.putText(image_with_alpha, f"Right: {segment_info['right']['status']} ({segment_info['right']['score']:.2f})",
                (x+1000, y - 100), cv2.FONT_HERSHEY_SIMPLEX, text_size, (0, 0, 0, 255), text_bold)
    grade = calculate_grade(segment_info)
    cv2.putText(image_with_alpha, f"Grade: {grade}", (x, y + h + 100),
                cv2.FONT_HERSHEY_SIMPLEX, text_size, (0, 0, 255, 255), text_bold)

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        cv2.rectangle(image_with_alpha, (x, y), (x + w, y + h), (0, 255, 0, 255), line_thickness)

        points = cnt.squeeze()
        mid_top = ((x + x + w) // 2, y)
        mid_bottom = ((x + x + w) // 2, y + h)
        mid_left = (x, (y + y + h) // 2)
        mid_right = (x + w, (y + y + h) // 2)
        center_x = (mid_left[0] + mid_right[0]) // 2

        # เส้นกรอบเขียว
        cv2.line(image_with_alpha, mid_top, mid_right, (0, 255, 0, 255), line_thickness)
        cv2.line(image_with_alpha, mid_right, mid_bottom, (0, 255, 0, 255), line_thickness)
        cv2.line(image_with_alpha, mid_bottom, mid_left, (0, 255, 0, 255), line_thickness)
        cv2.line(image_with_alpha, mid_left, mid_top, (0, 255, 0, 255), line_thickness)

        # จุดกึ่งกลางเส้นขอบ
        for p in [mid_top, mid_bottom, mid_left, mid_right]:
            cv2.circle(image_with_alpha, p, point_size, (0, 0, 255, 255), -1)

        # ตรวจหาและวาดจุดเฉลี่ยขอบ
        left_points = points[points[:, 0] < x + 5]
        if len(left_points) > 0:
            left_avg_y = np.mean(left_points[:, 1])
            left_point = (x, int(left_avg_y))
            cv2.circle(image_with_alpha, left_point, 2, (255, 0, 0, 255), -1)
            cv2.putText(image_with_alpha, "Left", (left_point[0] + 5, left_point[1] - 5), 
                                    cv2.FONT_HERSHEY_SIMPLEX, text_size, (255, 0, 0, 255), text_bold)

        right_points = points[points[:, 0] > x + w - 5]
        if len(right_points) > 0:
            right_avg_y = np.mean(right_points[:, 1])
            right_point = (x + w, int(right_avg_y))
            cv2.circle(image_with_alpha, right_point, point_size, (255, 0, 0, 255), -1)
            cv2.putText(image_with_alpha, "Right", (right_point[0] + 5, right_point[1] - 5), 
                                    cv2.FONT_HERSHEY_SIMPLEX, text_size, (255, 0, 0, 255), text_bold)

        bottom_points = points[points[:, 1] > y + h - 5]
        if len(bottom_points) > 0:
            bottom_avg = np.mean(bottom_points[:, 1])
            bottom_point = (x + w // 2, int(bottom_avg))
            cv2.circle(image_with_alpha, bottom_point, point_size, (255, 0, 0, 255), -1)
            cv2.putText(image_with_alpha, "Bottom", (bottom_point[0] + 5, bottom_point[1] - 5), 
                                    cv2.FONT_HERSHEY_SIMPLEX, text_size, (255, 0, 0, 255), text_bold)

        top_points = points[points[:, 1] < y + 5]
        if len(top_points) > 0:
            top_avg = np.mean(top_points[:, 1])
            top_point = (x + w // 2, int(top_avg))
            cv2.circle(image_with_alpha, top_point, 2, (255, 0, 0, 255), -1)
            cv2.putText(image_with_alpha, "Top", (top_point[0] + 5, top_point[1] - 5), 
                                    cv2.FONT_HERSHEY_SIMPLEX, text_size, (255, 0, 0, 255), text_bold)
    
    return image_with_alpha

def process_image(image_path):
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
            center_x = x1 + w // 2

            left_status, left_score = analyze_segment_fullness(binary_mask, 'left', center_x, image_height, image_width)
            right_status, right_score = analyze_segment_fullness(binary_mask, 'right', center_x, image_height, image_width)

            segment_info = {
                'left': {'status': left_status, 'score': left_score},
                'right': {'status': right_status, 'score': right_score}
            }

            result_image = draw_results(image.copy(), binary_mask, (x1, y1, w, h), segment_info)
            all_results.append({
                'image': result_image,
                'text': f"Durian {i+1}:\n"
                        f"  Left: {left_status} ({left_score:.2f})\n"
                        f"  Right: {right_status} ({right_score:.2f})\n"
                        f"  Grade: {calculate_grade(segment_info)}"
            })

    if not all_results:
        return None, "No durians detected."

    return all_results[0]['image'], all_results[0]['text']
