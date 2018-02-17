import boto3
import PIL
from PIL import Image, ImageOps
from io import BytesIO
from os import path

s3 = boto3.resource('s3')
origin_bucket = 'static-printweb-com-au'
destination_bucket = 'static-resized-printweb-com-au'
# desination_folder = 'uploads/'
resample_size = 64, 64

def lambda_handler(event, context):
    
    for key in event.get('Records'):
        object_key = key['s3']['object']['key']
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
        resized_image = _resize_image(obj_body)

        # Uploading the image
        # dest_object_key = _create_resampled_filename(thumb_folder_path, basename, 'png')
        new_file_name = '{0}.{1}'.format(basename, 'png')
        dest_object_key = path.join(thumb_folder_path, new_file_name)

        obj = s3.Object(
            bucket_name=destination_bucket,
            key=dest_object_key,
        )
        obj.put(Body=resized_image)

        # Printing to CloudWatch
        print('File saved at {}/{}'.format(
            destination_bucket,
            dest_object_key,
        ))

# Resizing the image
def _resize_image(obj_body):
    img = Image.open(BytesIO(obj_body))
    thumb = ImageOps.fit(img, resample_size, Image.ANTIALIAS, 0.0, (0.5, 0.5))

    in_mem_file = BytesIO()
    thumb.save(in_mem_file, 'PNG')
    return in_mem_file.getvalue()

def _create_resampled_filename(folder, file_name, ext):
    s = '{0}x{1}'.format(resample_size[0], resample_size[1])
    new_file_name = '{0}_{1}.{2}'.format(file_name, s, ext)

    return path.join(folder, new_file_name)
