from ultralytics import YOLO
import cv2

import torch
import numpy as np

# ตรวจสอบว่าใช้ GPU ได้หรือไม่
print("Using CUDA:", torch.cuda.is_available())
device = 'cuda' if torch.cuda.is_available() else 'cpu'

# โหลดโมเดล YOLO แบบ Segmentation
model = YOLO('yolo11n-seg.pt')
model.to(device)

line_thickness = 8
text_size = 2
text_bold = 3
point_size = 8

def find_center_and_blue_points(mask, image_shape):
    """หาจุดกึ่งกลางแกน Y (จุดแดง) และจุดสีน้ำเงิน"""
    height, width = image_shape[:2]
    center_y = height // 2
    center_x = width // 2
    
    # หาจุดขอบของ mask
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None, []
    
    # หาจุดสีน้ำเงิน (จุดที่อยู่บนขอบของ segment)
    blue_points = []
    for contour in contours:
        # หาจุดที่ใกล้กับแกน Y กึ่งกลางที่สุด
        for point in contour:
            x, y = point[0]
            if abs(y - center_y) < 20:  # จุดที่อยู่ใกล้แกน Y กึ่งกลาง
                blue_points.append((x, y))
    
    # เลือกจุดที่ห่างจากจุดกึ่งกลางมากที่สุด
    if blue_points:
        distances = [abs(x - center_x) for x, y in blue_points]
        max_dist_idx = np.argmax(distances)
        selected_blue_point = blue_points[max_dist_idx]
    else:
        selected_blue_point = None
    
    red_point = (center_x, center_y)
    
    return red_point, [selected_blue_point] if selected_blue_point else []

def calculate_distance_from_center(red_point, blue_points):
    """คำนวณระยะห่างจากจุดแดงไปยังจุดน้ำเงิน"""
    if not blue_points or not red_point:
        return 0
    
    distances = []
    for blue_point in blue_points:
        if blue_point:
            dist = np.sqrt((red_point[0] - blue_point[0])**2 + (red_point[1] - blue_point[1])**2)
            distances.append(dist)
    
    return np.mean(distances) if distances else 0

def analyze_segment_with_distance(mask, image_shape, segment_name):
    """วิเคราะห์ segment และคำนวณระยะห่าง"""
    # หาจุดกึ่งกลางและจุดสีน้ำเงิน
    red_point, blue_points = find_center_and_blue_points(mask, image_shape)
    
    # คำนวณระยะห่าง
    distance = calculate_distance_from_center(red_point, blue_points)
    
    # วิเคราะห์ความเต็มของ segment (ใช้วิธีเดิม)
    area = np.sum(mask > 0)
    total_area = image_shape[0] * image_shape[1]
    fullness_ratio = area / total_area
    
    if fullness_ratio > 0.3:
        status = 'Full'
    elif fullness_ratio > 0.15:
        status = 'Half'
    else:
        status = 'Empty'
    
    return {
        'segment': segment_name,
        'distance': distance,
        'red_point': red_point,
        'blue_points': blue_points,
        'status': status,
        'fullness_ratio': fullness_ratio
    }

