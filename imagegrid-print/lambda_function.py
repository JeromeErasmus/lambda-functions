# This script creates individual thumbnail iamges from the mail source and stores them seperatly into a resized bucket
# It also generates a thumbnail grid of all the resized images

import boto3
import botocore.config
import PIL
import json
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
tile_size = 567
cols = 3
col_spacing = 23
bleed = 60


def lambda_handler(event, context):
    generate_grid(event)

def getFileFromUrl(url, downloaded_images):
    img_file = urlopen(url)
    im = BytesIO(img_file.read())

    if(im):
        downloaded_images.append(Image.open(im))
        return True
    else:
        return False

def generate_grid(event):
    downloaded_images = []
    # size = ((tile_size+col_spacing)*(cols)) + (bleed * 2) - col_spacing
    size = getCanvasPrintSize()

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

    for url in event.get('files'):
        print(url)
        getFileFromUrl(url, downloaded_images)

    # CREATE CLASSIC
    if(product_type == 'classic'):
        for (i, obj_body) in enumerate(downloaded_images):
            if(obj_body):
                # paste data onto canvas
                x_pos = int((i % cols) * (tile_size+col_spacing)) + bleed
                y_pos = int(i / (cols)) * (tile_size+col_spacing) + bleed
                canvas.paste(obj_body, (x_pos, y_pos))
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
        x_pos = bleed
        y_pos = bleed
        # resize_size = ( size-(col_spacing*2) ) - ( int(col_spacing / 2) )
        # img = obj_body.resize((resize_size, resize_size), PIL.Image.ANTIALIAS)

        canvas.paste(obj_body, (x_pos, y_pos))
        print(size)
        print ("Mosaque tiles")
        # canvas.thumbnail((size, size))

        # -----------------------
        # draw lines
        draw = ImageDraw.Draw(canvas)

        #do vertical lines
        for i in range(1, cols):
            x0 = int(i * (tile_size+col_spacing)) + 36
            y0 = 0

            x1 = x0 + col_spacing
            y1 = size
            pos = (x0, y0, x1, y1)
            print('vpos : ', pos)
            draw.rectangle(pos, fill=(255,255,255))

        # # do horizontal lines
        for i in range(1, cols):
            x0 = 0
            y0 = int(i * (tile_size+col_spacing)) + 36

            x1 = size
            y1 = y0 + col_spacing
            pos = (x0, y0, x1, y1)
            print('hpos : ', pos)
            draw.rectangle(pos, fill=(255,255,255))

        # do bleed and cropmarks
        canvas_printready = add_cropmarks(canvas, size)
        
        in_mem_file = BytesIO()
        canvas_printready.save(in_mem_file, 'PNG')
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

def getCanvasPrintSize():
    return 1867
    # tile_w = tile_size*3 
    # cols_w = (cols-1) * col_spacing

    # return tile_w + cols_w + (bleed * 2) #1773 + 92 + 118

def add_cropmarks(canvas, size):
    print("adding cropmarks and bleed")
    # draw lines
    draw = ImageDraw.Draw(canvas)

    gap_width = (tile_size+col_spacing) 
    increment_offset = int(col_spacing/2)+2

    # do vertical lines
    for i in range(1, (cols+2)):
        increment = ((i*gap_width) - gap_width) - increment_offset
        x0 = increment + bleed
        x1 = x0 + 1
        pos1 = (x0, 0, x1, int(bleed / 4))
        pos2 = (x0, size - int(bleed / 4), x1, size)
        draw.rectangle(pos1, fill=(0,0,0))
        draw.rectangle(pos2, fill=(0,0,0))

    # do horizontal lines
    for i in range(1, (cols+2)):
        increment = ((i*gap_width) - gap_width) - increment_offset
        y0 = increment + bleed
        y1 = y0 + 1
        # x1 = int(bleed / 4)
        # x0 = 0
        pos1 = (0, y0, int(bleed / 4), y1)
        pos2 = (size, y0, size - int(bleed / 4), y1)
        draw.rectangle(pos1, fill=(0,0,0))
        draw.rectangle(pos2, fill=(0,0,0))
    return canvas