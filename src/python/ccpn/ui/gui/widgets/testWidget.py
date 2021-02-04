
if False:
    """
    Use this to test new widgets in a popup. 
    """
    if __name__ == '__main__':
        from ccpn.ui.gui.widgets.Application import TestApplication
        from ccpn.ui.gui.popups.Dialog import CcpnDialog
        from ccpn.ui.gui.widgets.Widget import Widget


        app = TestApplication()

        texts = ['Int', 'Float', 'String', '']
        objects = [int, float, str, 'Green']



        popup = CcpnDialog(windowTitle='Test widget', setLayout=True)
        widget = Widget(parent=popup, grid=(0,0))

        popup.show()
        popup.raise_()
        app.start()



