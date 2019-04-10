from .base import Daemon
from .utils import ConfigDict, template_lookup


class OpenrDaemon(Daemon):
    """The base class for the OpenR daemon"""

    NAME = 'openr'

    @property
    def STARTUP_LINE_EXTRA(self):
        # Add options to the standard startup line
        return ''

    @property
    def startup_line(self):
        return '{name} {cfg} {extra}'\
                .format(name=self.NAME,
                        cfg=self._cfg_options(),
                        extra=self.STARTUP_LINE_EXTRA)

    def build(self):
        cfg = super(OpenrDaemon, self).build()
        cfg.debug = self.options.debug
        return cfg

    def set_defaults(self, defaults):
        """:param debug: the set of debug events that should be logged"""
        defaults.debug = ()
        super(OpenrDaemon, self).set_defaults(defaults)

    def _cfg_options(self):
        """The OpenR daemon has currently no option to read config from
        configuration file itself. The run_openr.sh script can be used to read
        options from environment files. However, we want to run the daemon
        directly.  The default options from the shell script are implemented in
        the openr.mako template and passed to the daemon as argument."""
        cfg = ConfigDict()
        cfg[self.NAME] = self.build()
        return template_lookup.get_template(self.template_filename)\
                              .render(node=cfg)

    @property
    def dry_run(self):
        """The OpenR dryrun runs the daemon and does not shutdown the daemon.
        As a workaround we only show the version of the openr daemon"""
        # TODO: Replace with a config parser or shutdown the daemon after few
        # seconds
        return '{name} --version'\
               .format(name=self.NAME)
