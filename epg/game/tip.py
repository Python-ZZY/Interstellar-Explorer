import epg

class TipManager:
	_id = 0

	def __init__(self, scene=None):
		self.scene = scene if scene else epg.app.scene
		self.tips = {} # (sprite, last_until, alive)

	def __getitem__(self, key):
		return self.tips[key]

	def __setitem__(self, key, value):
		self.tips[key] = value

	def __delitem__(self, key):
		del self.tips[key]

	def add(self, *args, id=None, cls=epg.sprite.Static, duration=0, **kw):
		if not id:
			self._id += 1
			id = f"tip_{self._id}"

		surf = tip_renderer.render(*args, **kw)
		s = cls(surf)
		self.tips[id] = (s, epg.get_time() + duration if duration != False else False, False)
		s.fade_in()

		return s

	def update(self):
		for key, (sprite, time, alive) in self.tips.items():
			sprite.update()

			if now > time:
				pass

class BaseTipSprite:
	def __init__(self, duration, renderer):
		self.duration = duration
		self.renderer = renderer
		self.alive = False

	def show(self):
		self.alive = True
		self.renderer.fade_in(self)
		self.time_to = epg.time.get_time() + self.duration

	def kill(self):
		self.alive = False
		
	def update(self):
		if self.alive:
			now = epg.get_time()
			if now > self.time_to:
				self.kill()

class TipSprite(epg.Static, BaseTipSprite):
	def __init__(self, *args, duration=False, renderer=None, **kw):
		epg.Static.__init__(self, *args, **kw)
		BaseTipSprite.__init__(self, duration, renderer or tip_renderer)

class ATipSprite(epg.AStatic, BaseTipSprite):
	def __init__(self, *args, duration=False, renderer=None, **kw):
		epg.AStatic.__init__(self, *args, **kw)
		BaseTipSprite.__init__(self, duration, renderer or tip_renderer)

class TipRenderer:
	def fade_in(self, sprite):
		pass

	def fade_out(self, sprite):
		sprite.kill()

	def render(self, *args, **kw):
		return epg.text_render(*args, **kw)

tip_renderer = TipRenderer()