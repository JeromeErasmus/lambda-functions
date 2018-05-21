# This script creates individual thumbnail iamges from the mail source and stores them seperatly into a resized bucket
# It also generates a thumbnail grid of all the resized images

import boto3
import botocore.config
import PIL
import json
from PIL import Image, ImageOps, ImageDraw
from io import BytesIO
from os import path
import threading
import time

s3 = boto3.resource('s3')
origin_bucket = 'static-resized-printweb-com-au'
destination_bucket = 'static-resized-printweb-com-au'
region = 's3-ap-southeast-2.amazonaws.com'
tile_size = 591
cols = 3
col_spacing = 46
bleed = 59

def lambda_handler(event, context):
    generate_grid(event)

def get_file_from_s3(key, folder_path, downloaded_images):
    object_key = path.join(folder_path,key)
    print('src bucket : ', origin_bucket)
    print('src key : ', object_key)
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

def generate_grid(event):
    downloaded_images = []
    size = ((tile_size+col_spacing)*(cols)) + (bleed * 2) - col_spacing
    src_folder_path =  path.join(event.get('uuid'), 'print')
    dest_folder_path = path.join(event.get('uuid'), 'print')
    product_type = event.get('product_type')
    canvas = Image.new('RGB', (size, size),color=(255,255,255))
    dest_object_key = path.join(dest_folder_path, 'grid-print.png')
    
    print('Product Type: ', product_type)
    print('uuid ', event.get('uuid'))
    
    obj = s3.Object(
        bucket_name=destination_bucket,
        key=dest_object_key,
    )

    # lambda_client = boto3.client('lambda')
    # event_payload = dict(size=tile_size, dest_path='print')
    for key in event.get('files'):
        get_file_from_s3(key, src_folder_path, downloaded_images)
        # call Lambda resizer
        # invoke_response = lambda_client.invoke(FunctionName="printweb-image-resizer",
        #                                    InvocationType='RequestResponse',
        #                                     Payload=json.dumps(event_payload)
        #                                    )

    # CREATE CLASSIC
    if(product_type == 'classic'):
        for (i, obj_body) in enumerate(downloaded_images):
            if(obj_body):
                # paste data onto canvas
                x_pos = int((i % cols) * (tile_size+col_spacing)) + bleed
                y_pos = int(i / (cols)) * (tile_size+col_spacing) + bleed
                img = Image.open(BytesIO(obj_body))
                canvas.paste(img, (x_pos, y_pos))
        print ("Classic tiles")

        # do bleed and cropmarks
        canvas_printready = add_cropmarks(canvas, size) 
        # save file
        in_mem_file = BytesIO()
        canvas_printready.save(in_mem_file, 'PNG')
        obj.put(Body=in_mem_file.getvalue())

    # CREATE mosaic
    elif product_type == 'mosaque':
        obj_body = downloaded_images[0]
        canvas = Image.open(BytesIO(obj_body))
        print(size)
        print ("Mosaque tiles")
        canvas.thumbnail((size, size))

        # -----------------------
        # draw lines
        draw = ImageDraw.Draw(canvas)

        # do vertical lines
        for i in range(1, cols):
            x0 = int(i * (tile_size+col_spacing))
            y0 = 0

            x1 = x0 + col_spacing
            y1 = size
            pos = (x0, y0, x1, y1)
            print('vpos : ', pos)
            draw.rectangle(pos, fill=(255,255,255))

        # do horizontal lines
        for i in range(1, cols):
            x0 = 0
            y0 = int(i * (tile_size+col_spacing))

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

def add_cropmarks(canvas, size):
    # draw lines
    draw = ImageDraw.Draw(canvas)

    # do vertical lines
    for i in range(1, (cols+2)):
        gap_width = (tile_size+col_spacing)
        increment = (int(i * gap_width) - int(col_spacing/2)) - gap_width
        x0 = increment + bleed
        x1 = x0 + 1
        pos1 = (x0, 0, x1, int(bleed / 4))
        pos2 = (x0, size - int(bleed / 4), x1, size)
        draw.rectangle(pos1, fill=(0,0,0))
        draw.rectangle(pos2, fill=(0,0,0))

    # do horizontal lines
    for i in range(1, (cols+2)):
        gap_width = (tile_size+col_spacing)
        increment = (int(i * gap_width) - int(col_spacing/2)) - gap_width
        y0 = increment + bleed
        y1 = y0 + 1
        # x1 = int(bleed / 4)
        # x0 = 0
        pos1 = (0, y0, int(bleed / 4), y1)
        pos2 = (size, y0, size - int(bleed / 4), y1)
        draw.rectangle(pos1, fill=(0,0,0))
        draw.rectangle(pos2, fill=(0,0,0))
    return canvas