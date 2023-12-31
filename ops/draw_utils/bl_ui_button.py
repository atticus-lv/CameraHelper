from .bl_ui_widget import BL_UI_Widget

import gpu
import blf
# import bgl
import bpy
from gpu_extras.batch import batch_for_shader
from . import wrap_gpu_state
from .shader import wrap_blf_size

class BL_UI_Button(BL_UI_Widget):

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        self._text_color = (1.0, 1.0, 1.0, 1.0)
        self._hover_bg_color = (0.5, 0.5, 0.5, 1.0)
        self._select_bg_color = (0.7, 0.7, 0.7, 1.0)

        self._text = "Button"
        self._text_size = 16
        self._textpos = (x, y)

        self.__state = 0
        self.__image = None
        self.__image_size = (24, 24)
        self.__image_position = (4, 2)

    @property
    def text_color(self):
        return self._text_color

    @text_color.setter
    def text_color(self, value):
        self._text_color = value

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value

    @property
    def text_size(self):
        return self._text_size

    @text_size.setter
    def text_size(self, value):
        self._text_size = value

    @property
    def hover_bg_color(self):
        return self._hover_bg_color

    @hover_bg_color.setter
    def hover_bg_color(self, value):
        self._hover_bg_color = value

    @property
    def select_bg_color(self):
        return self._select_bg_color

    @select_bg_color.setter
    def select_bg_color(self, value):
        self._select_bg_color = value

    def set_image_size(self, imgage_size):
        self.__image_size = imgage_size

    def set_image_position(self, image_position):
        self.__image_position = image_position

    def set_image(self, rel_filepath):
        try:
            self.__image = bpy.data.images.load(rel_filepath, check_existing=True)
            self.__image.gl_load()
        except:
            pass

    def update(self, x, y):
        super().update(x, y)
        area_height = self.get_area_height()
        self._textpos = [x, area_height - y]

    def draw(self):
        if not self.visible:
            return

        area_height = self.get_area_height()

        self.shader.bind()

        self.set_colors()

        with wrap_gpu_state():

            self.batch_panel.draw(self.shader)

            self.draw_image()


        # Draw text
        self.draw_text(area_height)

    def set_colors(self):
        color = self._bg_color
        text_color = self._text_color

        # pressed
        if self.__state == 1:
            color = self._select_bg_color

        # hover
        elif self.__state == 2:
            color = self._hover_bg_color

        self.shader.uniform_float("color", color)

    def draw_text(self, area_height):
        wrap_blf_size(0,self._text_size)
        size = blf.dimensions(0, self._text)

        textpos_y = area_height - self._textpos[1] - (self.height + size[1]) / 2.0
        blf.position(0, self._textpos[0] + (self.width - size[0]) / 2.0, textpos_y + 1, 0)

        r, g, b, a = self._text_color
        blf.color(0, r, g, b, a)

        blf.draw(0, self._text)

    def draw_image(self):
        if self.__image is None:
            return
        try:
            off_x = self.over_scale(self._image_position[0])
            off_y = self.over_scale(self._image_position[1])

            sx = self.over_scale(self._image_size[0])
            sy = self.over_scale(self._image_size[1])

            x_screen = self.over_scale(self.x_screen)
            y_screen = self.over_scale(self.y_screen)

            texture = gpu.texture.from_image(self._image)

            # Bottom left, top left, top right, bottom right
            vertices = ((x_screen + off_x, y_screen - off_y),
                        (x_screen + off_x, y_screen - sy - off_y),
                        (x_screen + off_x + sx, y_screen - sy - off_y),
                        (x_screen + off_x + sx, y_screen - off_y))

            self.shader_img = gpu.shader.from_builtin('2D_IMAGE')
            self.batch_img = batch_for_shader(self.shader_img,
                                              'TRI_FAN', {"pos": vertices,
                                                          "texCoord": ((0, 1), (0, 0), (1, 0), (1, 1)), },
                                              )
            # import bgl
            # bgl.glActiveTexture(bgl.GL_TEXTURE0)
            # bgl.glBindTexture(bgl.GL_TEXTURE_2D, self._image.bindcode)

            self.shader_img.bind()
            # self.shader_img.uniform_int("image", 0)
            self.shader_img.uniform_sampler("image", texture)
            self.batch_img.draw(self.shader_img)
        except Exception as e:
            pass

        return False

    def set_mouse_down(self, mouse_down_func, obj):
        self.mouse_down_func_obj = obj
        self.mouse_down_func = mouse_down_func

    def mouse_down(self, x, y):
        if self.is_in_rect(x, y):
            self.__state = 1
            try:
                self.mouse_down_func(self.mouse_down_func_obj)
            except:
                pass

            return True

        return False

    def mouse_move(self, x, y):
        if self.is_in_rect(x, y):
            if (self.__state != 1):
                # hover state
                self.__state = 2
        else:
            self.__state = 0

    def mouse_up(self, x, y):
        if self.is_in_rect(x, y):
            self.__state = 2
        else:
            self.__state = 0
