import boto3
import botocore.config
import PIL
from PIL import Image, ImageOps
from io import BytesIO
from os import path
import threading
import time

s3 = boto3.resource('s3')
origin_bucket = 'static-resized-printweb-com-au'
destination_bucket = 'static-resized-printweb-com-au'
region = 's3-ap-southeast-2.amazonaws.com'
tile_size = 64
cols = 3
col_spacing = 4
downloaded_images = []
start = time.time()

def lambda_handler(event, context): 
    if(event.get('type') == 'thumb'):
        return generate_thumb_grid(event)

def get_file_from_s3(key, folder_path):
    object_key = path.join(folder_path,key)

    # Grabs the source file
    obj = s3.Object(
        bucket_name=origin_bucket,
        key=object_key,
    )
    obj_body = obj.get()['Body'].read()
    if(obj_body):
        downloaded_images.append(obj_body)
        return True
    else:
        return False

def generate_thumb_grid(event):
    size = (tile_size+col_spacing)*cols - col_spacing
    canvas = Image.new('RGB', (size, size),color=(255,255,255))
    folder_path = path.join(event.get('uuid'), 'thumb')
    
    # thread load the files in async. Warning S3 boto is not thread safe
    for key in event.get('files'):
        t = threading.Thread(target = get_file_from_s3, args=(key, folder_path,))
        t.start()
        t.join()

    for (i, obj_body) in enumerate(downloaded_images):
        if(obj_body):
            # paste data onto canvas
            x_pos = int((i % cols) * (tile_size+col_spacing))
            y_pos = int(i / (cols)) * (tile_size+col_spacing)
            
            img = Image.open(BytesIO(obj_body))
            print(img, i)
            # img = Image.open(path.join('thumb', key))
            canvas.paste(img, (x_pos, y_pos))

    # save file
    dest_object_key = path.join(folder_path, 'thumb_grid.png')
    obj = s3.Object(
        bucket_name=destination_bucket,
        key=dest_object_key,
    )
    
    in_mem_file = BytesIO()
    canvas.save(in_mem_file, 'PNG')
    obj.put(Body=in_mem_file.getvalue())

    # Printing to CloudWatch
    print('File saved at {}/{}'.format(
        destination_bucket,
        dest_object_key,
    ))

    p = 'https://'+destination_bucket+'.'+region
    return {'data': path.join(p, dest_object_key)}


# Resizing the image
def _resize_image(obj_body):
    img = Image.open(BytesIO(obj_body))
    thumb = ImageOps.fit(img, resample_size, Image.ANTIALIAS, 0.0, (0.5, 0.5))

    in_mem_file = BytesIO()
    thumb.save(in_mem_file, 'PNG')
    return in_mem_file.getvalue()


