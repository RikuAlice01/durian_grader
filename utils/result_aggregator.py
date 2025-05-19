from statistics import mean, mode
from collections import Counter

def status_from_score(score):
    if score > 0.75:
        return 'Full'
    elif score > 0.35:
        return 'Half'
    else:
        return 'Empty'

def calculate_final_grade(combined_info):
    score_table = {'Full': 2, 'Half': 1, 'Empty': 0}
    left_score = score_table[combined_info['left']['status']]
    right_score = score_table[combined_info['right']['status']]
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

def aggregate_results(result_list):
    """
    รวมผลลัพธ์จากหลายภาพ (dicts ที่มี key: left_score, right_score, grade)
    คืนค่า dict สรุปผล
    """
    if not result_list:
        return {
            'summary': "No valid results to aggregate.",
            'grade': "N/A"
        }

    left_scores = [r['left_score'] for r in result_list]
    right_scores = [r['right_score'] for r in result_list]
    grades = [r['grade'] for r in result_list]

    avg_left = mean(left_scores)
    avg_right = mean(right_scores)
    most_common_grade = mode(grades) if grades else "N/A"

    left_status = status_from_score(avg_left)
    right_status = status_from_score(avg_right)

    combined_info = {
        'left': {'status': left_status, 'score': avg_left},
        'right': {'status': right_status, 'score': avg_right}
    }

    final_grade = calculate_final_grade(combined_info)

    summary_text = (
        f"🔍 รวมผลวิเคราะห์จาก {len(result_list)} มุม:\n"
        f"  ▸ Left avg score: {avg_left:.2f} → {left_status}\n"
        f"  ▸ Right avg score: {avg_right:.2f} → {right_status}\n"
        f"  ▸ Most common grade: {most_common_grade}\n"
        f"🎓 Final Aggregated Grade: {final_grade}"
    )

    return {
        'summary': summary_text,
        'grade': final_grade,
        'left_avg': avg_left,
        'right_avg': avg_right,
        'left_status': left_status,
        'right_status': right_status,
        'individual_grades': grades
    }
