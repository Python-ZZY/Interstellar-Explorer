import epg
from .box import *

class Variable:
    def __init__(self, value=None):
        self._value = value
        self.widgets = []

    def __bool__(self):
        return bool(self._value)

    def bind(self, widget):
        self.widgets.append(widget)

    def set(self, value):
        self._value = value

        for w in self.widgets:
            w.update_widget()

    def get(self):
        return self._value

class BaseWidget(BaseUI):
    def update_display(self):
        self.box.update_display()

class Container(BaseWidget):
    def __init__(self, scene, *args, **kw):
        self.scene = scene
        self.box = BaseBox(*args, **kw)
        self.children = []

    def map(self, *args, **kw):
        epg.throw("cannot map the container")

    def unmap(self):
        epg.throw("cannot unmap the container")

    def events(self, event):
        for w in self.all_children:
            w.events(event)

    def update(self):
        for w in self.all_children:
            w.update()

    def draw(self, offset=None):
        for w in self.all_children:
            w.draw(self.scene.screen, offset=None)

class Widget(BaseWidget):
    STATES = ("normal", "hover", "active", "disabled")
    ATTR = {}

    def __init__(self, parent, state=STATES[0], inpad=0, outpad=0, **kw):
        self.parent = parent
        self.children = []

        self.kw = self.ATTR.copy()
        self.box = Box(parent=parent.box, size=(0, 0), inpad=inpad, outpad=outpad)
        self._state = None

        self.config(state=state, **kw)

    def __delitem__(self, key):
        del self.kw[key]

    def __getitem__(self, key):
        return self.kw[key]

    def __setitem__(self, key, value):
        self.kw[key] = value
        
    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        if value not in self.STATES:
            epg.throw("Incorrect state: " + str(value), "")

        _state = self._state
        self._state = value

        if _state != value:
            self.update_widget()

    @property
    def rect(self):
        return self.box.get_outer_rect()

    def config(self, state=None, **kw):
        epg.check_attr(kw, self.ATTR)
        self.kw.update(kw)

        self.box.resize(self.init())
        if state:
            self.state = state

    def init(self):
        raise NotImplementedError("Widget.init(self) -> (width, height)")

    def events(self, event):
        pass

    def update(self):
        pass

    def draw(self, screen, offset=None):
        raise NotImplementedError("Widget.draw(self, screen, offset=None) -> None")

    def update_widget(self):
        pass

    def export_info(self):
        return self.state, self.kw

    def import_info(self, info):
        self.state, self.kw = info

    def kill(self):
        self.unmap()
        for c in self.children:
            c.kill()

    def map(self, type=None, **kw):
        self.parent.children.append(self)
        self.box.map(type, **kw)

    def unmap(self):
        self.parent.children.remove(self)
        self.box.unmap()

class SelectableWidget(Widget):
    ATTR = {"selected":False}

    @property
    def selected(self):
        return self["selected"]

    @selected.setter
    def selected(self, value):
        if value:
            self.select()
        else:
            self.deselect()

    def select(self):
        self["selected"] = True

    def deselect(self):
        self["selected"] = False

    def toogle(self):
        if self.selected:
            self.deselect()
        else:
            self.select()

    def command(self):
        self.toogle()

class Frame(Widget):
    ATTR = {"width":0, "height":0, "relwidth":None, "relheight":None}

    def init(self):
        size = [0, 0]

        for i, x in enumerate(("width", "height")):
            v = self[x]
            if not v and self["rel" + x]:
                v = epg.math.round_to_int(self.parent.box.width * self["rel" + x])
            size[i] = v

        return size

    def draw(self, screen=None, offset=None):
        pass
            
class Button(Widget):
    ATTR = {"command":None}

    def command(self):
        if self["command"]:
            self["command"](self)

    def events(self, event):
        if self.state != "disabled":
            if event.type == epg.MOUSEBUTTONDOWN:
                if event.button == 1 and self.box.collidepoint(event.pos):
                    self.state = "active"

            elif event.type == epg.MOUSEBUTTONUP:
                if event.button == 1 and self.state == "active":
                    self.state = "normal"
                    if self.box.collidepoint(event.pos):
                        self.command()

    def update(self):
        if self.state in ("normal", "hover"):
            pos = epg.mouse.get_pos()
            if self.box.collidepoint(pos):
                self.state = "hover"
            else:
                self.state = "normal"

class Checkbutton(SelectableWidget, Button):
    ATTR = SelectableWidget.ATTR.copy()
    ATTR.update(Button.ATTR)

    def command(self):
        SelectableWidget.command(self)
        Button.command(self)

class Radiobutton(SelectableWidget, Button):
    ATTR = {"variable":None, "value":None}

    def __init__(self, *args, **kw):
        SelectableWidget.__init__(self, *args, **kw)
        kw["variable"].bind(self)

    @property
    def selected(self):
        return self["variable"].get() == self["value"]            

    def select(self):
        self["variable"].set(self["value"])

    def deselect(self):
        epg.throw("cannot deselect radiobuttons")

    def command(self):
        self.select()
        Button.command(self)

    def kill(self):
        super().kill()
        self["variable"].widgets.remove(self)

class Input(SelectableWidget):
    ATTR = SelectableWidget.ATTR.copy()
    ATTR.update({"index":0, "text":"", "charnum":None})

    @property
    def index(self):
        return self["index"]

    @index.setter
    def index(self, value):
        if value == "end":
            value = len(self["text"])
        else:
            value = epg.math.clamp(value, 0, len(self["text"]))\

        self["index"] = value

    @property
    def text(self):
        return self["text"]

    @text.setter
    def text(self, value):
        self["text"] = str(value)

    def clear(self):
        self.text = ""
        self.index = 0
        self.update_widget()

    def backspace(self, num=1):
        self.text = self.text[:(self.index - num)] + self.text[self.index:]
        self.index -= num
        self.update_widget()

    def delete(self, num=1):
        self.text = self.text[:self.index] + self.text[(self.index + num):]
        self.update_widget()

    def text_edit(self, text):
        raise NotImplementedError("Input.text_edit(self, text) -> (ime_pos_x, ime_pos_y)")

    def text_input(self, char):
        self.text = self.text[:self.index] + char + self.text[self.index:]
        self.index += len(char)
        if self["charnum"] != None and len(self.text) > self["charnum"]:
            self.text_overload()
        self.update_widget()

    def text_overload(self):
        self.backspace(len(self.text) - self["charnum"])

    def events(self, event):
        if self.selected:
            if event.type == epg.TEXTEDITING:
                pos = self.text_edit(event.text)
                epg.key.set_text_input_rect((pos[0], pos[1], 0, 0))

            elif event.type == epg.TEXTINPUT:
                self.text_input(event.text)

            elif event.type == epg.KEYDOWN:
                match event.key:
                    case epg.K_BACKSPACE:
                        self.backspace()
                    case epg.K_DELETE:
                        self.delete()
                    case epg.K_HOME:
                        self.index = 0
                    case epg.K_END:
                        self.index = "end"
                    case epg.K_LEFT:
                        self.index -= 1
                    case epg.K_RIGHT:
                        self.index += 1
