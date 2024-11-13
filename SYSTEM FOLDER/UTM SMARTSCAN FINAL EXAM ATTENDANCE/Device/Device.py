import cv2
import firebase_admin
from firebase_admin import credentials, firestore
import face_recognition
import numpy as np
from datetime import datetime
import time
import lgpio

# GPIO setup
chip = lgpio.gpiochip_open(0)
buzzer_pin = 20
lgpio.gpio_claim_output(chip, buzzer_pin)

# Initialize Firebase
cred = credentials.Certificate("/home/muhafiz/Downloads/utmsmartscan-firebase-adminsdk-5gtap-ee911ca231.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Load the face detector (Haar Cascade)
face_cascade = cv2.CascadeClassifier('/home/muhafiz/Downloads/haarcascade_frontalface_default.xml')

# Variables for tracking the exit button state and position
button_pressed = False
button_width, button_height = 150, 75  # Adjusted for better visibility on larger displays

def get_active_exam():
    exams = db.collection('exam').stream()
    for exam in exams:
        exam_data = exam.to_dict()
        if exam_data.get("StartScan") == "Yes":
            return exam.id
    return None

def get_subjects_for_exam(exam_id):
    subjects = db.collection('exam').document(exam_id).collection('subject').stream()
    subject_ids = [subject.id for subject in subjects]
    return subject_ids

def check_face_in_users(face_descriptor):
    if face_descriptor is None:
        print("Error: Face descriptor is None.")
        return None, None

    users_ref = db.collection('users').stream()
    for user in users_ref:
        user_data = user.to_dict()
        stored_face_descriptor = user_data.get("Face")

        if stored_face_descriptor and isinstance(stored_face_descriptor, list) and len(stored_face_descriptor) == 128:
            try:
                stored_face_descriptor = np.array(stored_face_descriptor, dtype=np.float64)
                distance = face_recognition.face_distance([stored_face_descriptor], face_descriptor)[0]
                if distance < 0.4:
                    return user.id, user_data
            except ValueError:
                continue

    return None, None

def update_attendance(exam_id, subject_id, student_id, student_name):
    subject_ref = db.collection('exam').document(exam_id).collection('subject').document(subject_id)
    subject_data = subject_ref.get().to_dict()

    if subject_data and "students" in subject_data:
        students = subject_data["students"]
        updated = False

        for student in students:
            if student["id"] == student_id:
                student["attendance"] = "Yes"
                student["time"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                updated = True
                break

        if updated:
            subject_ref.update({"students": students})
            print(f"Attendance updated for {student_name}.")
        else:
            print(f"Student {student_name} not found in the subject.")

def draw_green_tick(frame):
    cv2.line(frame, (150, 100), (200, 150), (0, 255, 0), 5)
    cv2.line(frame, (200, 150), (275, 75), (0, 255, 0), 5)

def draw_red_cross(frame):
    cv2.line(frame, (150, 100), (275, 225), (0, 0, 255), 5)
    cv2.line(frame, (275, 100), (150, 225), (0, 0, 255), 5)

def end_program(event, x, y, flags, param):
    global button_pressed
    # Dynamically calculate the button position based on screen size
    screen_width, screen_height = param
    exit_button_position = (screen_width - button_width - 10, screen_height - button_height - 10)
    if event == cv2.EVENT_LBUTTONDOWN:
        if exit_button_position[0] <= x <= exit_button_position[0] + button_width and \
           exit_button_position[1] <= y <= exit_button_position[1] + button_height:
            button_pressed = True

def main():
    global button_pressed

    try:
        cap = cv2.VideoCapture(0)
        cv2.namedWindow('Face Recognition', cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty('Face Recognition', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        # Determine screen resolution dynamically
        ret, frame = cap.read()
        screen_height, screen_width = frame.shape[:2]
        exit_button_position = (screen_width - button_width - 10, screen_height - button_height - 10)

        # Set mouse callback with screen size as parameter
        cv2.setMouseCallback('Face Recognition', end_program, param=(screen_width, screen_height))

        display_message = "No active exam for scanning. Scanning will not start."
        display_message_start = 0
        display_symbol = None
        active_exam_id = None

        while True:
            if button_pressed:
                print("Exit button pressed. Ending the program.")
                break

            active_exam_id = get_active_exam()
            if not active_exam_id:
                ret, frame = cap.read()
                if not ret:
                    continue
                frame = np.zeros((screen_height, screen_width, 3), dtype=np.uint8)
                cv2.putText(frame, display_message, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                
                # Draw exit button dynamically in the bottom right corner
                cv2.rectangle(frame, exit_button_position, 
                              (exit_button_position[0] + button_width, exit_button_position[1] + button_height),
                              (0, 0, 255), -1)
                cv2.putText(frame, "EXIT", (exit_button_position[0] + 20, exit_button_position[1] + 45),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                
                cv2.imshow('Face Recognition', frame)
                if cv2.waitKey(1) & 0xFF == ord('k'):
                    break
                continue

            subject_ids = get_subjects_for_exam(active_exam_id)

            ret, frame = cap.read()
            if not ret:
                continue

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)

            if time.time() - display_message_start > 5:
                display_message = ""
                display_symbol = None

            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

            if not display_message:
                for (x, y, w, h) in faces:
                    face_encoding = face_recognition.face_encodings(rgb_frame, [(y, x + w, y + h, x)])
                    if face_encoding:
                        face_descriptor = face_encoding[0]
                        user_id, user_data = check_face_in_users(face_descriptor)
                        if user_data:
                            for subject_id in subject_ids:
                                update_attendance(active_exam_id, subject_id, user_id, user_data['Name'])
                            lgpio.gpio_write(chip, buzzer_pin, 1)
                            time.sleep(0.2)
                            lgpio.gpio_write(chip, buzzer_pin, 0)
                            display_message = f"Scan Success: {user_data['Name']}"
                            display_symbol = "success"
                        else:
                            lgpio.gpio_write(chip, buzzer_pin, 1)
                            time.sleep(1)
                            lgpio.gpio_write(chip, buzzer_pin, 0)
                            display_message = "Scan Denied"
                            display_symbol = "failure"
                        display_message_start = time.time()

            if display_message:
                text_color = (0, 255, 0) if "Success" in display_message else (0, 0, 255)
                cv2.putText(frame, display_message, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, text_color, 2)

            if display_symbol == "success":
                draw_green_tick(frame)
            elif display_symbol == "failure":
                draw_red_cross(frame)

            # Draw exit button
            cv2.rectangle(frame, exit_button_position,
                          (exit_button_position[0] + button_width, exit_button_position[1] + button_height),
                          (0, 0, 255), -1)
            cv2.putText(frame, "EXIT", (exit_button_position[0] + 20, exit_button_position[1] + 45),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

            cv2.imshow('Face Recognition', frame)
            if cv2.waitKey(1) & 0xFF == ord('k'):
                break
    finally:
        lgpio.gpio_write(chip, buzzer_pin, 0)
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
