
import logging
from logging.config import dictConfig
import os

from flask import Flask, request
from flask.logging import default_handler

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
    # modify werkzeug so development/testing log output goes to console
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
    loggers = [
        logger.lower()[6:]
        for logger, value in app.config.items()
        if logger.startswith('DEBUG_') and value == True
    ]
    for logger in loggers:
        logging.getLogger(logger).setLevel(logging.DEBUG)

    # set loglevel DEBUG on the root/app logger
    logging.getLogger('app').setLevel(logging.INFO)
    if app.config.get('ROOT_LOG_LEVEL_DEBUG', None):
        logging.getLogger('app').setLevel(logging.DEBUG)

    # #########################################################################
    # Just about all modifications to the template should go here

    # Initialize extensions
    # TODO: establish an rcon server connection here
    #   Later todo is to ensure reconnection is attempted if connection is
    #   failed and communicate a failed connection to the user.

    # Register blueprints
    # -------------------
    from .main import main
    app.register_blueprint(main, url_prefix='/')

    # Helpful log output before return
    # --------------------------------
    # list all loggers (helps to identify other log levels you can set)
    loggers = [str(logging.getLogger(name)) for name in logging.root.manager.loggerDict]
    app.logger.debug('\nList of loggers available:\n * ' + '\n * '.join(loggers))

    for startup_message in app.startup_messages:
        app.logger.info(startup_message)
    app.logger.info(f'App "{app.alias}" started with profile "{app.profile}"')
    del app.startup_messages

    return app

def _app_base(alias=None, instance_path=None):
    """Returns a basic flask app, ready to initialize (or as a fake)."""

    if alias is None:
        alias = os.path.basename(os.getcwd())

    # Create the app
    app = Flask(__name__.split('.')[0],
        instance_relative_config=True,
        instance_path=instance_path)
    app.alias = alias

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
    app.config.from_pyfile(config_file, True)

    app.startup_messages = list()
    if not os.path.exists(os.path.join(app.instance_path, config_file)):
        app.startup_messages.append(
            f'No config file ({config_file}) found'
        )

    # Note: As much as I like the idea of using class inheritance with
    #   from_object to load profile-specific configs, I just find using
    #   the instance folder a better way to corral things.

    return app

def fake_app(alias=None, instance_path=None):
    """Return an application base for config value access only."""
    return _app_base(alias, instance_path)