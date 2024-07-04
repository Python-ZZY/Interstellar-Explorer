import epg

_SX = "left", "right"
_SY = "top", "bottom"
_SIDES = _SX + _SY

def get_anchor(anchor):
	if anchor in _SIDES:
		return "mid" + anchor
	return anchor

def _get_side_idx(side):
	if side in _SX:
		return 0
	elif side in _SY:
		return 1
	epg.throw(side)

class BaseUI:
	@property
	def all_children(self):
		cs = []
		for c in self.children:
			cs.append(c)
			cs.extend(c.all_children)
		return cs

	def pack(self, **kw):
		self.map(Pack, **kw)

	def grid(self, **kw):
		self.map(Grid, **kw)

	def place(self, **kw):
		self.map(Place, **kw)

class BaseGM:
	ATTR = {}
	def __init__(self, parent, children):
		self.parent = parent
		self.children = children

		self.ATTR.update({"padx":None, "pady":None})
		self.init()

	def get_children(self):
		'''process kw'''
		children = self.children.copy()

		for i, (box, _kw) in enumerate(children):
			epg.check_attr(_kw, self.ATTR)
			kw = self.ATTR.copy()
			kw.update(_kw)
			children[i] = box, kw
			self.set_pad(box, kw)

		return children

	def map(self):
		inner = self.parent.get_inner_rect()

		for box, kw in self.get_children():
			outer = box.get_outer_rect()
			new_outer = self.update(outer.copy(), inner, kw, box)
			box.size += epg.Vector2(new_outer.size) - outer.size
			box.x = new_outer.x + box.outpad[0]
			box.y = new_outer.y + box.outpad[2]
			
	def adjust(self, outer, occ_rect, kw):
		'''process anchor and fill'''
		anchor, fill = kw["anchor"], kw["fill"]
		
		if anchor:
			anchor = get_anchor(anchor)
			setattr(outer, anchor, getattr(occ_rect, anchor))
			
		if fill and fill != "none":
			outer.x = occ_rect.x if fill in ("x", "both") else outer.x
			outer.y = occ_rect.y if fill in ("y", "both") else outer.y
			outer.width = occ_rect.width if fill in ("x", "both") else outer.width
			outer.height = occ_rect.height if fill in ("y", "both") else outer.height

	def set_pad(self, box, kw):
		padx, pady = kw["padx"], kw["pady"]
		if padx or pady:
			if not padx: padx = box.outpad[:2]
			if not pady: pady = box.outpad[2:]
			if isinstance(padx, (int, float)): padx = (padx, padx)
			if isinstance(pady, (int, float)): pady = (pady, pady)
				
			box.outpad = (*padx, *pady)
		
	def init(self):
		pass
	
	def update(self, *_):
		pass

	def estimate_size(self):
		pass

class Pack(BaseGM):
	ATTR = {"side":"top", "anchor":"center", "fill":"none"}
	def update(self, outer, inner, kw, *_):
		si = _get_side_idx(kw["side"])
		
		inner[si+2] -= outer[si+2] # width or height
		match kw["side"]:
			case "left":
				occ_rect = inner.x, inner.y, outer.width, inner.height
				inner.x += outer.width
				outer.right = inner.x
			case "right":
				occ_rect = inner.right, inner.y, outer.width, inner.height
				outer.x = inner.right
			case "top":
				occ_rect = inner.x, inner.y, inner.width, outer.height
				inner.y += outer.height
				outer.bottom = inner.y
			case "bottom":
				occ_rect = inner.x, inner.bottom, inner.width, outer.height
				outer.y = inner.bottom

		self.adjust(outer, epg.Rect(occ_rect), kw)
		return outer

	def estimate_size(self):
		pos, bottomright = epg.Vector2(0, 0), [0, 0]

		for box, kw in self.get_children():
			si = _get_side_idx(kw["side"])
			w_or_h = (s := box.estimate_size())[si]

			for i in (0, 1):
				bottomright[i] = max((pos[i] + s[i], bottomright[i]))

			pos[si] += w_or_h
			
		return bottomright

class Grid(BaseGM):
	ATTR = {"column":0, "row":0, "columnspan":1, "rowspan":1, "anchor":"center", "fill":"none"}
	def init(self, getsize=None):
		self.cols, self.rows = {}, {}
		getsize = getsize if getsize else lambda box: box.get_outer_rect().size

		for key, d, attr, span in (("column", self.cols, 0, "columnspan"),
							 ("row", self.rows, 1, "rowspan")):
			for box, kw in self.get_children():
				w = getsize(box)[attr] // kw[span]
				for i in range(kw[span]):
					index = kw[key] + i
					d.setdefault(index, [])
					d[index].append(w)

			d_ = {k:d[k] for k in sorted(d)}
			d.clear()
			d.update(d_)

	def update(self, outer, inner, kw, *_):
		col, row = kw["column"], kw["row"]
		occ_rect = epg.Rect(
			sum([max(v) if k < col else 0 for k, v in self.cols.items()]) + inner.x,
			sum([max(v) if k < row else 0 for k, v in self.rows.items()]) + inner.y,
			sum([max(self.cols[col+i]) for i in range(kw["columnspan"])]),
			sum([max(self.rows[row+i]) for i in range(kw["rowspan"])])
			)
		self.adjust(outer, occ_rect, kw)
		return outer

	def estimate_size(self): # TODO: further test
		self.init(lambda box: box.estimate_size())
		return (
			sum([max(v) for k, v in self.cols.items()]),
			sum([max(v) for k, v in self.rows.items()])
			)

