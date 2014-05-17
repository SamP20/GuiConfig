import wx
import os

import vstore
    
class Func(object):
    def __init__(self, vars, fn):
        self.vars = vars
        self.fn = fn

    def get_dependencies(self):
        return self.vars

    def __call__(self, dict):
        return self.fn(*[dict[x] for x in self.vars])


class Attribute(object):
    def __init__(self, value):
        self._var = value
        self.handlers = []
        try:
            for dep in self._var.get_dependencies():
                vstore.instance.add_binding(dep, self._change_handler)
        except AttributeError:
            pass
            
    def add_handler(self, handler, call=False):
        self.handlers.append(handler)
        if call:
            handler(self.value)

    def _change_handler(self, key, value):
        for handler in self.handlers:
            handler(self.value)

    @property
    def value(self):
        try:
            return self._var(vstore.instance)
        except TypeError:
            return self._var


class GenericPart(object):
    def __init__(self):
        self.children = []
        self.parent = None

    def add_children(self, *args):
        for child in args:
            self.add_child(child)
        return self

    def add_child(self, child):
        child.parent = self
        self.children.append(child)
        return self

    def build_gui(self, parent):
        pass

    def refresh(self, recursive=True):
        if recursive:
            for child in self.children:
                child.refresh()
                
    def layout(self):
        if self.parent:
            self.parent.layout()


class Notebook(GenericPart):
    def __init__(self):
        GenericPart.__init__(self)

    def build_gui(self, parent_ctrl):
        self._control = wx.Notebook(parent_ctrl)
        page_count = 0
        
        #Load child controls
        for child in self.children:           
            self._control.AddPage(child.build_gui(self._control), child.title.value)
            child.title.add_handler(lambda val: self._control.SetPageText(page_count, value))
            page_count += 1

        return self._control
        
    def layout(self):
        self._control.Layout()
        for child in self.children:
            child.layout()
            

class Tab(GenericPart):
    def __init__(self, title):
        GenericPart.__init__(self)
        self.title = Attribute(title)

    def build_gui(self, parent_ctrl):
        self._control = wx.Panel(parent_ctrl)
        self._sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._sizer.SetSizeHints(self._control)
        self._control.SetSizer(self._sizer)
        left_col_width = 150
        self._treectrl = wx.TreeCtrl(self._control, -1, wx.DefaultPosition, (150, -1),
                                    wx.TR_NO_BUTTONS | wx.TR_HIDE_ROOT | wx.TR_SINGLE |
                                    wx.TR_NO_LINES | wx.BORDER_SUNKEN | wx.WANTS_CHARS)
        self._sizer.Add(self._treectrl, 0, wx.EXPAND | wx.LEFT | wx.TOP | wx.BOTTOM, 3)
        self._imagelist = wx.ImageList(16, 16, 1)
        self._icons = []
        self._treectrl.AssignImageList(self._imagelist)
        self._iconcount = -1
        self._treectrl.AddRoot("root")
        self._treectrl.SetIndent(0)
        self._control.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_sel_changed, self._treectrl)

        #Load child controls
        for child in self.children:
            control = child.build_gui(self._control)
            self._sizer.Add(control, 1, wx.EXPAND | wx.ALL, 5)
            control.Hide()
            iconIndex = -1
            try:
                iconName = child.icon.value
                try:
                    iconIndex = self._icons.index(iconName)
                except:
                    self._imagelist.Add(wx.Bitmap(os.path.join(os.path.dirname(__file__), "icons", iconName), wx.BITMAP_TYPE_PNG))
                    self._icons.append(iconName)
                    iconIndex = len(self._icons)-1
            except:
                pass
            root = self._treectrl.GetRootItem()
            treeData = wx.TreeItemData(control)
            item = self._treectrl.AppendItem(root, child.title.value, iconIndex, iconIndex, treeData)
            child.title.add_handler(lambda val: self._treectrl.SetItemText(item, val))
        return self._control

    def on_sel_changed(self, event):
        root = self._treectrl.GetRootItem()
        (child, cookie) = self._treectrl.GetFirstChild(root)
        while child.IsOk():
            control = self._treectrl.GetPyData(child)
            if child == event.GetItem():
                control.Show()
            else:
                control.Hide()
            (child, cookie) = self._treectrl.GetNextChild(root, cookie)
        self.layout()
        
    def layout(self):
        self._control.Layout()
        for child in self.children:
            child.layout()

            
class Page(GenericPart):
    def __init__(self, title, icon="cog.png"):
        GenericPart.__init__(self)
        self.title = Attribute(title)
        self.icon = Attribute(icon) #TODO: Icon change handler

    def build_gui(self, parent_ctrl):
        self._control = wx.ScrolledWindow(parent_ctrl, style=wx.TAB_TRAVERSAL)
        self._control.SetScrollbars(1, 1, 1, 1)
        self._vsizer = wx.BoxSizer(wx.VERTICAL)
        self._control.SetSizer(self._vsizer)

        #Load child controls
        for child in self.children:
            self._vsizer.Add(child.build_gui(self._control), 0, wx.EXPAND | wx.ALL, 5)
            
        return self._control
        
    def refresh(self):
        GenericPart.refresh(self)

    def layout(self):
        self._control.Layout()
  
  
