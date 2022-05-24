from flask import Flask, render_template, Response
import cv2
import datetime, time

app = Flask(__name__)

'''
for ip camera use - rtsp://username:password@ip_address:554/user=username_password='password'_channel=channel_number_stream=0.sdp' 
for local webcam use cv2.VideoCapture(0)
'''


# def reload_camera():
#     camera = cv2.VideoCapture(0)
#     return camera

# camera = None

# class Camera():
#     def __init__(self):
#         self.reload()

#     def __del__(self):
#         self.camera.release()
    
#     def read(self, tries=0):
#         print('reading')
#         success, frame =  self.camera.read()
#         if(not success):
#             self.reload()
#             print('reloading...', tries)
#             if(tries > 5):
#                 return False, None
#             return self.read(tries=tries+1)

#     def reload(self):
#         self.camera = cv2.VideoCapture(0)

# camera = Camera()
camera = cv2.VideoCapture(0)

def gen_frames():  
    # global camera 
    # if(camera is None):
    # camera = Camera()
    
    while True:
        success, frame = camera.read()  # read the camera frame
        frame = cv2.putText(
            frame,
            str(datetime.datetime.strftime(datetime.datetime.now(), '%m/%d/%Y, %H:%M:%S')),  
            (0,35),
            0,
            1,
            (255,255,0)
        )
        # print(success, frame)
        # if(not success):
        #     camera = cv2.VideoCapture(0)
        #     success, frame = camera.read()  # read the camera frame

        #     camera = reload_camera()
        #     success, frame = camera.read()  # read the camera frame

        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    # this_camera = Camera()
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=1236, debug=False) 
    # app.run(debug=True)