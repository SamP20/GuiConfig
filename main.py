import wx
#import wx.lib.inspection
import os
import importlib.machinery
import json
from templite import Templite

import vstore


outputs = {}
open_dir = os.path.join(os.path.dirname(__file__),"templates")
load_save_dir = os.path.expanduser("~")
export_dir = os.path.expanduser("~")


def load_module(path):
    loader = importlib.machinery.SourceFileLoader("module.name", path)
    return loader.load_module()


class MainFrame(wx.Frame):
    
    def __init__(self):
        wx.Frame.__init__(self, None, title="PyConfig", size=(760, 470))      
        self.SetMenuBar(self.create_menu_bar())
        
        self.panel = wx.Panel(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.sizer)
        self.SetMinSize(self.GetSize())
        self.parent = None
        

    def create_menu_bar(self):
        menuBar = wx.MenuBar()
        fileMenu = wx.Menu()
        m_open = fileMenu.Append(wx.ID_OPEN, "&Open Template", "Open template file")
        self.Bind(wx.EVT_MENU, self.on_open, m_open)
        
        self.m_load = fileMenu.Append(wx.ID_ANY, "&Load settings", "Load configuration settings")
        self.m_load.Enable(False)
        self.Bind(wx.EVT_MENU, self.on_load, self.m_load)
        
        self.m_save = fileMenu.Append(wx.ID_SAVE, "&Save settings", "Save configuration settings")
        self.m_save.Enable(False)
        self.Bind(wx.EVT_MENU, self.on_save, self.m_save)
        
        self.m_export = fileMenu.Append(wx.ID_ANY, "&Export config", "Export configuration files")
        self.m_export.Enable(False)
        self.Bind(wx.EVT_MENU, self.on_export, self.m_export)
        
        m_exit = fileMenu.Append(wx.ID_EXIT, "E&xit\tAlt-X", "Close window and exit program.")
        self.Bind(wx.EVT_MENU, self.on_close, m_exit)
        
        menuBar.Append(fileMenu, "&File")
        return menuBar
        
    def on_open(self, event):
        global open_dir
        wildcard = "Py files (*.py)|*.py|" \
           "All files (*.*)|*.*"
        dlg = wx.FileDialog(
            self, message="Choose a file",
            defaultDir=open_dir, 
            defaultFile="",
            wildcard=wildcard,
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
            )
        
        if dlg.ShowModal() == wx.ID_OK:
            open_dir = os.path.dirname(dlg.GetPath())
            module = load_module(dlg.GetPath())
            vstore.instance.clear()
            vstore.instance.update(module.load_defaults())
            self.gui = module.load_gui()
            self.sizer.Clear(True)
            self.sizer.Add(self.gui.build_gui(self.panel), 1, wx.ALL|wx.EXPAND, 5)
            self.sizer.Layout()
            self.gui.layout()
            outputs = module.load_outputs()
            self.m_load.Enable(True)
            self.m_save.Enable(True)
            self.m_export.Enable(True)
        
    def on_load(self, event):
        global load_save_dir
        wildcard = "JSON files (*.json)|*.json|" \
           "All files (*.*)|*.*"
        dlg = wx.FileDialog(
            self, message="Choose a file",
            defaultDir=load_save_dir,
            defaultFile="",
            wildcard=wildcard,
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
            )
        
        if dlg.ShowModal() == wx.ID_OK:
            load_save_dir = os.path.dirname(dlg.GetPath())
            with open(dlg.GetPath(), "r") as fp:
                data = json.load(fp)
                vstore.instance.update(data)
                self.gui.refresh()
        
    def on_save(self, event):
        global load_save_dir
        wildcard = "JSON files (*.json)|*.json|" \
           "All files (*.*)|*.*"
        dlg = wx.FileDialog(
            self, message="Choose a file",
            defaultDir=load_save_dir,
            defaultFile="",
            wildcard=wildcard,
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
            )
        
        if dlg.ShowModal() == wx.ID_OK:
            load_save_dir = os.path.dirname(dlg.GetPath())
            with open(dlg.GetPath(), "w") as fp:
                json.dump(vstore.instance, fp)
        
    def on_export(self, event):
        global export_dir
        dlg = wx.DirDialog(
            self, message="Choose a directory",
            defaultPath=export_dir,
            style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST
            )
            
        if dlg.ShowModal() == wx.ID_OK:
            export_dir = dlg.GetPath()
            for output, contents in outputs.items():
                filename = os.path.join(export_dir, output)
                template = Templite(contents)
                with open(filename, "w") as fh:
                    fh.write(template.render(vstore.instance))
    
    def on_close(self, event):
        self.Destroy()
    
if __name__ == "__main__":
    app = wx.App()
    MainFrame().Show()
    #wx.lib.inspection.InspectionTool().Show()
    app.MainLoop()