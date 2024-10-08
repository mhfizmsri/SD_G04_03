import cv2
import firebase_admin
from firebase_admin import credentials, firestore
import face_recognition
import numpy as np
from datetime import datetime
import time  # Use time directly
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

def check_face_in_firebase(face_descriptor):
    if face_descriptor is None:
        print("Error: Face descriptor is None.")
        return None

    users_ref = db.collection('users')
    users = users_ref.stream()

    for user in users:
        user_data = user.to_dict()
        stored_face_descriptor = user_data.get("Face")

        # Validate that the face descriptor is a valid array
        if stored_face_descriptor is None or not isinstance(stored_face_descriptor, list) or len(stored_face_descriptor) != 128:
            print(f"Warning: Invalid face descriptor for user {user_data['Name']}. Skipping.")
            continue

        try:
            # Convert the stored face descriptor to a NumPy array
            stored_face_descriptor = np.array(stored_face_descriptor, dtype=np.float64)
        except ValueError as e:
            print(f"Error converting face descriptor for user {user_data['Name']}: {e}")
            continue

        # Compare face descriptors
        distance = face_recognition.face_distance([stored_face_descriptor], face_descriptor)[0]
        if distance < 0.4:
            print(f"User found: {user_data['Name']}")
            return user_data

    print("No matching face found in Firebase.")
    return None

def mark_attendance(user_data):
    attendance_ref = db.collection('attendance').document()
    attendance_ref.set({
        'Name': user_data['Name'],
        'Time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    print(f"Attendance marked for {user_data['Name']}.")

def draw_green_tick(frame):
    # Draw a green tick mark
    cv2.line(frame, (150, 100), (200, 150), (0, 255, 0), 5)  # First part of the tick
    cv2.line(frame, (200, 150), (275, 75), (0, 255, 0), 5)   # Second part of the tick

def draw_red_cross(frame):
    # Draw a red cross
    cv2.line(frame, (150, 100), (275, 225), (0, 0, 255), 5)  # First diagonal line
    cv2.line(frame, (275, 100), (150, 225), (0, 0, 255), 5)

def main():
    try:
        cap = cv2.VideoCapture(0)
        display_message = ""
        display_message_start = 0
        display_symbol = None

        while True:
            ret, frame = cap.read()
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)

            if time.time() - display_message_start > 5:
                display_message = ""
                display_symbol = None

            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

            # Check for face recognition and attendance marking
            if not display_message:
                for (x, y, w, h) in faces:
                    face_encoding = face_recognition.face_encodings(rgb_frame, [(y, x+w, y+h, x)])
                    if face_encoding:
                        face_descriptor = face_encoding[0]
                        user_data = check_face_in_firebase(face_descriptor)
                        if user_data:
                            mark_attendance(user_data)
                            lgpio.gpio_write(chip, buzzer_pin, 1)  # Turn buzzer ON
                            time.sleep(0.2)  # Wait for 0.5 seconds
                            lgpio.gpio_write(chip, buzzer_pin, 0)  # Turn buzzer OFF
                            display_message = f"Scan Success: {user_data['Name']}"
                            display_symbol = "success"
                        else:
                            lgpio.gpio_write(chip, buzzer_pin, 1)  # Turn buzzer ON
                            time.sleep(1)  # Wait for 0.5 seconds
                            lgpio.gpio_write(chip, buzzer_pin, 0)  # Turn buzzer OFF
                            display_message = "Scan Denied"
                            display_symbol = "failure"
                        display_message_start = time.time()

            # Display the message on the screen
            if display_message:
                if "Success" in display_message:
                 text_color = (0, 255, 0)  # Green for success
                else:
                    text_color = (0, 0, 255)  # Red for failure
                cv2.putText(frame, display_message, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, text_color, 2)
            
            if display_symbol == "success":
                draw_green_tick(frame)  # Draw green tick on frame
            elif display_symbol == "failure":
                draw_red_cross(frame)

            # Show the frame
            cv2.imshow('Face Recognition', frame)

            # Check if 'k' is pressed to stop the program
            if cv2.waitKey(1) & 0xFF == ord('k'):  # 'k' is the kill button
                print("Kill button pressed. Exiting the program.")
                break
    finally:
        # Clean up GPIO and release resources when the program exits
        lgpio.gpio_write(chip, buzzer_pin, 0)  # Ensure the buzzer is off
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()