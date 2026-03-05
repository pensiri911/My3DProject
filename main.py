import pygame as pg
import math
import os
from object_3d import *
from camera import *
from projection import *
from player import *
from wall import *
from ground import Ground, generate_parkour
from billboard import Billboard

class SoftwareRender:
    def __init__(self):
        pg.init()
        self.RES = self.WIDTH, self.HEIGHT = 800, 450
        self.H_WIDTH, self.H_HEIGHT = self.WIDTH // 2, self.HEIGHT // 2
        self.FPS = 60
        self.screen = pg.display.set_mode(self.RES)
        self.clock = pg.time.Clock()
        self.polygon_pool = []
        pg.mouse.set_visible(False)
        pg.event.set_grab(True)
        self.create_objects()

    def create_objects(self):
        self.camera = Camera(self, [-5, 5, -50])
        self.projection = Projection(self)
        self.player = Player(self, [0, 2, 0])
        self.cat2 = self.load_obj('resource/megumi3.obj')
        self.cat2.translate([-2, 0, -1])
        self.walls = [
            Wall(self, position=[20, 0, 10], width=8, depth=0.5, height=3),
            Wall(self, position=[20, 0, -5], width=8, depth=0.5, height=3),
        ]
        self.billboards = [
            Billboard(self, 'cat.jpg', position=[-5, 1, 10], width=2, height=2),
            # Billboard(self, 'resource/tree.png', position=[-3, 1, 15], width=1.5, height=3),
        ]
        self.grounds, self.spawn = generate_parkour(self, start=(0, 0, 0))
        self._sky_surface = self._build_sky_surface()
        
    def _build_sky_surface(self):
        top    = (30,  60, 114)
        bottom = (135, 190, 235)
        surf = pg.Surface((self.WIDTH, self.HEIGHT))
        for y in range(self.HEIGHT):
            t = y / self.HEIGHT
            r = int(top[0] + (bottom[0] - top[0]) * t)
            g = int(top[1] + (bottom[1] - top[1]) * t)
            b = int(top[2] + (bottom[2] - top[2]) * t)
            pg.draw.line(surf, (r, g, b), (0, y), (self.WIDTH, y))
        return surf

    def load_mtl(self, filename):
        materials = {}
        current_mat = None
        try:
            with open(filename) as f:
                for line in f:
                    if line.startswith('newmtl '):
                        current_mat = line.split()[1]
                    elif line.startswith('Kd ') and current_mat:
                        r, g, b = [float(i) for i in line.split()[1:4]]
                        materials[current_mat] = pg.Color(int(r * 255), int(g * 255), int(b * 255))
        except FileNotFoundError:
            print(f"Warning: MTL file '{filename}' not found.")
        return materials

    def load_obj(self, filename):
        vertex, faces, color_faces = [], [], []
        materials = {}
        current_color = pg.Color('white')
        obj_dir = os.path.dirname(filename)
        with open(filename) as f:
            for line in f:
                if line.startswith('mtllib '):
                    mtl_path = os.path.join(obj_dir, line.split()[1])
                    materials = self.load_mtl(mtl_path)
                elif line.startswith('usemtl '):
                    current_color = materials.get(line.split()[1], pg.Color('white'))
                elif line.startswith('v '):
                    vertex.append([float(i) for i in line.split()[1:]] + [1])
                elif line.startswith('f '):
                    indices = [int(f.split('/')[0]) - 1 for f in line.split()[1:]]
                    for i in range(1, len(indices) - 1):
                        face = [indices[0], indices[i], indices[i + 1]]
                        faces.append(face)
                        color_faces.append((current_color, face))
        return Object3D(self, vertex, faces, color_faces)

    def update(self):
        raw_dt = self.clock.get_time() / 1000.0
        self.dt = min(raw_dt, 1/30)
        # 1. reset grounded
        self.player.is_grounded = False
        self.player._prev_y = self.player.position[1]
        # 2. apply gravity และขยับ Y ก่อน
        self.player.velocity_y += self.player.gravity * self.dt * 60
        self.player.velocity_y = max(self.player.velocity_y, -1.0)
        self.player.position[1] += self.player.velocity_y * self.dt * 60

        # 3. เช็ค ground หลัง gravity
        for ground in self.grounds:
            ground.resolve_player(self.player, self.player.hitbox)

        # 4. player update (เดิน, กระโดด, animation)
        self.player.update(self.dt)

        # 5. wall collision
        for wall in self.walls:
            wall.check_collision(self.player.hitbox)

        # 6. camera
        self.update_camera()

        # 7. respawn ถ้าตกโลก
        if self.player.position[1] < -20:
            self.player.position = self.spawn.copy()
            self.player.velocity_y = 0

    def update_camera(self):
        distance = 8
        height = 3
        angle_rad = self.player.angle_y
        cam_x = self.player.position[0] - math.sin(angle_rad) * distance
        cam_y = self.player.position[1] + height
        cam_z = self.player.position[2] - math.cos(angle_rad) * distance
        dx = self.player.position[0] - cam_x
        dy = (self.player.position[1] + 1.0) - cam_y
        dz = self.player.position[2] - cam_z
        distance_2d = math.sqrt(dx**2 + dz**2)
        self.camera.position = np.array([cam_x, cam_y, cam_z, 1.0])
        self.camera.yaw = math.atan2(dx, dz)
        self.camera.pitch = -math.atan2(dy, distance_2d)
        self.camera.update_vectors()

    def draw(self):
        # self.screen.fill(pg.Color('darkslategray'))
        self.draw_sky()
        self.polygon_pool.clear()
        self.update()
        ground_pool = []
        for ground in self.grounds:
            ground._mesh.draw(ground_pool)
        ground_pool.sort(key=lambda x: x['depth'], reverse=True)
        self.player.draw()
        self.cat2.draw()
        for wall in self.walls:
            wall.draw()
        for b in self.billboards:
            b.draw()
        self.render_polygons(ground_pool)
        
        

    def render_polygons(self, ground_pool=None):
        if ground_pool:
            for poly in ground_pool:
                pts = poly['points']
                if len(pts) >= 3:
                    pg.draw.polygon(self.screen, poly['color'], pts)

        self.polygon_pool.sort(key=lambda x: x['depth'], reverse=True)
        for poly in self.polygon_pool:
            pts = poly['points']
            if len(pts) >= 3:
                pg.draw.polygon(self.screen, poly['color'], pts)
        self.player.hitbox.draw_debug(self.screen, self.camera, self.projection)
        
        
    def draw_sky(self):
        self.screen.blit(self._sky_surface, (0, 0))
        # pg.draw.circle(self.screen, (255, 240, 100), (self.WIDTH - 100, 80), 40)
            
            
    def run(self):
        while True:
            for event in pg.event.get():
                if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                    pg.quit()
                    exit()
            self.draw()
            self.clock.tick(self.FPS)
            pg.display.flip()

if __name__ == '__main__':
    app = SoftwareRender()
    app.run()
