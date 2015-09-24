from django.shortcuts import render
# Create your views here.
from django.views.generic import View
from django.http import HttpResponse, Http404
from django.template import RequestContext, loader, Template, Context
from PIL import Image, ImageOps
from pilkit.processors import Resize
from django.conf import settings
import os
from django.shortcuts import render_to_response

def create_img_paths(req_directory, req_img_name):
    img_path_dict = dict()
    img_path_dict['o_img'] = os.path.join(req_directory, req_img_name)
    img_path_dict['w_img'] = os.path.join(req_directory, \
			 os.path.splitext(req_img_name)[0]+'_w' + os.path.splitext(req_img_name)[1])
    img_path_dict['h_img'] = os.path.join(req_directory, \
			 os.path.splitext(req_img_name)[0]+'_h' + os.path.splitext(req_img_name)[1])
    print "Debug log: image path list %s" % img_path_dict
    return img_path_dict

def get_image_path(img_dict, req_img_priority):
    resp_img_path = None
    exist_flag = False
    for img_type, img_path in img_dict.iteritems():
        if os.path.exists(img_path):
            exist_flag = True
            break
    if not exist_flag:
        # also send dummy image
        raise Http404("Image does not exist")
    elif req_img_priority == 'h':
        if os.path.exists(img_dict['h_img']):
            resp_img_path = img_dict['h_img']
        else:
            if os.path.exists(img_dict['o_img']):
                resp_img_path = img_dict['o_img']
            else:
                resp_img_path = img_dict['w_img']
    else:
        if os.path.exists(img_dict['w_img']):
            resp_img_path = img_dict['w_img']
        else:
            if os.path.exists(img_dict['o_img']):
                resp_img_path = img_dict['o_img']
            else:
                resp_img_path = img_dict['h_img']
    return resp_img_path

def pixel_calculation(req_img_w, req_img_h, w, h, cropped_img_path):
    resize_flag = True
    if req_img_h > 0 and req_img_w > 0:
        if req_img_w >= w and req_img_h >= h:
            new_w = w
            new_h = h
        elif req_img_w >= w:
            new_h = req_img_h
            new_w = (new_h * w)/h
        elif req_img_h >= h:
            new_w = req_img_w
            new_h = (new_w * h)/w
        elif req_img_w < w and req_img_h < h:
            new_w = req_img_w
            new_h = (new_w * h)/w
        else:
            resize_flag = False
    #only width is given 
    elif req_img_h < 0 and req_img_w > 0:
        if req_img_w < w: #resizing required
            new_w = req_img_w
            new_h = (new_w * h)/w
        else:
            resize_flag = False
    #only height is given
    elif req_img_w < 0 and req_img_h > 0:
        if req_img_h < h: #resizing required
            new_h = resp_img_h
            new_w = (new_h * w)/h
        else:
            resize_flag = False
    else:
        resize_flag = False
    if resize_flag:
        return (True, new_w, new_h)
    else:
        return (False, None, None)


class ImageRender(View):
    def get(self, request, req_img_path):
        #TODO: catch type conversion errors
        print "Debug log: image render view"
        # store request data 
        req_img_w = int(request.GET.get('w', '-1'))
        req_img_h = int(request.GET.get('h', '-1'))
        req_img_priority = request.GET.get('priority', 'w')
        req_img_border_pc = request.GET.get('pad', None)
        print "Debug log: image size requested : %sx%s, Image Priority : %s,\
                Image border Color %s, req_img_path : %s" % \
                (req_img_w, req_img_h, req_img_priority, req_img_border_pc, req_img_path)

        #req_directory = os.path.join(settings.BASE_DIR, "static", "images")
        #req_img_name = os.path.basename(req_img_path)
        req_directory = os.path.join(settings.MEDIA_ROOT, os.path.dirname(req_img_path))
        req_img_name = os.path.basename(req_img_path)
        
        # create img path dict
        img_path_dict = create_img_paths(req_directory, req_img_name)
 
        #choose image file path
        resp_img_path = get_image_path(img_path_dict, req_img_priority)

        #pixel calculation
        img_path_dict['c_img'] = os.path.join(req_directory, 'resized', \
                   os.path.splitext(req_img_name)[0]+'_%sx%s' % (req_img_w, req_img_h)+ os.path.splitext(req_img_name)[1])
        if os.path.exists(img_path_dict['c_img']):
            resp_img_path = img_path_dict['c_img']
            resize_flag = False
        else:
            #resizing required
            im = Image.open(resp_img_path)
            w,h = im.size
            resize_flag, new_w, new_h = pixel_calculation(req_img_w, req_img_h, w, h, img_path_dict['c_img'])

        print "Debug Log : Response Image path: %s" % resp_img_path
        if resize_flag:
            print "Debug Log : Resizing required, new_w X new_h %sx%s" % (new_w, new_h)
            img = Image.open(resp_img_path)
            processor = Resize(new_w, new_h)
            m_img = processor.process(img)
            #update path to render
            resp_img_path = img_path_dict['c_img']

            if not os.path.exists(os.path.join(req_directory, "resized")):
                os.makedirs(os.path.join(req_directory, "resized"))
            if req_img_border_pc is not None:
                border_w = (req_img_w - new_w)/2
                border_h = (req_img_h - new_h)/2
                print "Debug Log: border_w X border_h %sx%s" % (border_w, border_h)
                ImageOps.expand(m_img, border=(border_w, border_h), fill=req_img_border_pc).save(resp_img_path, quality=95)
            else:
                m_img.save(resp_img_path, quality=95)

        relative_path = os.path.relpath(resp_img_path, settings.MEDIA_ROOT)
        #context_dict = {'relative_path':relative_path}
        #return render_to_response('images/image_render.html', context_dict, RequestContext(request))
        print "Debug Log: relative path: %s" % relative_path
        img = Image.open(resp_img_path)
        response = HttpResponse(content_type="image/jpeg")
        img.save(response, "jpeg")
        return response
