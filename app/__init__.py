
import atexit
import logging
from logging.config import dictConfig
import os

from flask import Flask
from flask.logging import default_handler

from .MCRconLib import MCRcon

####################
# Flask extensions #
####################


class ApplicationLogFilter(logging.Filter):
    def __init__(self, param=None):
        # TODO: What is param? (noshow as of now)
        self.param = param

    def filter(self, record):
        allow = True
        # Filter out werkzeug
        if record.name == 'werkzeug':
            allow = False
        return allow

class MCR():
    def __init__(self, _mcr):
        self._mcr = _mcr

    # This is a terrible workaround. Sometimes mcr doesn't return a value
    # we're expecting in testing, it returns nothing. I don't know if this is
    # a failing of our fake_server or what, but running a couple times until
    # we get a response seems to fix things for now.
    def command(self, command):
        for _ in range(0,3):
            response = self._mcr.command(command)
            if len(response) > 0: break
        return response


def create_app(alias=None, instance_path=None):
    '''The main function with which our flask app is created.

    Arguments:
    alias
        Used to load well-named config files (e.g. my_service.conf,
        my_service-dev.conf, my_service-testing.conf). If not provided, this
        value is set to os.path.basename(os.getcwd()), the projects package
        directory, which should be appropriately named.
    instance_path
        The instance path is where config files and other read/write data
        should go. This defaults to ./instance in the project's package when
        run locally using "flask run" (regardless of profile: dev, production,
        or testing). When deployed, the default appears to be [relative to
        the package] ../var/alias-instance when considering $PREFIX. I'm
        not sure how $PREFIX is set, but you can try and read about "instance
        folders" in the Flask documentation. Set this in the wsgi to a
        convenient location (e.g. /opt/var/alias).
        Anyway! This is basically mandatory because the default sucks.
    '''

    # Initial setup & app creation
    # ----------------------------
    # Configure the application logger
    format_string = ('%(levelname)s [%(asctime)s] '
                     '%(name)s.%(module)s.%(funcName)s(): %(message)s')
    dictConfig({
        'version': 1,
        'formatters': {
            'default': {
                # Brief vs precise formatters are below (one is commented out).
                # Brief is way cleaner to read in most cases. Precise
                #   pinpoints the logger.module.function() but is wide & ugly.
                'format': format_string,
                # 'format': '[%(asctime)s]: %(message)s'
            },
        },
        'filters': {
            'application_log_filter': {
                '()': ApplicationLogFilter,
                'param': 'noshow',
            },
        },
        'handlers': {
            # real file handler is programatically added below
            'file': {
                'class': 'logging.NullHandler',
            },
            'stream': {
                'class': 'logging.StreamHandler',
                'formatter': 'default',
            },
        },
        'root': {
            'level': 'INFO',
            'handlers': ['file']
        },
    })

    # Create the app
    app = _app_base(alias, instance_path)

    # Configure log handling
    # ----------------------
    # modify werkzeug so development log output goes to console
    if app.debug:
        # add the default [stream] handler so application logs go to stdout
        app.logger.addHandler(default_handler)
        # also add to werkzeug so werkzeug [request] output goes to stdout
        logging.getLogger('werkzeug').addHandler(default_handler)
        logging.getLogger('werkzeug').disabled = False

    # create the file handler; location comes from config or we set a default
    log_file = app.config.get(
        'LOG_FILE',
        os.path.join(os.getcwd(), 'application.log')
    )
    fh = logging.FileHandler(log_file)
    formatter = logging.Formatter(format_string)
    fh.setFormatter(formatter)
    fh.addFilter(ApplicationLogFilter())
    logging.getLogger('root').addHandler(fh)

    # set DEBUG loglevel on any loggers by looking at config values
    # TODO, I think this must be placed after registering blueprints?
    #   Otherwise how am I going to set a logger that doesn't yet exist?
    loggers = [
        logger.lower()[6:]
        for logger, value in app.config.items()
        if logger.startswith('DEBUG_') is True and value is True
    ]
    for logger in loggers:
        logging.getLogger(logger).setLevel(logging.DEBUG)

    # set loglevel DEBUG on the root/app logger
    app.logger.setLevel(logging.INFO)
    if app.config.get('ROOT_LOG_LEVEL_DEBUG', None):
        app.logger.setLevel(logging.DEBUG)

    # #########################################################################
    # Just about all modifications to the template should go here

    # Initialize extensions

    # Connect to the RCON server
    # TODO: Add ability for app to reconnect if disconnected
    if len(app.config.get('RCON_SERVER', None)) == 0:
        app._startup_failures.append('No RCON server set in the config file')
    else:
        app._mcr = MCRcon(
            host=app.config['RCON_SERVER'],
            password=app.config['RCON_PASSWD'],
            port=app.config['RCON_PORT']
        )
    try:
        app._mcr.connect()
        app._startup_messages.append((
                f'Connected to RCON server at '
                f"{app.config['RCON_SERVER']}:{app.config['RCON_PORT']}"))
    except Exception as e:
        app._startup_failures.append(
            'Could not connect to RCON server; see log for additional details')
        app.logger.error((
                f'Connection failure to Minecraft RCON server '
                f"{app.config['RCON_SERVER']}:{app.config['RCON_PORT']}:\n{e}"))

    app.mcr = MCR(app._mcr)

    # When the app is closing, close all connections
    def _app_cleanup():
        app.logger.info(f'App "{app.alias}" shutting down')
        app.logger.info('Disconnecting from RCON server')
        app._mcr.disconnect()

    atexit.register(_app_cleanup)
    # Register blueprints
    # -------------------
    from .main import main
    app.register_blueprint(main, url_prefix='/')

    from .cmd import cmd
    app.register_blueprint(cmd, url_prefix='/cmd/')

    # Helpful log output before return
    # --------------------------------
    # list all loggers (helps to identify other log levels you can set)
    loggers = [
        str(logging.getLogger(name))
        for name in logging.root.manager.loggerDict
    ]
    logger_list = '\n * '.join(loggers)
    app.logger.debug(
        '\nList of loggers available:'
        f'{logger_list}'
    )

    if app._startup_failures:
        @app.before_request
        def no_config_file():
            # A template might be nice
            html = f'<h3>{app.alias} unmet requirements:</h3></ br><ul>'
            for message in app._startup_failures:
                html += f'<li>{message}</li>'
            html += '</ul>'
            return (
                html,
                200
            )

    for startup_message in app._startup_messages:
        app.logger.info(startup_message)
    app.logger.info(f'App "{app.alias}" started with profile "{app.profile}"')
    del app._startup_messages

    return app


