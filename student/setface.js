// Start the video stream and face scanning process
function startScan(auth, db, updateDoc, doc, storage, ref, uploadBytes, getDownloadURL) {
    // Load face-api models from CDN
    Promise.all([
      faceapi.nets.tinyFaceDetector.loadFromUri('https://cdn.jsdelivr.net/gh/justadudewhohacks/face-api.js/weights/tiny_face_detector_model-weights_manifest.json'),
      faceapi.nets.faceLandmark68Net.loadFromUri('https://cdn.jsdelivr.net/gh/justadudewhohacks/face-api.js/weights/face_landmark_68_model-weights_manifest.json'),
      faceapi.nets.faceRecognitionNet.loadFromUri('https://cdn.jsdelivr.net/gh/justadudewhohacks/face-api.js/weights/face_recognition_model-weights_manifest.json')
    ]).then(() => {
      console.log("Models loaded successfully.");
      document.getElementById('status').innerHTML = "Models loaded. Ready to scan!";
  
      document.getElementById('scanButton').addEventListener('click', async () => {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ video: true });
          const videoElement = document.getElementById('video');
          videoElement.srcObject = stream;
  
          videoElement.onloadedmetadata = () => {
            videoElement.play();
            document.getElementById('status').innerHTML = "Video started. Scanning face...";
            scanFace(auth, db, updateDoc, doc, storage, ref, uploadBytes, getDownloadURL);
          };
        } catch (err) {
          console.error("Camera access error: ", err);
          document.getElementById('status').innerHTML = "Failed to access camera: " + err.message;
        }
      });
    }).catch((err) => {
      console.error("Error loading models: ", err);
      document.getElementById('status').innerHTML = "Error loading models: " + err.message;
    });
  }
  
  // Scan face and detect landmarks using face-api.js
  async function scanFace(auth, db, updateDoc, doc, storage, ref, uploadBytes, getDownloadURL) {
    const video = document.getElementById('video');
    const canvas = faceapi.createCanvasFromMedia(video);
  
    // Ensure the video container exists before appending the canvas
    const videoContainer = document.getElementById('video-container');
    if (videoContainer) {
      videoContainer.append(canvas);
    } else {
      console.error("Video container not found!");
      return;
    }
  
    const displaySize = { width: video.videoWidth, height: video.videoHeight };
    faceapi.matchDimensions(canvas, displaySize);
  
    let faceDescriptors = [];
    const scanDuration = 10000; // Scan for 10 seconds
    const bestScanThreshold = 5; // Number of good scans required to mark as "best scan"
    let consecutiveGoodScans = 0;
  
    const interval = setInterval(async () => {
      const detections = await faceapi.detectAllFaces(video, new faceapi.TinyFaceDetectorOptions()).withFaceLandmarks().withFaceDescriptors();
      const resizedDetections = faceapi.resizeResults(detections, displaySize);
  
      // Clear previous canvas content
      canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height);
      faceapi.draw.drawDetections(canvas, resizedDetections);
      faceapi.draw.drawFaceLandmarks(canvas, resizedDetections);
  
      if (detections.length > 0) {
        // Collect face descriptors
        faceDescriptors.push(detections[0].descriptor);
        consecutiveGoodScans++;
  
        // If enough good scans are collected, mark as "best scan"
        if (consecutiveGoodScans >= bestScanThreshold) {
          document.getElementById('status').innerHTML = "Best scan detected! Please stand still...";
  
          // When enough face descriptors are collected, process the final scan
          if (faceDescriptors.length >= (bestScanThreshold * 2)) {
            clearInterval(interval);
            await processFinalScan(auth, db, updateDoc, doc, faceDescriptors, canvas, storage, ref, uploadBytes, getDownloadURL);
            stopVideo();
          }
        } else {
          document.getElementById('status').innerHTML = "Scanning face...";
        }
      } else {
        consecutiveGoodScans = 0; // Reset counter if face is not detected
      }
    }, 1000); // Run detection every second
  
    // Automatically stop scanning after 10 seconds
    setTimeout(() => {
      clearInterval(interval);
      if (faceDescriptors.length > 0) {
        processFinalScan(auth, db, updateDoc, doc, faceDescriptors, canvas, storage, ref, uploadBytes, getDownloadURL);
      }
      stopVideo();
    }, scanDuration);
  }
  
  // Stop the video stream
  function stopVideo() {
    const video = document.getElementById('video');
    video.srcObject.getTracks().forEach(track => track.stop());
  }
  
  // Process the final scan result
  async function processFinalScan(auth, db, updateDoc, doc, faceDescriptors, canvas, storage, ref, uploadBytes, getDownloadURL) {
    try {
      const user = auth.currentUser;
      if (user) {
        // Calculate the average descriptor from the collected face descriptors
        const avgDescriptor = calculateAverageDescriptor(faceDescriptors);
        await saveFaceData(auth, db, updateDoc, doc, avgDescriptor, canvas, storage, ref, uploadBytes, getDownloadURL);
        document.getElementById('status').innerHTML = "Face scan completed successfully!";
  
        // Reload the page after 2 seconds to reset
        setTimeout(() => {
          location.reload();
        }, 2000);
      } else {
        document.getElementById('status').innerHTML = "User is not authenticated.";
      }
    } catch (error) {
      console.error("Error processing final scan:", error);
      document.getElementById('status').innerHTML = "Failed to process face scan.";
    }
  }
  
  // Calculate the average face descriptor from multiple descriptors
  function calculateAverageDescriptor(descriptors) {
    const avgDescriptor = new Float32Array(descriptors[0].length);
    for (let i = 0; i < descriptors.length; i++) {
      for (let j = 0; j < descriptors[i].length; j++) {
        avgDescriptor[j] += descriptors[i][j] / descriptors.length;
      }
    }
    return avgDescriptor;
  }
  
  // Save the face descriptor and upload the image to Firebase Storage
  async function saveFaceData(auth, db, updateDoc, doc, faceDescriptor, canvas, storage, ref, uploadBytes, getDownloadURL) {
    try {
      const user = auth.currentUser;
      if (user) {
        // Convert the face descriptor from Float32Array to a regular array
        const faceDescriptorArray = Array.from(faceDescriptor);
  
        // Save the face descriptor in Firestore under the user's document
        const userDocRef = doc(db, "users", user.uid);
        await updateDoc(userDocRef, { "Face": faceDescriptorArray });
  
        // Capture the face image from the canvas
        const faceImage = await captureFaceImage(canvas);
  
        // Upload the face image to Firebase Storage
        const storageRef = ref(storage, `faces/${user.uid}/face.png`);
        const uploadResult = await uploadBytes(storageRef, faceImage);
  
        // Get the download URL of the uploaded image
        const downloadURL = await getDownloadURL(uploadResult.ref);
        await updateDoc(userDocRef, { "FaceImageURL": downloadURL });
  
        document.getElementById('status').innerHTML = "Face data and image saved successfully!";
      } else {
        document.getElementById('status').innerHTML = "User is not authenticated.";
      }
    } catch (error) {
      console.error("Error saving face data:", error);
      document.getElementById('status').innerHTML = "Failed to save face data.";
    }
  }
  
  // Capture the face image from the canvas as a Blob
  function captureFaceImage(canvas) {
    return new Promise((resolve, reject) => {
      canvas.toBlob((blob) => {
        if (blob) {
          resolve(blob); // Return the blob containing the image data
        } else {
          reject(new Error("Failed to capture face image"));
        }
      }, 'image/png'); // Save the image as PNG
    });
  }
  