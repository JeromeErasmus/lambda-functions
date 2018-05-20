# This script watches the original uploads bucket and creates resized versions of the uploaded files

import boto3
import PIL
from PIL import Image, ImageOps
from io import BytesIO
from os import path

s3 = boto3.resource('s3')
# origin_bucket = 'static-printweb-com-au'
destination_bucket = 'static-resized-printweb-com-au'
region = 's3-ap-southeast-2.amazonaws.com'
# desination_folder = 'uploads/'

def lambda_handler(event, context):
    
    # for key in event.get('Records'):
    object_key = event.get('file')['object_key']#key['s3']['object']['key']
    origin_bucket = event.get('file')['bucket_name']

    if event.get('size'): 
        resample_size = event.get('size'), event.get('size')
    else:
        resample_size = 128,128

    print(object_key)
    print(origin_bucket)
    print(event.get('size'))
    print(resample_size)
    basename_with_ext = path.basename(object_key)
    basename = path.splitext(basename_with_ext)[0]
    folder_basename = path.basename(path.dirname(object_key))
    thumb_folder_path = path.join(folder_basename, 'thumb')

    # Grabs the source file
    obj = s3.Object(
        bucket_name=origin_bucket,
        key=object_key,
    )
    obj_body = obj.get()['Body'].read()

    # CREATE THUMBNAIL
    resized_image = _resize_image(obj_body, resample_size)

    # Uploading the image
    new_file_name = '{0}.{1}'.format(basename, 'png')
    dest_object_key = path.join(thumb_folder_path, new_file_name)

    obj = s3.Object(bucket_name=destination_bucket, key=dest_object_key,)
    obj.put(Body=resized_image)

    # Printing to CloudWatch
    print('File saved at {}/{}'.format(
        destination_bucket,
        dest_object_key,
    ))

    p = 'https://'+destination_bucket+'.'+region
    return {'data': path.join(p, dest_object_key)}

# Resizing the image
def _resize_image(obj_body, resample_size):
    img = Image.open(BytesIO(obj_body))
    thumb = ImageOps.fit(img, resample_size, Image.ANTIALIAS, 0.0, (0.5, 0.5))

    in_mem_file = BytesIO()
    thumb.save(in_mem_file, 'PNG')
    return in_mem_file.getvalue()

# def _create_resampled_filename(folder, file_name, ext):
#     s = '{0}x{1}'.format(resample_size[0], resample_size[1])
#     new_file_name = '{0}_{1}.{2}'.format(file_name, s, ext)

#     return path.join(folder, new_file_name)
