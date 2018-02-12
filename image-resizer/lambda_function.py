import boto3
import PIL
from PIL import Image, ImageOps
from io import BytesIO
from os import path

s3 = boto3.resource('s3')
origin_bucket = 'static-printweb-com-au'
destination_bucket = 'static-resized-printweb-com-au'
thumb_size = 128, 128
width_size = 256

def lambda_handler(event, context):
    
    for key in event.get('Records'):
        object_key = key['s3']['object']['key']
        extension = path.splitext(object_key)[1].lower()
        format = _get_file_format(extension)

        # Grabs the source file
        obj = s3.Object(
            bucket_name=origin_bucket,
            key=object_key,
        )
        obj_body = obj.get()['Body'].read()
        resized_image = _resize_image(obj_body, format)

        # Uploading the image
        obj = s3.Object(
            bucket_name=destination_bucket,
            key=object_key,
        )
        obj.put(Body=resized_image)

        # Printing to CloudWatch
        print('File saved at {}/{}'.format(
            destination_bucket,
            object_key,
        ))

# Resizing the image
def _resize_image(obj_body, format):
    img = Image.open(BytesIO(obj_body))
    thumb = ImageOps.fit(img, thumb_size, Image.ANTIALIAS, 0.0, (0.5, 0.5))
    return thumb
    # img = Image.open(BytesIO(obj_body))
    # wpercent = (width_size / float(img.size[0]))
    # hsize = int((float(img.size[1]) * float(wpercent)))
    # img = img.resize((width_size, hsize), PIL.Image.ANTIALIAS)
    # buffer = BytesIO()
    # img.save(buffer, format)
    # buffer.seek(0)

    # return buffer

def _get_file_format(extension):
    # Checking the extension and
    # Defining the buffer format
    if extension in ['.jpeg', '.jpg']:
        format = 'JPEG'
    if extension in ['.png']:
        format = 'PNG'
    if extension in ['.gif']:
        format = 'GIF'
    if extension in ['.bmp']:
        format = 'BMP'
    
    return format