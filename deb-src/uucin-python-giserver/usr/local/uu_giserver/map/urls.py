from django.conf.urls import patterns, url


urlpatterns = patterns(
    '',
    url(r'^(?P<version>\w+)/grid/(?P<scale>[0-9]+)/(?P<x>[0-9-]+)/(?P<y>[0-9-]+)/(?P<index>[0-9-]+).png', "map.views.send_grid_file"),
    url(r'^(?P<version>\w+)/text/(?P<scale>[0-9]+)/(?P<x>[0-9-]+)/(?P<y>[0-9-]+)/(?P<index>[0-9-]+).(js|json|jsonp)', "map.views.send_text_file"),
)
