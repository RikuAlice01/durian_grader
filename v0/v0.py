from ultralytics import YOLO
import cv2
import matplotlib.pyplot as plt
import torch
import numpy as np

# ตรวจสอบว่าใช้ GPU ได้หรือไม่
print("Using CUDA:", torch.cuda.is_available())

# โหลดโมเดล YOLO แบบ Segmentation
model = YOLO('yolo11n-seg.pt')
model.to('cuda')

# โหลดภาพ
image_path = './test-0.jpg'
image = cv2.imread(image_path)
image_height, image_width = image.shape[:2]
line_thickness = 2

# สร้างภาพที่มี alpha channel (โปร่งใส)
image_with_alpha = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)  # เพิ่ม alpha channel

# ตรวจจับแบบ segmentation
results = model(image, device='cuda')[0]

# วาดผลลัพธ์ลงภาพ
if results.masks is not None:
    masks = results.masks.data  # [N, H, W]
    for seg_mask, box in zip(masks, results.boxes):
        # รีเซ็ตค่าจุดขอบ
        top_point = bottom_point = left_point = right_point = None
        dist_left = dist_right = dist_top = dist_bottom = None

        # Resize mask ให้ตรงกับขนาดภาพจริง
        resized_mask = torch.nn.functional.interpolate(
            seg_mask.unsqueeze(0).unsqueeze(0),  # [1, 1, H, W]
            size=(image_height, image_width),
            mode='bilinear',
            align_corners=False
        ).squeeze().cpu().numpy()

        # Threshold
        binary_mask = (resized_mask > 0.5).astype(np.uint8) * 255
        contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            if cv2.contourArea(cnt) > 1000:
                x, y, w, h = cv2.boundingRect(cnt)
                cv2.rectangle(image_with_alpha, (x, y), (x + w, y + h), (0, 255, 0, 255), line_thickness)

                points = cnt.squeeze()
                mid_top = ((x + x + w) // 2, y)
                mid_bottom = ((x + x + w) // 2, y + h)
                mid_left = (x, (y + y + h) // 2)
                mid_right = (x + w, (y + y + h) // 2)
                center_x = (mid_left[0] + mid_right[0]) // 2

                # สร้าง overlay แยกซ้ายขวา
                left_half_mask = np.zeros_like(binary_mask, dtype=np.uint8)
                right_half_mask = np.zeros_like(binary_mask, dtype=np.uint8)
                left_half_mask[:, :center_x] = binary_mask[:, :center_x]
                right_half_mask[:, center_x:] = binary_mask[:, center_x:]

                left_overlay = np.zeros_like(image_with_alpha, dtype=np.uint8)
                left_overlay[left_half_mask == 255] = (255, 200, 200, 100)
                image_with_alpha = cv2.addWeighted(image_with_alpha, 1, left_overlay, 0.5, 0)

                right_overlay = np.zeros_like(image_with_alpha, dtype=np.uint8)
                right_overlay[right_half_mask == 255] = (200, 255, 200, 100)
                image_with_alpha = cv2.addWeighted(image_with_alpha, 1, right_overlay, 0.5, 0)

                # วาด contour
                cv2.drawContours(image_with_alpha, [cnt], -1, (255, 255, 255, 255), line_thickness)

                # เส้นกรอบเขียว
                cv2.line(image_with_alpha, mid_top, mid_right, (0, 255, 0, 255), line_thickness)
                cv2.line(image_with_alpha, mid_right, mid_bottom, (0, 255, 0, 255), line_thickness)
                cv2.line(image_with_alpha, mid_bottom, mid_left, (0, 255, 0, 255), line_thickness)
                cv2.line(image_with_alpha, mid_left, mid_top, (0, 255, 0, 255), line_thickness)

                # จุดกึ่งกลาง
                for p in [mid_top, mid_bottom, mid_left, mid_right]:
                    cv2.circle(image_with_alpha, p, 2, (0, 0, 255, 255), -1)

                # ตรวจหาและวาดจุดเฉลี่ยขอบ
                left_points = points[points[:, 0] < x + 5]
                if len(left_points) > 0:
                    left_avg_y = np.mean(left_points[:, 1])
                    left_point = (x, int(left_avg_y))
                    cv2.circle(image_with_alpha, left_point, 2, (255, 0, 0, 255), -1)
                    cv2.putText(image_with_alpha, "Left", (left_point[0] + 5, left_point[1] - 5), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0, 255), 1)

                right_points = points[points[:, 0] > x + w - 5]
                if len(right_points) > 0:
                    right_avg_y = np.mean(right_points[:, 1])
                    right_point = (x + w, int(right_avg_y))
                    cv2.circle(image_with_alpha, right_point, 2, (255, 0, 0, 255), -1)
                    cv2.putText(image_with_alpha, "Right", (right_point[0] + 5, right_point[1] - 5), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0, 255), 1)

                bottom_points = points[points[:, 1] > y + h - 5]
                if len(bottom_points) > 0:
                    bottom_avg = np.mean(bottom_points[:, 1])
                    bottom_point = (x + w // 2, int(bottom_avg))
                    cv2.circle(image_with_alpha, bottom_point, 2, (255, 0, 0, 255), -1)
                    cv2.putText(image_with_alpha, "Bottom", (bottom_point[0] + 5, bottom_point[1] - 5), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0, 255), 1)

                top_points = points[points[:, 1] < y + 5]
                if len(top_points) > 0:
                    top_avg = np.mean(top_points[:, 1])
                    top_point = (x + w // 2, int(top_avg))
                    cv2.circle(image_with_alpha, top_point, 2, (255, 0, 0, 255), -1)
                    cv2.putText(image_with_alpha, "Top", (top_point[0] + 5, top_point[1] - 5), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0, 255), 1)

                if top_point is not None and bottom_point is not None:
                    cv2.line(image_with_alpha, top_point, bottom_point, (255, 255, 255, 255), line_thickness)

                cv2.line(image_with_alpha, mid_top, mid_bottom, (0, 255, 0, 255), line_thickness)

# ระยะห่าง
if left_point is not None:
    dist_left = np.linalg.norm(np.array(left_point) - np.array(mid_left))
    print(f"Distance Left: {dist_left:.2f} px")

if right_point is not None:
    dist_right = np.linalg.norm(np.array(right_point) - np.array(mid_right))
    print(f"Distance Right: {dist_right:.2f} px")

if top_point is not None:
    dist_top = np.linalg.norm(np.array(top_point) - np.array(mid_top))
    print(f"Distance Top: {dist_top:.2f} px")

if bottom_point is not None:
    dist_bottom = np.linalg.norm(np.array(bottom_point) - np.array(mid_bottom))
    print(f"Distance Bottom: {dist_bottom:.2f} px")

# แสดงผลด้วย matplotlib
image_rgb = cv2.cvtColor(image_with_alpha, cv2.COLOR_BGRA2RGBA)
plt.imshow(image_rgb)
plt.title("Durian Segmentation with Overlay")
plt.axis('off')
plt.show()