class Place(BaseGM):
	ATTR = {"x":None, "y":None, "relx":None, "rely":None, "anchor":"center",
			"width":None, "height":None, "relwidth":None, "relheight":None}
	def update(self, outer, inner, kw, box):
		s = box.size
		if m := kw["width"]:
			outer.width += m - s[0]
		elif m := kw["relwidth"]:
			outer.width += epg.math.round_to_int(inner.width * m) - s[0]
			
		if m := kw["height"]:
			outer.height += m - s[1]
		elif m := kw["relheight"]:
			outer.height += epg.math.round_to_int(inner.height * m) - s[1]

		anchor = get_anchor(kw["anchor"])
		err = False

		if kw["x"] != None:
			x = inner.x + kw["x"] - box.outpad[0]
		elif kw["relx"] != None:
			x = inner.x + epg.math.round_to_int(inner.width * kw["relx"]) - box.outpad[0]
		else:
			err = True

		if kw["y"] != None:
			y = inner.y + kw["y"] - box.outpad[2]
		elif kw["rely"] != None:
			y = inner.y + epg.math.round_to_int(inner.height * kw["rely"]) - box.outpad[2]
		else:
			err = True

		if err:
			epg.throw("miss required argument(s)")

		setattr(outer, anchor, (x, y))

		return outer

	def estimate_size(self):
		for box, _ in self.children:
			box.estimate_size()

		return self.parent.get_outer_rect().size
	
class Box(epg.Rect, BaseUI):
	def __init__(self, parent, size=(0, 0), inpad=0, outpad=0):
		epg.Rect.__init__(self, (0, 0), size)
		self.orig_rect = epg.Rect.copy(self)
		self.inpad = inpad
		self.outpad = outpad
		self.parent = parent
		self._children = [] # Store children boxes and gm kw
		self.gm_type = None

	def __set_pad(self, attr, arg):
		try:
			arg = int(arg)
		except TypeError:
			length = len(arg)
			if length == 2:
				arg = (arg[0],) * 2 + (arg[1],) * 2
			elif length != 4:
				epg.throw("invalid pad:", arg)
		else:
			arg = (arg,) * 4
		setattr(self, attr, arg)

	@property
	def inpad(self):
		return self._inpad
	@inpad.setter
	def inpad(self, arg):
		if arg != None:
			self.__set_pad("_inpad", arg)

	@property
	def outpad(self):
		return self._outpad
	@outpad.setter
	def outpad(self, arg):
		if arg != None:
			self.__set_pad("_outpad", arg)

	@property
	def children(self):
		return [c[0] for c in self._children]
	
	def copy(self):
		box = self.__class__(self.parent, self.size, self.inpad, self.outpad)
		box.topleft = self.topleft
		return box

	def get_inner_rect(self):
		'''Return the rect used to hold the children'''
		p = self.inpad
		return epg.Rect(
			self.x + p[0],
			self.y + p[2],
			self.width - p[0] - p[1],
			self.height - p[2] - p[3]
			)

	def get_outer_rect(self):
		'''Return the rect used to hold itself'''
		p = self.outpad
		return epg.Rect(
			self.x - p[0],
			self.y - p[2],
			self.width + p[0] + p[1],
			self.height + p[2] + p[3]
			)

	def kill(self):
		self.unmap()
		for c in self.all_children:
			c.kill()

	def resize(self, size):
		self.orig_rect.size = self.size = size

	def map(self, type=None, **kw):
		if self.parent is None:
			epg.throw("no need to", type.__name__, "the top box")

		if not self.parent.children:
			self.parent.gm_type = None

		if self.parent.gm_type and type and self.parent.gm_type != type:
			epg.throw("cannot use geometry manager", repr(type.__name__),
					   "because", repr(self.parent.gm_type.__name__), "is already in use")
		elif not (self.parent.gm_type or type):
			epg.throw("no geometry manager is specified")

		if type:
			self.parent.set_gm(type)
		self.parent._children.append((self, kw))

	def unmap(self):
		for i, c in enumerate(self.parent._children):
			if c[0] == self:
				self.parent._children.pop(i)
				break

	def set_gm(self, type):
		self.gm_type = type
	
	def update_box(self):####################
		rects = [b for b in self.children]
		
		if not self.width:
			self.left = min(rects, key=lambda r:r.left).left
			self.width = max(rects, key=lambda r:r.right).right - self.left

		if not self.height:
			self.top = min(rects, key=lambda r:r.top).top
			self.height = max(rects, key=lambda r:r.bottom).bottom - self.top

	def estimate_size(self, gm=None):
		if self.gm_type:
			if not gm: gm = self.gm_type(self, self._children)
			size = gm.estimate_size()

			p = self.inpad
			if not self.width:
				self.width = size[0] + p[0] + p[1]
			if not self.height:
				self.height = size[1] + p[2] + p[3]

		return self.get_outer_rect().size

	def update_display(self, est=True):
		if self.gm_type and self._children:
			gm = self.gm_type(self, self._children)
			if est: self.estimate_size(gm)

			gm.map()

		for c in self.children:
			c.update_display(est=False)

class BaseBox(Box):
	def __init__(self, pos=(0, 0), size=None, inpad=0, outpad=0):
		Box.__init__(self, None, size if size else epg.display.get_window_size(), inpad, outpad)
		self.move_ip(pos)

	def kill(self):
		for c in self.all_children:
			c.kill()