def draw_enhanced_results(image, mask, bounding_box, analysis_result):
    """วาดผลการวิเคราะห์แบบใหม่"""
    image_with_alpha = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
    x, y, w, h = bounding_box
    
    # วาดขอบของ segment
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(image_with_alpha, contours, -1, (255, 255, 255, 255), 2)
    
    # วาดจุดแดง (จุดกึ่งกลาง)
    if analysis_result['red_point']:
        cv2.circle(image_with_alpha, analysis_result['red_point'], point_size, (0, 0, 255, 255), -1)
        cv2.putText(image_with_alpha, "Center", 
                   (analysis_result['red_point'][0] + 10, analysis_result['red_point'][1] - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, text_size, (0, 0, 255, 255), text_bold)
    
    # วาดจุดน้ำเงิน
    for blue_point in analysis_result['blue_points']:
        if blue_point:
            cv2.circle(image_with_alpha, blue_point, point_size, (255, 0, 0, 255), -1)
            cv2.putText(image_with_alpha, "Edge", 
                       (blue_point[0] + 10, blue_point[1] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, text_size, (255, 0, 0, 255), text_bold)
    
    # วาดเส้นเชื่อมระหว่างจุดแดงและจุดน้ำเงิน
    if analysis_result['red_point'] and analysis_result['blue_points']:
        for blue_point in analysis_result['blue_points']:
            if blue_point:
                cv2.line(image_with_alpha, analysis_result['red_point'], blue_point, 
                        (0, 255, 255, 255), line_thickness)
    
    # แสดงข้อมูลระยะห่าง
    info_text = [
        f"Segment: {analysis_result['segment']}",
        f"Distance: {analysis_result['distance']:.2f} px",
        f"Status: {analysis_result['status']}",
        f"Fullness: {analysis_result['fullness_ratio']:.2f}"
    ]
    
    for i, text in enumerate(info_text):
        cv2.putText(image_with_alpha, text, (x, y - 120 + i * 30),
                   cv2.FONT_HERSHEY_SIMPLEX, text_size, (0, 255, 0, 255), text_bold)
    
    # เพิ่มสีพื้นหลังตามสถานะ
    colors = {
        'Full': (50, 255, 50, 80),
        'Half': (50, 255, 255, 80),
        'Empty': (50, 50, 255, 80)
    }
    
    overlay = np.zeros_like(image_with_alpha, dtype=np.uint8)
    overlay[mask > 0] = colors[analysis_result['status']]
    image_with_alpha = cv2.addWeighted(image_with_alpha, 1.0, overlay, 0.5, 0)
    
    return image_with_alpha

def process_image(image_path, segment_name="Unknown"):
    """ประมวลผลรูปภาพแบบใหม่"""
    image = cv2.imread(image_path)
    if image is None:
        return None, "Error: Cannot load image."

    image_height, image_width = image.shape[:2]
    results = model(image, device=device)[0]

    if results.masks is not None:
        masks = results.masks.data
        for i, (seg_mask, box) in enumerate(zip(masks, results.boxes)):
            # ปรับขนาด mask
            resized_mask = torch.nn.functional.interpolate(
                seg_mask.unsqueeze(0).unsqueeze(0),
                size=(image_height, image_width),
                mode='bilinear',
                align_corners=False
            ).squeeze().cpu().numpy()

            binary_mask = (resized_mask > 0.5).astype(np.uint8) * 255

            # ดึงข้อมูล bounding box
            x1, y1, x2, y2 = box.xyxy.cpu().numpy()[0].astype(int)
            w, h = x2 - x1, y2 - y1

            # วิเคราะห์ segment
            analysis_result = analyze_segment_with_distance(
                binary_mask, (image_height, image_width), segment_name
            )

            # วาดผลลัพธ์
            result_image = draw_enhanced_results(
                image.copy(), binary_mask, (x1, y1, w, h), analysis_result
            )
            
            # แปลงเป็น RGB ถ้าเป็น RGBA
            if result_image.shape[2] == 4:
                result_image = cv2.cvtColor(result_image, cv2.COLOR_RGBA2RGB)

            # สร้างข้อความผลลัพธ์
            text_result = f"Segment: {analysis_result['segment']}\n"
            text_result += f"Distance from center: {analysis_result['distance']:.2f} pixels\n"
            text_result += f"Status: {analysis_result['status']}\n"
            text_result += f"Fullness ratio: {analysis_result['fullness_ratio']:.2f}\n"
            
            if analysis_result['red_point']:
                text_result += f"Center point: {analysis_result['red_point']}\n"
            
            if analysis_result['blue_points']:
                text_result += f"Edge points: {analysis_result['blue_points']}\n"

            return result_image, text_result

        return None, "No durians detected."

def process_multiple_segments(image_paths_dict):
    """ประมวลผล segment หลายตัวพร้อมกัน"""
    results = {}
    
    segment_mapping = {
        'segments_ab': ['A', 'B'],
        'segments_bc': ['B', 'C'],
        'segments_cd': ['C', 'D'],
        'segments_de': ['D', 'E'],
        'segments_ea': ['E', 'A']
    }
    
    for img_key, img_path in image_paths_dict.items():
        if img_path and img_key in segment_mapping:
            for segment in segment_mapping[img_key]:
                result_img, result_text = process_image(img_path, segment)
                if result_img is not None:
                    results[f"{img_key}_{segment}"] = {
                        'image': result_img,
                        'text': result_text,
                        'segment': segment
                    }
    
    return results