def _app_base(alias=None, instance_path=None):
    """Returns a basic flask app, ready to initialize (or as a fake)."""

    if alias is None:
        alias = os.path.basename(os.getcwd())

    # Create the app
    app = Flask(
        __name__.split('.')[0],
        instance_relative_config=True,
        instance_path=instance_path)
    app.alias = alias

    # Startup messages are logged; failures are rendered to web clients
    app._startup_messages = list()
    app._startup_failures = list()

    # Set the profile to load additional config
    if app.debug:
        app.profile = 'development'
    elif os.environ.get('FLASK_TESTING', None):
        app.profile = 'testing'
    else:
        app.profile = 'production'

    default_config = f'{alias}.conf'
    config_files = {
        'production': default_config,
        'development': f'{alias}-dev.conf',
        'testing': f'{alias}-testing.conf'
    }
    config_file = config_files.get(app.profile, default_config)

    app.config.from_object("app.default_settings")
    try:
        app.config.from_pyfile(config_file)
    except Exception:
        app._startup_failures.append(
            f'Config file not found: '
            f'{os.path.join(app.instance_path, config_file)}')
        # If no config file exists, intercept all requests and issue a warning

    if not os.path.exists(os.path.join(app.instance_path, config_file)):
        app._startup_messages.append(
            f'No config file ({config_file}) found'
        )

    # Note: As much as I like the idea of using class inheritance with
    #   from_object to load profile-specific configs, I just find using
    #   the instance folder a better way to corral things.

    return app


def fake_app(alias=None, instance_path=None):
    """Return an application base for config value access only."""
    return _app_base(alias, instance_path)
