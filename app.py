import cv2
from flask import Flask, Response, request, render_template
from roboflow import Roboflow
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import smtplib

app = Flask(__name__)

ROBOFLOW_API_KEY = 'NmAbA1QRNGTcU3m5SNKG'
rf = Roboflow(api_key=ROBOFLOW_API_KEY)

project_name = "weapon-detection-f1lih"
model_version = 1

webcam_streaming = False
cap = None
weapons = ["Knife", "Pistol", "grenade"]

smtp_server = 'smtp.gmail.com'  
smtp_port = 587
smtp_username = 'crimedetectionproject@gmail.com'  
smtp_password = 'pyrv xlfs zalm syxy'

def send_email_notification(frame, object_name):
    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = 'abhinavmodem@gmail.com, reddyashok399@gmail.com'
        msg['Subject'] = 'Weapon Detected Alert'
        
        body = f"A weapon has been detected in camera:\nObject name: {object_name}"
        body_msg = MIMEText(body, 'plain', 'utf-8')
        msg.attach(body_msg)

        if capture_screenshot:
            _, screenshot_data = cv2.imencode('.jpg', frame)
            screenshot_bytes = screenshot_data.tobytes()
            screenshot = MIMEImage(screenshot_bytes, name='screenshot.jpg')
            msg.attach(screenshot)

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_username, msg['To'].split(','), msg.as_string())
        server.quit()

        return 'Email sent!'
    except Exception as e:
        return f"Error sending email: {str(e)}"

def draw_annotations(frame, annotations):
    for annotation in annotations:
        x = annotation['x']
        y = annotation['y']
        width = annotation['width']
        height = annotation['height']
        label = annotation['class']
        confidence = annotation['confidence']

        x1 = int(x - width / 2)
        y1 = int(y - height / 2)
        x2 = int(x + width / 2)
        y2 = int(y + height / 2)

        color = (0, 255, 0)
        thickness = 2
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
        label_text = f"{label}: {confidence:.2f}"
        cv2.putText(frame, label_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness)

def webcam():
    global cap, capture_screenshot

    while True:
        if webcam_streaming:
            ret, frame = cap.read()

            if not ret:
                break

            response = model.predict(frame, confidence=40, overlap=30)
            annotations = response.json()['predictions']

            weapon_detected = False
            detected_label = ""

            for annotation in annotations:
                label = annotation['class']
                if label in weapons:
                    weapon_detected = True
                    detected_label = label
                    break

            if weapon_detected:
                draw_annotations(frame, annotations)
                capture_screenshot = True 
                print(send_email_notification(frame, detected_label))
                capture_screenshot = False
            
            _, jpeg = cv2.imencode('.jpg', frame)
            frame_bytes = jpeg.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed', methods=['POST', 'GET'])
def video_feed():
    global webcam_streaming, cap, model  

    if request.method == 'POST':
        webcam_streaming = True

        cap = cv2.VideoCapture(0)
        cap.set(3, 640)
        cap.set(4, 480)

        project = rf.workspace().project(project_name)
        model = project.version(model_version).model
    
    return Response(webcam(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True)
