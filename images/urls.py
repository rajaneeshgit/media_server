from django.conf.urls import url
from django.conf import settings

from . import views
from images.views import ImageRender
urlpatterns = [
    url(r'^(?P<req_img_path>.*)$', ImageRender.as_view(), name='image_render'),
]

