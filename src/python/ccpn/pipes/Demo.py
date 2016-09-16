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
             'value'    : ('Normal1', 'Weird1'),
             'label'    : 'Param #1',
             'default'  : 'Weird1'},                        # List

            {'variable' : 'param2',
             'value'    : False},                           # checkbox

            {'variable': 'param3',
             'value': ('0', '4')},                           # List

            {'variable' : 'param4',                         # Spinbox
             'value'    : (0, 4)},

            {'variable' : 'param5',                         # Spinbox with default
             'value'    : (0, 4),
             'default'  : 2},

            {'variable' : 'param6',                         # Spinbox with stepsize
             'value'    : (0, 4),
             'stepsize' : 2},

            {'variable' : 'param7',                         # Spinbox with default and stepsize
             'value'    : (0, 4),
             'stepsize' : 2,
             'default'  : 2},

            {'variable' : 'param8',                         # Double Spinbox
             'value'    : (0., 1)},

            {'variable' : 'param9',                         # Double Spinbox with default
             'value'    : (0., 1.),
             'default'  : 0.2},

            {'variable' : 'param10',                         # Double Spinbox with stepsize
             'value'    : (0., 1.),
             'stepsize' : 0.1},

            {'variable' : 'param11',                         # Double Spinbox with default and stepsize
             'value'    : (0., 1),
             'stepsize' : 0.1,
             'default'  : 0.2},

            {'variable': 'param12',                         # LineEdit
             'value': ''},

            {'variable': 'param13',
             'value': (('TJ', 'Ragan'),                    # Mapped list
                       ('Simon', 'Skinner'),
                       ('Rasmus', 'Fogh')
                      )},
            ]

  def run(self, dataframe, test=None, **params):
    print('', str(test), params)
    if dataframe:
      return dataframe + '* '
    return 'Dataframe '
