from .base import RouterDaemon

class Pimd(RouterDaemon):
    """ This class configure the pim Daemon which can be found here:
        https://github.com/troglobit/pimd
    """
    NAME = 'pimd'
    KILL_PATTERNS = (NAME,)

    def __init__(self,node,*args,**kwargs):
        super().__init__(node=node,*args,**kwargs)
        # add some custom attr
        if "cfg" in kwargs:
            self.custom_config = kwargs["cfg"]
        if "log_file" in kwargs: 
            self.logfile = kwargs["log_file"]


    @property
    def startup_line(self):
        if hasattr(self,'custom_config'):
            return '{name} -f --config={cfg}'.format(name=self.NAME,cfg=self.custom_config)
        else:
            return '{name} -f --config={cfg}'.format(name=self.NAME,cfg=self.cfg_filename)

    @property
    def dry_run(self):
        return 'echo 2BeOrNot2Be > /dev/null'

    def set_defaults(self,defaults):
        super().set_defaults(defaults)

    def build(self):
        cfg = super().build()
        return cfg
