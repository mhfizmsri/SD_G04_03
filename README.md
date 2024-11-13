
# SD_SEC03_G04
Website:
1. Clone the repository.
2. Download Node.js from the link (https://nodejs.org/en).
3. Download and install the Firebase CLI from [Firebase CLI Documentation](https://firebase.google.com/docs/cli).
Download and set up Face API:
4. Go to the Face API GitHub repository (https://github.com/justadudewhohacks/face-api.js).
Download the face-api.js file and place it in your project directory under the js folder. Ensure that you also have face-api.min.js (if needed) to integrate Face API in your project.
5. Create a Firebase project and set up Firestore and Firebase Authentication.
6. Follow the YouTube link to host the project (https://youtu.be/gtcUIQNhgyQ?si=VczyBU1eS0zkXS0W).
7. Open the local server that showed in the command prompt.
8. Enter the user id and password of the users and you can now access to our system.

Device(Raspberry Pi): 
1. Clone the "Device.py" repository to your Raspberry Pi.
2. Install dependencies:
("pip install opencv-python firebase-admin face_recognition numpy")
("sudo apt-get install python3-lgpio")
3. Download face-api.js from Face API GitHub (https://github.com/justadudewhohacks/face-api.js) if needed.
4. Download haarcascade_frontalface_default.xml from OpenCV GitHub (https://github.com/opencv/opencv/tree/master/data/haarcascades) and place it in the specified path.
5. Set up Firebase with Firestore and Authentication. Download the service account key JSON file and place it in the specified location.
6. Connect the buzzer to GPIO 20 and GND. Ensure Device.py has the correct GPIO configuration.
7. Connect and enable the Raspberry Pi Camera using ("sudo raspi-config"), then reboot. Test with ("raspistill -o test.jpg").
8. Run Device.py with python3 Device.py and check that all components are functioning.
9. Access the website admin page, go to "View Exam," and select an exam to start scanning attendance.


Link of Github for source code (https://github.com/mhfizmsri/SD_G04_03)

Link of the project (https://utmsmartscan.firebaseapp.com/)

List of the username and password:

Student User Id: 
1.muhafiz@graduate.utm.my Password:Ayam123
2.nging@graduate.utm.my Password: nging2004

Admin User Id: 
1.muhafizmasri2004@gmail.com Password:Admin123#
2.chee.sen987@gmail.com Password: Admin123!


