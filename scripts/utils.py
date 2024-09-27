import os
import sys
import pygame

BASE_IMG_PATH = "data/images/"

keys = {"quit": pygame.K_q, "mv_left": pygame.K_a, "mv_right": pygame.K_d, "mv_up": pygame.K_w, "mv_down": pygame.K_s, "jump": pygame.K_w, "dash": pygame.K_x, "surf": pygame.K_f, "attack": pygame.K_SPACE, "grab": pygame.K_e, "throw": pygame.K_SPACE, "menu": pygame.K_m}
colors = {"WHITE": (255, 255, 255), "BLACK": (0, 0, 0), "RED": (255, 0, 0), "GREEN": (0, 255, 0), "BLUE": (0, 0, 255), "YELLOW": (255, 255, 0), "CYAN": (0, 255, 255), "MAGENTA": (255, 0, 255), "GRAY": (128, 128, 128), "DARK_GRAY": (64, 64, 64), "LIGHT_GRAY": (192, 192, 192), "ORANGE": (255, 165, 0), "PURPLE": (128, 0, 128), "BROWN": (139, 69, 19), "PINK": (255, 192, 203)}


def load_image(path, alpha=255, color_key=(0, 0, 0)):
	img = pygame.image.load(BASE_IMG_PATH + path)

	if alpha < 255:
		img = img.convert_alpha()
		img.set_alpha(alpha)
	else:
		img = img.convert()
	img.set_colorkey(color_key)
	
	return img


def load_images(path, alpha=255, color_key=(0, 0, 0)):
	images = []
	full_path = os.path.join(BASE_IMG_PATH, path)
	for img_name in sorted(os.listdir(full_path)):
		if img_name.endswith((".png", ".jpg", ".bmp", ".gif")):
			images.append(load_image(os.path.join(path, img_name), alpha, color_key))
	return images


def display_msg(self, txt):
	font = pygame.font.Font(None, 20)
	text_surface = font.render(txt, True, (255, 255, 255))
	text_rect = text_surface.get_rect()
	text_rect.center = (
		self.screen.get_width() / 2,
		self.screen.get_height() / 2,
	)
	self.screen.blit(text_surface, text_rect)
	pygame.display.update()

	while True:
		self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()
			if event.type == pygame.KEYDOWN:
				return event.key


def key_to_number(key):
	if pygame.K_0 <= key <= pygame.K_9:
		return key - pygame.K_0
	else:
		return None


class Animation:
	def __init__(self, images, img_dur=5, loop=True):
		self.images = images
		self.img_duration = img_dur
		self.loop = loop
		self.done = False
		self.frame = 0

	def copy(self):
		return Animation(self.images, self.img_duration, self.loop)

	def update(self):
		if self.loop:
			self.frame = (self.frame + 1) % (self.img_duration * len(self.images))
		else:
			self.frame = min(self.frame + 1, self.img_duration * len(self.images) - 1)
			if self.frame >= self.img_duration * len(self.images) - 1:
				self.done = True

	def img(self):
		return self.images[int(self.frame / self.img_duration)]
