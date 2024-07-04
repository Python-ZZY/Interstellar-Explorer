import epg
from pygame.mask import *

def get(obj, fill=True, threshold=127):
	if isinstance(obj, epg.Rect):
		return Mask(obj.size, fill=True)
	elif isinstance(obj, epg.Surface):
		return from_surface(obj, threshold=threshold)
	elif not isinstance(obj, Mask):
		epg.throw("invalid type", repr(type(obj)))

def get_shaped_mask(size, func, fill=True, threshold=127, *args, **kw):
	surf = epg.Surface(size).convert_alpha()
	surf.fill(0, 0, 0, 0)
	func(surf, (255, 255, 255), *args, **kw)
	return get_mask(surf, fill, threshold)
