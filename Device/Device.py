import cv2
import firebase_admin
from firebase_admin import credentials, firestore
import face_recognition
import numpy as np
from datetime import datetime
import time
from gpiozero import Buzzer
from time import sleep
buzzer = Buzzer(20)
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

def main():
    cap = cv2.VideoCapture(0)
    display_message = ""
    display_message_start = 0

    while True:
        ret, frame = cap.read()
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)

        if time.time() - display_message_start > 5:
            display_message = ""

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
                        buzzer.on()
                        sleep(1)
                        buzzer.off()
                        sleep(1)
                        display_message = f"Access Granted: {user_data['Name']}"
                    else:
                        display_message = "Access Denied"
                    display_message_start = time.time()

        # Display the message on the screen
        if display_message:
            cv2.putText(frame, display_message, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0) if "Granted" in display_message else (0, 0, 255), 2)

        # Show the frame
        cv2.imshow('Face Recognition', frame)

        # Check if 'k' is pressed to stop the program
        if cv2.waitKey(1) & 0xFF == ord('k'):  # 'k' is the kill button
            print("Kill button pressed. Exiting the program.")
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()