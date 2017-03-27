__author__ = 'TJ Ragan'

from ccpn.framework.lib.Pipe import PandasPipe

class DemoExtension(PandasPipe):
  '''
  Demo auto-generated gui for pipeline
  '''
  METHODNAME = 'Demo'

  from collections import OrderedDict
  # TODO: Expand dictionary spec
  params = [{'variable' : 'param1',
             'value'    : ('Fast', 'Slow'),
             'label'    : 'Param #1',
             'default'  : 'Fast'},                        # List

            {'variable' : 'param2',
             'value'    : False,
             'default'  : 0},                              # checkbox 0 unchecked 2 checked

            {'variable': 'param43',
             'value': (('White 1',False),('Red 2',True)),  #  RadioButtons
             'default': 'Red 2'},

            {'variable' : 'param3',
             'value'    : ('0', '4'),
             'default'  : 4},                                # List

            {'variable' : 'param4',                         # Spinbox
             'value'    : (0, 4),
             'default'  : (3)},

            {'variable' : 'param5',                         # Spinbox with default
             'value'    : (0, 4),
             'default'  : 2},

            {'variable' : 'param6',                         # Spinbox with stepsize
             'value'    : (0, 4),
             'stepsize' : 2,
             'default'  : 3},

            {'variable' : 'param7',                         # Spinbox with default and stepsize
             'value'    : (0, 4),
             'stepsize' : 2,
             'default'  : 2},

            {'variable' : 'param8',                         # Double Spinbox
             'value'    : (0., 1),
             'default'  : 0.3},

            {'variable' : 'param9',                         # Double Spinbox with default
             'value'    : (0., 1.),
             'default'  : 0.2},

            {'variable' : 'param10',                         # Double Spinbox with stepsize
             'value'    : (0., 1.),
             'stepsize' : 0.1,
             'default'  : 0.2},

            {'variable' : 'param11',                         # Double Spinbox with default and stepsize
             'value'    : (0., 1),
             'stepsize' : 0.1,
             'default'  : 0.2},

            {'variable': 'param12',                         # LineEdit
             'value': '',
             'default'  : 'param12'},

            {'variable': 'param13',
             'value': (('Ford', 'Focus'),                    # Mapped list
                       ('BMW', '320'),
                       ('Fiat', '500')
                      ),
             'default'  : 'Focus'},
            ]

  def run(self, dataframe, test=None, **params):
    print('', str(test), params)
    return dataframe