class OptionsGroup(GenericPart):
    def __init__(self, title, visible=True):
        GenericPart.__init__(self)
        self.title = Attribute(title)
        self.visible = Attribute(visible)

    def build_gui(self, parent_ctrl):
        self._control = wx.StaticBox(parent_ctrl, label=self.title.value)
        self._sizer = wx.StaticBoxSizer(self._control, wx.VERTICAL)
        self._control.Show(self.visible.value)
        
        #Load child controls
        for child in self.children:
            self._sizer.Add(child.build_gui(self._control), 0, wx.EXPAND | wx.ALL, 0)
        
        #Attribute change handlers
        self.title.add_handler(self._control.SetLabel)
        self.visible.add_handler(self._show)
        return self._sizer
    
    def _show(self, val):
        self._control.Show(val)
        self.layout()


class TextInput(GenericPart):
    def __init__(self, title, name, label="", tooltip=None):
        GenericPart.__init__(self)
        self.title = Attribute(title)
        self.name = Attribute(name)
        self.label = Attribute(label)
        self.tooltip = Attribute(tooltip)

    def build_gui(self, parent_ctrl):
        self._title = wx.StaticText(parent_ctrl, label=self.title.value, size=(180, -1))
        self._input = wx.TextCtrl(parent_ctrl, style=wx.TE_PROCESS_ENTER)
        self._label = wx.StaticText(parent_ctrl, label=self.label.value)
        self._sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._sizer.Add(self._title, flag=wx.LEFT)
        self._sizer.Add(self._input, flag=wx.LEFT)
        self._sizer.Add(self._label, flag=wx.LEFT)

        #Attribute change handlers
        self.title.add_handler(self._title.SetLabel)
        self.name.add_handler(self.refresh, True)
        self.tooltip.add_handler(lambda val:
                                 self._input.SetToolTip(wx.ToolTip(val) if val else None), True)

        self._input.Bind(wx.EVT_TEXT, self.on_value_changed)
        return self._sizer

    def on_value_changed(self, event):
        vstore.instance.setr(self.name.value, self._input.GetValue())

    def refresh(self, val=None):
        try:
            if val is None: val = self.name.value
            self._input.ChangeValue(vstore.instance.getr(val))
        except KeyError:
            pass


class IntegerInput(GenericPart):
    def __init__(self, title, name, label="", min=0, max=100, tooltip=None):
        GenericPart.__init__(self)
        self.title = Attribute(title)
        self.min = Attribute(min)
        self.max = Attribute(max)
        self.name = Attribute(name)
        self.label = Attribute(label)
        self.tooltip = Attribute(tooltip)

    def build_gui(self, parent_ctrl):
        #TODO: Load default value
        self._title = wx.StaticText(parent_ctrl, label=self.title.value,
                                    size=(180, -1))
        self._input = wx.SpinCtrl(parent_ctrl, style=wx.TE_PROCESS_ENTER,
                                  min=self.min.value, max=self.max.value)
        self._label = wx.StaticText(parent_ctrl, label=self.label.value)
        self._sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._sizer.Add(self._title, flag=wx.LEFT)
        self._sizer.Add(self._input, flag=wx.LEFT)
        self._sizer.Add(self._label, flag=wx.LEFT)

        #Attribute change handlers
        self.title.add_handler(self._title.SetLabel)
        self.min.add_handler(self._min_change_handler)
        self.max.add_handler(self._max_change_handler)
        self.name.add_handler(self.refresh, True)
        self.tooltip.add_handler(lambda val:
                                 self._input.SetToolTip(wx.ToolTip(val) if val else None), True)

        self._input.Bind(wx.EVT_SPINCTRL, self.on_value_changed)
        return self._sizer

    def _max_change_handler(self, val):
        self._input.SetRange(self._input.Min, val)
        self.on_value_changed(None)

    def _min_change_handler(self, val):
        self._input.SetRange(val, self._input.Max)
        self.on_value_changed(None)

    def on_value_changed(self, event):
        vstore.instance.setr(self.name.value, self._input.GetValue())

    def refresh(self, val=None):
        try:
            if val is None: val = self.name.value
            self._input.SetValue(vstore.instance.getr(val))
        except KeyError:
            pass


