# import boto3
import PIL
from PIL import Image, ImageOps
from io import BytesIO
from os import path
import threading

s3 = ''
origin_bucket = 'static-printweb-com-au'
destination_bucket = 'static-resized-printweb-com-au'
tile_size = 64
cols = 3
col_spacing = 4
downloaded_images = []

def get_file_from_s3(myfile):
    img = Image.open(path.join('thumb', myfile))
    print(img)
    if(img):
        downloaded_images.append(img)
        return True
    else:
        return False

def run():
    size = (tile_size+col_spacing)*cols - col_spacing
    canvas = Image.new('RGB', (size, size),color=(255,255,255))
    files = [
        "27878946_206477100089499_879342309873811456_n.png",
        "27575659_2058294521128396_2998052301215629312_n.png",
        "27892015_414567345638763_3545394240404062208_n.png",
        "27576187_278383172696298_641875792871030784_n.png",
        "26869123_1877135248987313_2142275523412230144_n.png",
        "26345717_140954673262880_3584371334903234560_n.png",
        "26871732_2012826105673849_4126337392376283136_n.png",
        "26864476_728803830662077_1828400872493678592_n.png",
        "27582306_988280247985883_3104767004272230400_n.png"
        ]
    
    # thread load the files in async. Warning S3 boto is not thread safe
    for fname in files:
        t = threading.Thread(target = get_file_from_s3, args=(fname,))
        t.start()
        t.join()
        
    
    for (i, key) in enumerate(downloaded_images):
        x_pos = int((i % cols) * (tile_size+col_spacing))
        y_pos = int(i / (cols)) * (tile_size+col_spacing)
     
        img = downloaded_images[i]
        canvas.paste(img, (x_pos, y_pos))
        # print(img, i)
        print(x_pos, y_pos)
    
    canvas.save('thumb_gridxx.png','PNG')

# Resizing the image
def _resize_image(img, format):
    
    # wpercent = (width_size / float(img.size[0]))
    # hsize = int((float(img.size[1]) * float(wpercent)))
    # img = img.resize((width_size, hsize), PIL.Image.ANTIALIAS)
    # buffer = BytesIO()

    # save the resized image 
    # img.save(buffer, format)
    # buffer.seek(0)

    # return buffer

    thumb = ImageOps.fit(img, thumb_size, Image.ANTIALIAS, 0.0, (0.5, 0.5))

    # img.thumbnail(thumb_size)
    thumb.save("output", format)
    
    return True


run()