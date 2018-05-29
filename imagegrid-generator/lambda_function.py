# This script creates individual thumbnail iamges from the mail source and stores them seperatly into a resized bucket
# It also generates a thumbnail grid of all the resized images

import boto3
import botocore.config
import PIL
from PIL import Image, ImageOps, ImageDraw
from io import BytesIO
from io import StringIO
from os import path
import threading
import time
from urllib.request import urlopen


s3 = boto3.resource('s3')
origin_bucket = 'static-resized-printweb-com-au'
destination_bucket = 'static-resized-printweb-com-au'
region = 's3-ap-southeast-2.amazonaws.com'
tile_size = 185
cols = 3
col_spacing = 4

def lambda_handler(event, context):
    if(event.get('type') == 'thumb'):
        return generate_thumb_grid(event)

# def get_file_from_s3(key, folder_path, downloaded_images):
#     object_key = path.join(folder_path,key)
#     print('src bucket : ', origin_bucket)
#     print('src key : ', object_key)
#     # Grabs the source file
#     obj = s3.Object(
#         bucket_name=origin_bucket,
#         key=object_key,
#     )
#     obj_body = obj.get()['Body'].read()
#     if(obj_body):
#         downloaded_images.append(obj_body)
#         return True
#     else:
#         return False

def getFileFromUrl(url, downloaded_images):
    img_file = urlopen(url)
    im = BytesIO(img_file.read())

    if(im):
        downloaded_images.append(Image.open(im))
        return True
    else:
        return False

def generate_thumb_grid(event):
    downloaded_images = []
    size = (tile_size+col_spacing)*cols - col_spacing
    folder_path = path.join(event.get('uuid'), 'thumb')
    product_type = event.get('product_type')
    canvas = Image.new('RGB', (size, size),color=(255,255,255))
    dest_object_key = path.join(folder_path, 'thumb_grid.png')
    
    print('Product Type: ', product_type)
    print('uuid ', event.get('uuid'))
    
    obj = s3.Object(
        bucket_name=destination_bucket,
        key=dest_object_key,
    )

    for url in event.get('files'):
        print(url)
        getFileFromUrl(url, downloaded_images)

    # CREATE CLASSIC
    if(product_type == 'classic'):
        for (i, obj_body) in enumerate(downloaded_images):
            if(obj_body):
                # paste data onto canvas
                x_pos = int((i % cols) * (tile_size+col_spacing))
                y_pos = int(i / (cols)) * (tile_size+col_spacing)
                # img = Image.open(BytesIO(obj_body))
                canvas.paste(obj_body, (x_pos, y_pos))
        print ("Classic tiles")
        # save file
        in_mem_file = BytesIO()
        canvas.save(in_mem_file, 'PNG')
        obj.put(Body=in_mem_file.getvalue())

    # CREATE mosaic
    elif product_type == 'mosaque':
        obj_body = downloaded_images[0]
        # canvas = Image.open(BytesIO(obj_body))
        canvas = obj_body
        print(size)
        print ("Mosaque tiles")
        canvas.thumbnail((size, size))

        # -----------------------
        # draw lines
        draw = ImageDraw.Draw(obj_body)

         # do vertical lines
        for i in range(1, cols):
            x0 = int(i * (tile_size))
            y0 = 0

            x1 = x0 + col_spacing
            y1 = size
            pos = (x0, y0, x1, y1)
            print('vpos : ', pos)
            draw.rectangle(pos, fill=(255,255,255))

        # do horizontal lines
        for i in range(1, cols):
            x0 = 0
            y0 = int(i * (tile_size))

            x1 = size
            y1 = y0 + col_spacing
            pos = (x0, y0, x1, y1)
            print('hpos : ', pos)
            draw.rectangle(pos, fill=(255,255,255))

        in_mem_file = BytesIO()
        canvas.save(in_mem_file, 'PNG')
        obj.put(Body=in_mem_file.getvalue())
    else:
        print('Error - no product type supplied')

    # Printing to CloudWatch
    print('File saved at {}/{}'.format(
        destination_bucket,
        dest_object_key,
    ))

    # clear from memory
    in_mem_file = None
    canvas = None
    obj = None
    downloaded_images = None

    p = 'https://'+destination_bucket+'.'+region
    return {'data': path.join(p, dest_object_key)}