import epg

def colliderect(rect1, rect2, mask1=None, mask2=None, **maskkw):
	if not mask1: mask1 = epg.get_mask(rect1, **maskkw)
	if not mask2: mask2 = epg.get_mask(mask2, **maskkw)
	return mask1.overlap(mask2, (rect2[0] - rect1[0], rect2[1] - rect1[1]))

def collidepoint(rect, point, mask=None, **maskkw):
	if not mask: mask = epg.get_mask(rect, **maskkw)
	try:
		return mask.get_at((point[0] - rect[0], point[1] - rect[1]))
	except IndexError:
		return False
