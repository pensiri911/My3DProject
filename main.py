import pygame as pg
import math
import os
from object_3d import *
from camera import *
from projection import *
from player import *
from wall import *

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

    # =========================================================
    # SETUP
    # =========================================================

    def create_objects(self):
        self.camera = Camera(self, [-5, 5, -50])
        self.projection = Projection(self)
        self.player = Player(self, [20, 0, 0])

        self.cat = self.load_obj('resource/smolcatobj.obj')
        self.cat.rotate_z(math.pi/4 )
        self.cat2 = self.load_obj('resource/megumi3.obj')
        self.cat2.translate([1, -2, 0])
        
        self.walls = [
            Wall(self, position=[20, 0, 10], width=8, depth=0.5, height=3),
            Wall(self, position=[20, 0, -5], width=8, depth=0.5, height=3),
        ]

    # =========================================================
    # ASSET LOADING
    # =========================================================

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
        
        # ✅ ใช้ directory ของไฟล์ .obj เป็น base path
        obj_dir = os.path.dirname(filename)

        with open(filename) as f:
            for line in f:
                if line.startswith('mtllib '):
                    # ✅ โหลด .mtl จาก folder เดียวกับ .obj เลย
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

    # =========================================================
    # UPDATE
    # =========================================================

    def update(self):
        self.dt = self.clock.get_time() / 1000.0 
        self.player.update(self.dt)
        self.update_camera()
        for wall in self.walls:
            wall.check_collision(self.player.hitbox)

    def update_camera(self):
        distance = 8
        height = 0
        angle_rad = self.player.angle_y

        # คำนวณ position ใหม่ก่อน
        cam_x = self.player.position[0] - math.sin(angle_rad) * distance
        cam_y = self.player.position[1] + height
        cam_z = self.player.position[2] - math.cos(angle_rad) * distance

        # คำนวณ dx/dy/dz จาก cam position ใหม่
        dx = self.player.position[0] - cam_x
        dy = (self.player.position[1] + 1.0) - cam_y
        dz = self.player.position[2] - cam_z
        distance_2d = math.sqrt(dx**2 + dz**2)

        self.camera.position = np.array([cam_x, cam_y, cam_z, 1.0])
        self.camera.yaw = math.atan2(dx, dz)
        self.camera.pitch = -math.atan2(dy, distance_2d)
        self.camera.update_vectors()

    # =========================================================
    # DRAW
    # =========================================================

    def draw(self):
        self.screen.fill(pg.Color('darkslategray'))
        self.polygon_pool.clear()

        self.update()

        self.player.draw()
        #self.cat.draw()
        self.cat2.draw()
        for wall in self.walls:
            wall.draw()

        self.render_polygons()

    def render_polygons(self):
        self.polygon_pool.sort(key=lambda x: x['depth'], reverse=True)
        for poly in self.polygon_pool:
            pts = poly['points']
            if len(pts) >= 3:
                pg.draw.polygon(self.screen, poly['color'], pts)
                pg.draw.polygon(self.screen, pg.Color('black'), pts, 1)
                self.player.hitbox.draw_debug(self.screen, self.camera, self.projection)

    # =========================================================
    # GAME LOOP
    # =========================================================

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