class RealInput(GenericPart):
    def __init__(self, title, name, label="", min=0.0, max=100.0, tooltip=None):
        GenericPart.__init__(self)
        self.title = Attribute(title)
        self.min = Attribute(min)
        self.max = Attribute(max)
        self.name = Attribute(name)
        self.label = Attribute(label)
        self.tooltip = Attribute(tooltip)

    def build_gui(self, parent_ctrl):
        self._title = wx.StaticText(parent_ctrl, label=self.title.value,
                                    size=(180, -1))
        self._input = wx.SpinCtrlDouble(parent_ctrl, style=wx.TE_PROCESS_ENTER,
                                  min=int(self.min.value), max=int(self.max.value))
        self._input.SetDigits(2)
        self._label = wx.StaticText(parent_ctrl, label=self.label.value)
        self._sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._sizer.Add(self._title, flag=wx.LEFT)
        self._sizer.Add(self._input, flag=wx.LEFT)
        self._sizer.Add(self._label, flag=wx.LEFT)

        #Attribute change handlers
        self.title.add_handler(self._title.SetLabel)
        self.min.add_handler(self._min_change_handler)
        self.max.add_handler(self._max_change_handler)
        self.name.add_handler(self.refresh, True)
        self.tooltip.add_handler(lambda val:
                                 self._input.SetToolTip(wx.ToolTip(val) if val else None), True)

        self._input.Bind(wx.EVT_SPINCTRL, self.on_value_changed)
        self.on_value_changed(None) #Set initial defaults
        return self._sizer

    def _max_change_handler(self, val):
        self._input.SetRange(self._input.Min, float(val))
        self.on_value_changed(None)

    def _min_change_handler(self, val):
        self._input.SetRange(float(val), self._input.Max)
        self.on_value_changed(None)

    def on_value_changed(self, event):
        vstore.instance.setr(self.name.value, self._input.GetValue())

    def refresh(self, val=None):
        try:
            if val is None: val = self.name.value
            self._input.SetValue(vstore.instance.getr(val))
        except KeyError:
            pass


class ChoiceInput(GenericPart):
    def __init__(self, title, name, label="", options=[], tooltip=None):
        GenericPart.__init__(self)
        self.title = Attribute(title)
        self.name = Attribute(name)
        self.label = Attribute(label)
        self.options = Attribute(options)
        self.tooltip = Attribute(tooltip)        

    def build_gui(self, parent_ctrl):
        self._title = wx.StaticText(parent_ctrl, label=self.title.value,
                                    size=(180, -1))
        self._input = wx.ListBox(parent_ctrl, style=wx.LB_SINGLE)
        self._label = wx.StaticText(parent_ctrl, label=self.label.value)
        self._sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._sizer.Add(self._title, flag=wx.LEFT)
        self._sizer.Add(self._input, flag=wx.LEFT)
        self._sizer.Add(self._label, flag=wx.LEFT)

        #Attribute change handlers
        self.title.add_handler(self._title.SetLabel)
        self.options.add_handler(self._set_options, True) #This needs to be first to initialize the optionids
        self.name.add_handler(self.refresh, True)
        self.tooltip.add_handler(lambda val:
                                 self._input.SetToolTip(wx.ToolTip(val) if val else None), True)

        self._input.Bind(wx.EVT_LISTBOX, self.on_value_changed)
        return self._sizer

    def _set_options(self, options):
        self._input.Clear()
        self._optionids = [obj[0] for obj in options]
        self._input.InsertItems([obj[1] for obj in options], pos=0)

    def on_value_changed(self, event):
        vstore.instance.setr(self.name.value, self._optionids[self._input.GetSelection()])

    def refresh(self, val=None):
        try:
            if val is None: val = self.name.value
            self._input.SetSelection(self._optionids.index(vstore.instance.getr(val)))
        except KeyError:
            pass
            

class CheckInput(GenericPart):
    def __init__(self, title, name, label="", tooltip=None):
        GenericPart.__init__(self)
        self.title = Attribute(title)
        self.name = Attribute(name)
        self.label = Attribute(label)
        self.tooltip = Attribute(tooltip)

    def build_gui(self, parent_ctrl):
        self._title = wx.StaticText(parent_ctrl, label=self.title.value, size=(180, -1))
        self._input = wx.CheckBox(parent_ctrl, label=self.label.value)
        self._sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._sizer.Add(self._title, flag=wx.LEFT)
        self._sizer.Add(self._input, flag=wx.LEFT)

        #Attribute change handlers
        self.title.add_handler(self._title.SetLabel)
        self.name.add_handler(self.refresh, True)
        self.tooltip.add_handler(lambda val:
                                 self._input.SetToolTip(wx.ToolTip(val) if val else None), True)

        self._input.Bind(wx.EVT_CHECKBOX, self.on_value_changed)
        return self._sizer

    def on_value_changed(self, event):
        vstore.instance.setr(self.name.value, self._input.GetValue())

    def refresh(self, val=None):
        try:
            if val is None: val = self.name.value
            self._input.SetValue(vstore.instance.getr(val))
        except KeyError:
            pass