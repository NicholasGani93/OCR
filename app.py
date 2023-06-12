import os
from flask import Flask, request, redirect, jsonify
from werkzeug.utils import secure_filename
from werkzeug.exceptions import BadRequest,HTTPException
import urllib.request
from PIL import Image, ImageDraw, ImageFont
import base64
from io import BytesIO

UPLOAD_FOLDER = 'images'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

class ResponseBody:
	def __init__(self, message=""):
		self.message = message
		self.image_result = None

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def watermark(filepath, text, rotation=0, is_repeat=False, opacity=1):
	original_image = Image.open(filepath)
	watermark_image = original_image.copy()
	draw = ImageDraw.Draw(watermark_image)

	w, h = watermark_image.size
	x, y = int(w / 2), int(h / 2)
	if x > y:
		font_size = y
	elif y > x:
		font_size = x
	else:
		font_size = x

	font = ImageFont.truetype("fonts/arial.ttf", int(font_size/6))

	# add watermark
	draw.text((x, y), text, fill=(0, 0, 0), font=font, anchor='ms')
	im_file = BytesIO()
	watermark_image.save(im_file, format="JPEG")
	im_bytes = im_file.getvalue()
	return base64.b64encode(im_bytes)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

isExist = os.path.exists(app.config['UPLOAD_FOLDER'])
if not isExist:
	os.mkdir(app.config['UPLOAD_FOLDER'])

@app.route('/')
def index():
    return jsonify({'message': 'Welcome'})

@app.route('/watermark', methods=['POST'])
def upload_file():
	file = None
	result_image = None
	image_url = ''
	watermark_text = ''
	if request.content_type.startswith('application/json'):
		json_body = request.json
		if 'watermark' not in json_body:
			resp = jsonify(ResponseBody('No watermark in the request').__dict__)
			resp.status_code = 400
			return resp
		watermark_text = json_body['watermark']
		if watermark_text == '':
			resp = jsonify(ResponseBody('Watermark cannot be empty').__dict__)
			resp.status_code = 400
			return resp
		if 'image_url' not in json_body:
			resp = jsonify(ResponseBody('No file part in the request').__dict__)
			resp.status_code = 400
			return resp
		image_url = json_body['image_url']
		if image_url == '':
			resp = jsonify(ResponseBody('No base file send').__dict__)
			resp.status_code = 400
			return resp
	elif(request.content_type.startswith("application/x-www-form-urlencoded")):
		if 'watermark' not in request.form:
			resp = jsonify(ResponseBody('No watermark in the request').__dict__)
			resp.status_code = 400
			return resp
		watermark_text = request.form['watermark']
		if watermark_text == '':
			resp = jsonify(ResponseBody('Watermark cannot be empty').__dict__)
			resp.status_code = 400
			return resp
		# check if the post request has the file part
		if 'file' not in request.files and 'image_url' not in request.form:
			resp = jsonify(ResponseBody('No file part in the request').__dict__)
			resp.status_code = 400
			return resp
		if 'file' in request.files:
			file = request.files['file']
		if 'image_url' in request.form:
			image_url = request.form['image_url']
		if (file == None or file.filename == '') and image_url == '':
			resp = jsonify(ResponseBody('No base file send').__dict__)
			resp.status_code = 400
			return resp
	if image_url != '':
		filename = 'temp.jpg'
		urllib.request.urlretrieve(image_url,filename)
		result_image = watermark(filename,watermark_text)
	elif file and allowed_file(file.filename):
		filename = secure_filename(file.filename)
		fullpath = os.path.join(os.getcwd(),app.config['UPLOAD_FOLDER'],filename)
		file.save(fullpath)
		result_image = watermark(fullpath,watermark_text)
	else:
		resp = jsonify(ResponseBody('Allowed file types are png, jpg, jpeg').__dict__)
		resp.status_code = 400
		return resp
	resp_body = ResponseBody('Success apply watermark')
	resp_body.image_result = result_image.decode('utf-8')
	resp = jsonify(resp_body.__dict__)
	resp.status_code = 201
	return resp
	
@app.errorhandler(BadRequest)
def handle_bad_request(e):
    return 'bad request!', 400
    
# @app.errorhandler(HTTPException)
# def handle_exception(e):
# 	"""Return JSON instead of HTML for HTTP errors."""
# 	# start with the correct headers and status code from the error
# 	response = e.get_response()
# 	# replace the body with JSON
# 	resp_body = jsonify(ResponseBody('Internal Server error').__dict__)
# 	resp_body.status_code = 500
# 	response.data = resp_body
# 	response.content_type = "application/json"
# 	return response

# or, without the decorator
app.register_error_handler(400, handle_bad_request)

if __name__ == '__main__':
    app.run(debug=True)