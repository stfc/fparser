class ParserFactory(object):
    ''' '''
    def create(self, std=None):
        ''' '''
        if not std:
            std = "f2003"
        if std == "f2003":
            from fparser.two import Fortran2003
            classes = dir(Fortran2003)
            base = Fortran2003.Base
            self.setup(classes, base)
            return Fortran2003.Program
        elif std == "f2008":
            from fparser.two import Fortran2008
            classes = dir(Fortran2008)
            from fparser.two import Fortran2003
            classes.extend(dir(Fortran2003))
            base = Fortran2003.Base
            self.setup(classes, base)
            return Fortran2003.Program
        else:
            print "unsupported standard {0}".format(api)
            exit(1)
    def setup(self, classes, base):
        ''' '''
        return

__autodoc__ = []
Base_classes = {}

import logging
import fparser.two.Fortran2003
CLASSES = dir(fparser.two.Fortran2003)
ClassType = type(fparser.two.Fortran2003.Base)

for clsname in CLASSES:
    cls = eval("fparser.two.Fortran2003."+clsname)
    # ?? classtype is set to Base so why have issubclass?
    if isinstance(cls, ClassType) and issubclass(cls, fparser.two.Fortran2003.Base) \
       and not cls.__name__.endswith('Base'):
        Base_classes[cls.__name__] = cls
        if len(__autodoc__) < 10:
            __autodoc__.append(cls.__name__)

#
# OPTIMIZE subclass_names tree
#

if 1:  # Optimize subclass tree:

    def _rpl_list(clsname):
        if clsname not in Base_classes:
            logging.getLogger(__name__).debug('Not implemented: %s' % clsname)
            return []  # remove this code when all classes are implemented
        cls = Base_classes[clsname]
        if 'match' in cls.__dict__:
            return [clsname]
        bits = []
        for n in getattr(cls, 'subclass_names', []):
            l1 = _rpl_list(n)
            for n1 in l1:
                if n1 not in bits:
                    bits.append(n1)
        return bits

    for cls in list(Base_classes.values()):
        if not hasattr(cls, 'subclass_names'):
            continue
        opt_subclass_names = []
        for n in cls.subclass_names:
            for n1 in _rpl_list(n):
                if n1 not in opt_subclass_names:
                    opt_subclass_names.append(n1)
        if not opt_subclass_names == cls.subclass_names:
            cls.subclass_names[:] = opt_subclass_names


# Initialize Base.subclasses dictionary:
for clsname, cls in list(Base_classes.items()):
    subclass_names = getattr(cls, 'subclass_names', None)
    if subclass_names is None:
        message = '%s class is missing subclass_names list' % (clsname)
        logging.getLogger(__name__).debug(message)
        continue
    try:
        bits = fparser.two.Fortran2003.Base.subclasses[clsname]
    except KeyError:
        fparser.two.Fortran2003.Base.subclasses[clsname] = bits = []
    for n in subclass_names:
        if n in Base_classes:
            bits.append(Base_classes[n])
        else:
            message = '%s not implemented needed by %s' % (n, clsname)
            logging.getLogger(__name__).debug(message)

if 1:
    for cls in list(Base_classes.values()):
        subclasses = fparser.two.Fortran2003.Base.subclasses.get(cls.__name__, [])
        subclasses_names = [c.__name__ for c in subclasses]
        subclass_names = getattr(cls, 'subclass_names', [])
        use_names = getattr(cls, 'use_names', [])
        for n in subclasses_names:
            break
            if n not in subclass_names:
                message = '%s needs to be added to %s subclasses_name list' \
                          % (n, cls.__name__)
                logging.getLogger(__name__).debug(message)
        for n in subclass_names:
            break
            if n not in subclasses_names:
                message = '%s needs to be added to %s subclass_name list' \
                          % (n, cls.__name__)
                logging.getLogger(__name__).debug(message)
        for n in use_names + subclass_names:
            if n not in Base_classes:
                message = '%s not defined used by %s' % (n, cls.__name__)
                logging.getLogger(__name__).debug(message)