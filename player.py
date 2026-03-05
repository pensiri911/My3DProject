import pygame as pg
import numpy as np
import math
from matrix_function import *
from animation import Animation
from hitbox import Hitbox


class Player:
    def __init__(self, render, position):
        self.render = render
        self.position = np.array([*position, 1.0])
        self.hitbox = Hitbox(self, width=0.6, height=2.4, depth=0.6, offset=(0, -1.5, 0))

        # โหลดชิ้นส่วนโมเดล
        self.body  = render.load_obj('resource/character/body.obj')
        self.head  = render.load_obj('resource/character/head.obj')
        self.arm_l = render.load_obj('resource/character/arm_L.obj')
        self.arm_r = render.load_obj('resource/character/arm_R.obj')
        self.leg_l = render.load_obj('resource/character/leg_L.obj')
        self.leg_r = render.load_obj('resource/character/leg_R.obj')

        for part in [self.body, self.head, self.arm_l, self.arm_r, self.leg_l, self.leg_r]:
            part.movement_flag = False

        # ฟิสิกส์
        self.velocity_y  = 0.0
        self.gravity     = -0.005
        self.jump_power  = 0.15
        self.is_grounded = False
        self.angle_y     = 0.0

        # =========================================================
        # ANIMATIONS
        # =========================================================
        self.animations = {
            'idle': Animation('idle', speed=0.08, swing_amplitude=0.03, bob_amplitude=0.015, mode='sync'),
            'walk': Animation('walk', speed=0.15, swing_amplitude=0.80, bob_amplitude=0.04,  mode='alternate'),
            'jump': Animation('jump', speed=0.16, swing_amplitude=0.50, bob_amplitude=0.00,  mode='sync'),
        }
        self.current_anim = self.animations['idle']

    # =========================================================
    # ANIMATION CONTROL
    # =========================================================

    def set_animation(self, name):
        if self.current_anim.name != name:
            self.current_anim = self.animations[name]

    # =========================================================
    # UPDATE
    # =========================================================

    def update(self, dt):
        keys = pg.key.get_pressed()
        is_moving = False
        move_speed = 0.2 * dt * 60  # ✅ ความเร็วเดินก็ sync ด้วย

        mouse_dx, _ = pg.mouse.get_rel()
        if abs(mouse_dx) > 2:
            self.angle_y += mouse_dx * 0.002

        if keys[pg.K_w]:
            self.position[0] += math.sin(self.angle_y) * move_speed
            self.position[2] += math.cos(self.angle_y) * move_speed
            is_moving = True
        if keys[pg.K_s]:
            self.position[0] -= math.sin(self.angle_y) * move_speed
            self.position[2] -= math.cos(self.angle_y) * move_speed
            is_moving = True
        if keys[pg.K_a]:
            self.position[0] += math.sin(self.angle_y - math.pi / 2) * move_speed
            self.position[2] += math.cos(self.angle_y - math.pi / 2) * move_speed
            is_moving = True
        if keys[pg.K_d]:
            self.position[0] += math.sin(self.angle_y + math.pi / 2) * move_speed
            self.position[2] += math.cos(self.angle_y + math.pi / 2) * move_speed
            is_moving = True

        if keys[pg.K_SPACE] and self.is_grounded:
            self.velocity_y = self.jump_power
            self.is_grounded = False

        self.velocity_y += self.gravity * dt * 60  # ✅ gravity sync ด้วย
        self.position[1] += self.velocity_y * dt * 60
        if self.position[1] <= 0:
            self.position[1] = 0
            self.velocity_y = 0
            self.is_grounded = True

        if not self.is_grounded:
            self.set_animation('jump')
        elif is_moving:
            self.set_animation('walk')
        else:
            self.set_animation('idle')

        self.current_anim.update(dt)  # ✅ ส่ง dt ไปด้วย
        self._update_matrices()

    def _update_matrices(self):
        anim  = self.current_anim
        swing = anim.get_swing()
        bob   = anim.get_bob()

        player_matrix = rotate_y(self.angle_y) @ translate(self.position[:3])

        self.body.matrix  = player_matrix
        
        if anim.mode == 'sync':
            # ✅ แขนสองข้างขยับพร้อมกัน (jump & idle)
            self.arm_l.matrix = rotate_x(swing) @ translate([ 0.18, 0.3, 0]) @ player_matrix
            self.arm_r.matrix = rotate_x(swing) @ translate([-0.18, 0.3, 0]) @ player_matrix
            self.leg_l.matrix = rotate_x(swing) @ translate([ 0.15, -0.6, 0]) @ player_matrix
            self.leg_r.matrix = rotate_x(swing) @ translate([-0.15, -0.6, 0]) @ player_matrix
        else:
            # alternate — แกว่งสลับกันปกติ (walk)
            self.arm_l.matrix = rotate_x( swing) @ translate([ 0.18, 0.3, 0]) @ player_matrix
            self.arm_r.matrix = rotate_x(-swing) @ translate([-0.18, 0.3, 0]) @ player_matrix
            self.leg_l.matrix = rotate_x(-swing) @ translate([ 0.15, -0.6, 0]) @ player_matrix
            self.leg_r.matrix = rotate_x( swing) @ translate([-0.15, -0.6, 0]) @ player_matrix

        # ✅ idle หายใจ — หัวและลำตัวขยับขึ้นลงเบาๆ
        self.head.matrix = translate([0, 0.6 + bob, 0]) @ player_matrix
        self.body.matrix = translate([0, bob * 0.5, 0]) @ player_matrix

    # =========================================================
    # DRAW
    # =========================================================

    def draw(self):
        player_pool = []
        for part in [self.leg_l, self.leg_r, self.body, self.head, self.arm_l, self.arm_r]:
            part.draw(player_pool)
        player_pool.sort(key=lambda x: x['depth'], reverse=True)
        self.render.polygon_pool.extend(player_pool)
