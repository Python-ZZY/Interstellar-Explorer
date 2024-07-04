import epg

def get_padded(f):
	def func(*args, padx=0, pady=0, **kw):
		surf = f()(*args, **kw)

		if padx or pady:
			bg = epg.Surface((surf.get_width() + padx*2, surf.get_height() + pady*2)).convert_alpha()
			bg.fill((0, 0, 0, 0))
			bg.blit(surf, (padx, pady))
			return bg
		return surf

	return func

@get_padded
def Text():
	return epg.text_render

@get_padded
def Image():
	return epg.sprite.get_surface

@get_padded
def Ln():
	return render

default_textstyle = {}
default_imagestyle = {}

def render(*sth, anchor="center", bgcolor=(0, 0, 0, 0), textstyle=default_textstyle, imagestyle=default_imagestyle):
	rs, ws, hs = [], [], []

	for obj in sth:
		if isinstance(obj, str):
			obj = Text(obj, **textstyle)
		rs.append(obj)

		ws.append(obj.get_width())
		hs.append(obj.get_height())

	surf = epg.Surface((sum(ws), maxh := max(hs))).convert_alpha()
	surf.fill(bgcolor)

	x = 0
	for i, r in enumerate(rs):
		rect = epg.Rect(x, 0, ws[i], hs[i])
		setattr(rect, anchor, getattr(epg.Rect(x, 0, ws[i], maxh), anchor))
		x += ws[i]
		surf.blit(r, rect)
	return surf

def renders(*sth, anchor="center", bgcolor=(0, 0, 0, 0), textstyle=default_textstyle, imagestyle=default_imagestyle):
	rs, ws, hs = [], [], []

	for obj in sth:
		if not isinstance(obj, epg.Surface):
			obj = render(*obj, textstyle=textstyle, imagestyle=imagestyle)
		rs.append(obj)

		ws.append(obj.get_width())
		hs.append(obj.get_height())

	surf = epg.Surface((maxw := max(ws), sum(hs))).convert_alpha()
	surf.fill(bgcolor)

	y = 0
	for i, r in enumerate(rs):
		rect = epg.Rect(0, y, ws[i], hs[i])
		setattr(rect, anchor, getattr(epg.Rect(0, y, maxw, hs[i]), anchor))
		y += hs[i]
		surf.blit(r, rect)
	return surf

			
