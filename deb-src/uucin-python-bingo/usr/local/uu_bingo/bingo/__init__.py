from pyramid.config import Configurator
from bingo import database


def api_include(config):
    config.add_route('group_poi', '/group/poi')
    config.add_route('write_poi', '/write/poi')
    config.add_route('search_poi', '/search/poi')


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    config.include(api_include, route_prefix='/api')
    database.configure(settings)
    config.scan()
    return config.make_wsgi_app()
