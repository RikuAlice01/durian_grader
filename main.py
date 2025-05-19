import numpy as np
import cv2
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import List, Tuple
import random
import os
import glob

# Define segment types
class SegmentType:
    FULL = "Full"
    HALF = "Half"
    EMPTY = "Empty"

@dataclass
class Segment:
    id: str  # Segment identifier (A, B, C, etc.)
    type: str  # Full, Half, or Empty
    position: Tuple[int, int]  # Position in the image

@dataclass
class Durian:
    id: int
    segments: List[Segment]
    grade: str = None
    
    def calculate_grade(self):
        """Calculate grade based on segments"""
        full_count = sum(1 for seg in self.segments if seg.type == SegmentType.FULL)
        half_count = sum(1 for seg in self.segments if seg.type == SegmentType.HALF)
        empty_count = sum(1 for seg in self.segments if seg.type == SegmentType.EMPTY)
        
        # Grading logic based on the whitepaper
        if full_count >= 4:
            if empty_count == 0:
                return "A+"
            else:
                return "A-"
        elif full_count == 3:
            if half_count >= 2:
                return "B+"
            else:
                return "B"
        elif full_count == 2:
            return "B-"
        else:
            return "C"

class DurianGradingSystem:
    def __init__(self):
        self.durians_processed = 0
        self.grades_count = {"A+": 0, "A-": 0, "B+": 0, "B": 0, "B-": 0, "C": 0}
    
    def detect_segments_from_top_view(self, image):
        """
        Detect segments from top view image
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply adaptive threshold to get binary image
        binary = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # Morphological operations to clean up the binary image
        kernel = np.ones((3, 3), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Draw the contours on the original image for visualization
        image_with_contours = image.copy()
        cv2.drawContours(image_with_contours, contours, -1, (0, 255, 0), 2)
        
        # Find the largest contour (assuming it's the durian)
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            
            # Find the center of the durian
            M = cv2.moments(largest_contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                
                # Draw the center
                cv2.circle(image_with_contours, (cx, cy), 5, (0, 0, 255), -1)
                
                # Analyze the star pattern to detect segments
                # For real images, we would use more sophisticated techniques
                # For now, we'll estimate based on the contour shape
                
                # Approximate the contour to find corners
                epsilon = 0.02 * cv2.arcLength(largest_contour, True)
                approx = cv2.approxPolyDP(largest_contour, epsilon, True)
                
                # Draw the approximated contour
                cv2.drawContours(image_with_contours, [approx], -1, (255, 0, 0), 2)
                
                # Estimate number of segments based on corners
                # In a real system, this would be more sophisticated
                num_corners = len(approx)
                num_segments = max(3, min(6, num_corners // 2))  # Between 3 and 6 segments
                
                # Draw lines from center to each corner
                for point in approx:
                    cv2.line(image_with_contours, (cx, cy), tuple(point[0]), (0, 255, 255), 2)
        else:
            # If no contours found, default to random number
            num_segments = random.randint(3, 6)
        
        return num_segments, image_with_contours
    
    def classify_segments(self, side_images):
        """
        Classify segments as Full, Half, or Empty
        """
        segments = []
        segment_ids = ['A', 'B', 'C', 'D', 'E', 'F']
        
        for i, image in enumerate(side_images):
            if i >= len(segment_ids):
                break
                
            # For real images, we would analyze the content of each segment
            # Here we'll use a simple color-based approach
            
            # Convert to HSV for better color analysis
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Calculate average saturation as a measure of "fullness"
            avg_saturation = np.mean(hsv[:, :, 1])
            
            # Calculate average brightness
            avg_brightness = np.mean(hsv[:, :, 2])
            
            # Position for visualization (center of image)
            h, w = image.shape[:2]
            position = (w // 2, h // 2)
            
            # Classify based on saturation and brightness
            if avg_saturation > 100 and avg_brightness > 100:
                segment_type = SegmentType.FULL
            elif avg_saturation > 50 and avg_brightness > 50:
                segment_type = SegmentType.HALF
            else:
                segment_type = SegmentType.EMPTY
            
            segments.append(Segment(segment_ids[i], segment_type, position))
        
        return segments
    
    def process_durian(self, top_image, side_images):
        """Process a single durian"""
        self.durians_processed += 1
        
        # Detect segments from top view
        num_segments, top_image_processed = self.detect_segments_from_top_view(top_image)
        
        # Use only the detected number of segments
        actual_side_images = side_images[:num_segments]
        
        # If we don't have enough side images, duplicate the last one
        while len(actual_side_images) < num_segments:
            if side_images:
                actual_side_images.append(side_images[-1])
            else:
                # Create a blank image if no side images available
                blank = np.zeros_like(top_image)
                actual_side_images.append(blank)
        
        # Classify segments
        segments = self.classify_segments(actual_side_images)
        
        # Create durian object
        durian = Durian(self.durians_processed, segments)
        
        # Calculate grade
        durian.grade = durian.calculate_grade()
        
        # Update grades count
        self.grades_count[durian.grade] += 1
        
        return durian, top_image_processed
    
    def visualize_results(self, durian, top_image_processed, side_images):
        """Visualize the grading results"""
        plt.figure(figsize=(12, 8))
        
        # Display top view with detected segments
        plt.subplot(2, 3, 1)
        plt.imshow(cv2.cvtColor(top_image_processed, cv2.COLOR_BGR2RGB))
        plt.title("Top View with Detected Segments")
        plt.axis('off')
        
        # Display segment classification
        for i, segment in enumerate(durian.segments):
            if i >= 5:  # Only show up to 5 segments in the visualization
                break
                
            plt.subplot(2, 3, i + 2)
            
            if i < len(side_images):
                # Show the actual side image
                img = side_images[i].copy()
                
                # Add colored overlay based on segment type
                overlay = img.copy()
                if segment.type == SegmentType.FULL:
                    cv2.rectangle(overlay, (0, 0), (img.shape[1], img.shape[0]), (0, 255, 0), -1)  # Green for Full
                elif segment.type == SegmentType.HALF:
                    cv2.rectangle(overlay, (0, 0), (img.shape[1], img.shape[0]), (255, 255, 0), -1)  # Yellow for Half
                else:
                    cv2.rectangle(overlay, (0, 0), (img.shape[1], img.shape[0]), (255, 0, 0), -1)  # Red for Empty
                
                # Apply the overlay with transparency
                alpha = 0.3
                cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)
                
                # Add text label
                cv2.putText(img, f"Segment {segment.id}: {segment.type}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            else:
                # Create a simple visualization if no image available
                img = np.zeros((200, 200, 3), dtype=np.uint8)
                
                # Color based on segment type
                if segment.type == SegmentType.FULL:
                    color = (0, 255, 0)  # Green for Full
                elif segment.type == SegmentType.HALF:
                    color = (255, 255, 0)  # Yellow for Half
                else:
                    color = (255, 0, 0)  # Red for Empty
                
                # Draw a filled circle to represent the segment
                cv2.circle(img, segment.position, 50, color, -1)
                
                # Add text label
                cv2.putText(img, f"Segment {segment.id}: {segment.type}", 
                           (20, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            plt.title(f"Segment {segment.id}")
            plt.axis('off')
        
        # Display grade
        plt.figtext(0.5, 0.05, f"Durian #{durian.id} - Grade: {durian.grade}", 
                   ha="center", fontsize=16, bbox={"facecolor":"orange", "alpha":0.5, "pad":5})
        
        plt.tight_layout()
        plt.show()
    
    def generate_report(self):
        """Generate a summary report"""
        print("\n===== Durian Grading System Report =====")
        print(f"Total durians processed: {self.durians_processed}")
        print("\nGrade distribution:")
        for grade, count in self.grades_count.items():
            percentage = (count / self.durians_processed) * 100 if self.durians_processed > 0 else 0
            print(f"  {grade}: {count} ({percentage:.1f}%)")
        print("=======================================")

# Load real durian images
def load_real_durian_images(top_image_path, side_images_folder=None):
    """
    Load real durian images from specified paths
    
    Args:
        top_image_path: Path to the top view image
        side_images_folder: Path to folder containing side view images
        
    Returns:
        top_image: The top view image
        side_images: List of side view images
    """
    # Load top view image
    if os.path.exists(top_image_path):
        top_image = cv2.imread(top_image_path)
        if top_image is None:
            print(f"Warning: Could not load top image from {top_image_path}")
            top_image = create_simulated_top_image()
    else:
        print(f"Warning: Top image path {top_image_path} does not exist")
        top_image = create_simulated_top_image()
    
    # Load side view images
    side_images = []
    
    if side_images_folder and os.path.exists(side_images_folder):
        # Get all image files in the folder
        image_extensions = ['jpg', 'jpeg', 'png', 'bmp', 'tif', 'tiff']
        image_files = []
        
        for ext in image_extensions:
            image_files.extend(glob.glob(os.path.join(side_images_folder, f"*.{ext}")))
        
        # Sort files to ensure consistent order
        image_files.sort()
        
        # Load up to 6 side images
        for file_path in image_files[:6]:
            img = cv2.imread(file_path)
            if img is not None:
                side_images.append(img)
            else:
                print(f"Warning: Could not load side image from {file_path}")
    
    # If no side images were loaded, create simulated ones
    if not side_images:
        print("No side images found, using simulated side images")
        _, side_images = create_simulated_durian_images()
    
    return top_image, side_images

# Create simulated durian images
def create_simulated_top_image():
    """Create a simulated top view image"""
    # Create a simulated top view image
    top_image = np.zeros((300, 300, 3), dtype=np.uint8)
    
    # Draw a durian-like shape
    cv2.circle(top_image, (150, 150), 100, (139, 69, 19), -1)  # Brown circle
    
    # Draw the star pattern
    points = []
    for i in range(5):
        angle = i * 2 * np.pi / 5
        x = int(150 + 80 * np.cos(angle))
        y = int(150 + 80 * np.sin(angle))
        points.append((x, y))
    
    for i in range(5):
        cv2.line(top_image, (150, 150), points[i], (0, 0, 0), 2)
    
    return top_image

def create_simulated_durian_images():
    """Create simulated durian images for testing"""
    top_image = create_simulated_top_image()
    
    # Create simulated side view images
    side_images = []
    for i in range(6):  # Maximum 6 segments
        side_image = np.zeros((200, 200, 3), dtype=np.uint8)
        
        # Draw a durian segment shape
        pts = np.array([[100, 50], [150, 100], [100, 150], [50, 100]], np.int32)
        pts = pts.reshape((-1, 1, 2))
        cv2.fillPoly(side_image, [pts], (139, 69, 19))
        
        side_images.append(side_image)
    
    return top_image, side_images

# Main function to demonstrate the system
def main():
    # Create the grading system
    grading_system = DurianGradingSystem()
    
    # Ask user for image paths
    use_real_images = input("ต้องการใช้ภาพจริงหรือไม่? (y/n): ").lower() == 'y'
    
    if use_real_images:
        top_image_path = input("ระบุ path ของภาพมุมบนของทุเรียน: ")
        side_images_folder = input("ระบุ path ของโฟลเดอร์ที่มีภาพด้านข้างของทุเรียน (หรือกด Enter เพื่อข้าม): ")
        
        if not side_images_folder:
            side_images_folder = None
            
        # Load real images
        top_image, side_images = load_real_durian_images(top_image_path, side_images_folder)
        
        # Process the durian
        durian, top_image_processed = grading_system.process_durian(top_image, side_images)
        
        # Print durian information
        print(f"\nDurian #{durian.id} has {len(durian.segments)} segments:")
        for segment in durian.segments:
            print(f"  Segment {segment.id}: {segment.type}")
        print(f"Grade: {durian.grade}")
        
        # Visualize the results
        grading_system.visualize_results(durian, top_image_processed, side_images)
        
    else:
        # Process multiple simulated durians
        num_durians = int(input("จำนวนทุเรียนที่ต้องการจำลอง: ") or "3")
        
        for i in range(num_durians):
            print(f"\nProcessing durian #{i+1}...")
            
            # Create simulated images
            top_image, side_images = create_simulated_durian_images()
            
            # Process the durian
            durian, top_image_processed = grading_system.process_durian(top_image, side_images)
            
            # Print durian information
            print(f"Durian #{durian.id} has {len(durian.segments)} segments:")
            for segment in durian.segments:
                print(f"  Segment {segment.id}: {segment.type}")
            print(f"Grade: {durian.grade}")
            
            # Visualize the results
            grading_system.visualize_results(durian, top_image_processed, side_images)
    
    # Generate report
    grading_system.generate_report()

if __name__ == "__main__":
    main()