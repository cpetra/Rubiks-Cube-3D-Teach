from ursina import *
class GuideCircle(Entity):
    def __init__(self, position=(0,0,0), rotation=(0,0,0), radius=2.0, segments=32, scale=(1,1,1)):
        super().__init__(
            position=position,
            scale=scale,
            rotation=rotation
        )

        # Create vertices for the circle
        vertices = []
        for i in range(segments + 1):
            angle = 2 * math.pi * i / segments
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            vertices.append(Vec3(x, y, 0))

        # Create Mesh
        self.circle = Entity(
            parent=self,
            model=Mesh(vertices=vertices, mode='line', thickness=8),
            color=color.black,
            position=(0, 0, 0),
            alpha=0.4
        )

        self.cone = Entity(
            parent=self,
            model=Cone(resolution=32, height=0.8),  # Adjust base and height as needed
            color=color.black,
            position=(radius, -0.4, 0.0),  # Adjust position to be slightly above the circle
            scale=(0.4, 1.0, 0.4),
            alpha=0.4
        )

class Game(Ursina.__closure__[0].cell_contents):
    def __init__(self):
        super().__init__()
        window.fullscreen = True
        Entity(model='quad', scale=60, texture='white_cube', texture_scale=(60, 60), rotation_x=90, y=-5,
               color=color.light_gray)  # plane
        Entity(model='sphere', scale=100, texture='textures/blank.png', double_sided=True)  # sky
        EditorCamera()

        camera.world_position = (0, 0, -15)
        self.model, self.texture = 'models/custom_cube', 'textures/rubik_texture'
        self.load_game()
        self.ignore_key = False

    def load_game(self):
        self.create_cube_positions()
        self.CUBES = [Entity(model=self.model, texture=self.texture, position=pos) for pos in self.SIDE_POSITIONS]
        self.PARENT = Entity()
        self.rotation_axes = {'LEFT': 'x', 'RIGHT': 'x', 'TOP': 'y', 'BOTTOM': 'y', 'FACE': 'z', 'BACK': 'z'}
        self.cubes_side_positons = {'LEFT': self.LEFT, 'BOTTOM': self.BOTTOM, 'RIGHT': self.RIGHT, 'FACE': self.FACE,
                                    'BACK': self.BACK, 'TOP': self.TOP}
        self.animation_time = 0.5
        self.action_trigger = True
        self.action_mode = True
        self.message = Text(origin=(0, 19), color=color.black)
        self.guidetext = Text(origin=(-.5, -5), color=color.black, scale=2)
        self.toggle_game_mode()
        self.create_sensors()
        self.create_control_buttons()
        self.random_state(rotations=3) # initial state of the cube, rotations - number of side turns
        self.guideCircle = GuideCircle(position=(3.0, 0, 0), rotation=(0,90,0))
        self.hideGuideCircle()
        #self.setGuideCircle('right')

    def create_control_buttons(self):
        """Create 12 rotation buttons in top-left corner"""
        faces = ['TOP', 'BOTTOM', 'FACE', 'BACK', 'LEFT', 'RIGHT']
        faces_map = {
            'TOP': 'U',
            'BOTTOM': 'D',
            'FACE': 'F',
            'BACK': 'B',
            'LEFT': 'L',
            'RIGHT': 'R'
        }
        button_properties = {
            'scale': (0.1, 0.04),
            'text_size': 0.8,
            'color': color.dark_gray,
            'parent': camera.ui
        }

        # Create two columns of buttons
        for i, face in enumerate(faces):
            # Clockwise buttons (left column)
            Button(
                text=faces_map[face],
                position=(-0.72, 0.45 - i*0.05),
                on_click=Func(self.rotate_side, face, False),
                **button_properties
            )
            
            # Counter-clockwise buttons (right column)
            Button(
                text=f"{faces_map[face]}\'",
                position=(-0.59, 0.45 - i*0.05),
                on_click=Func(self.rotate_side, face, True),
                **button_properties
            )

    def hideGuideCircle(self):
        self.guideCircle.visible = False
        self.guidetext.text = ''
        
    def setGuideCircle(self, position='right', inverted=False):
        angle = 90 if not inverted else -90
        suffix = '\'' if inverted else ''
        self.guideCircle.visible = True
        if position == 'right':
            self.guideCircle.position = (3.0, 0, 0)
            self.guideCircle.rotation = (90-angle, 90, 0)
            text = 'R'
        elif position == 'left':
            self.guideCircle.position = (-3.0, 0, 0)
            self.guideCircle.rotation = (90-angle, 90, 0)
            text = 'L'
        elif position == 'up':
            self.guideCircle.position = (0, 3.0, 0)
            self.guideCircle.rotation = (-angle, 0, -angle)
            text = 'U'
        elif position == 'down':
            self.guideCircle.position = (0, -3.0, 0)
            self.guideCircle.rotation = (-angle, 0, -angle)
            text = 'D'
        elif position == 'front':
            self.guideCircle.position = (0, 0, -3.0)
            self.guideCircle.rotation = (180, angle-90, 90)
            text = 'F'
        elif position == 'back':
            self.guideCircle.position = (0, 0, 3.0)
            self.guideCircle.rotation = (180, angle-90, 90)
            text = 'B'
        msg = dedent(f"{text}{suffix}").strip()
        self.guidetext.text = msg

#        invoke(self.toggle_animation_trigger, delay=self.animation_time + 0.11)

    def random_state(self, rotations=3):
        [self.rotate_side_without_animation(random.choice(list(self.rotation_axes))) for i in range(rotations)]

    def rotate_side_without_animation(self, side_name):
        cube_positions = self.cubes_side_positons[side_name]
        rotation_axis = self.rotation_axes[side_name]
        self.reparent_to_scene()
        for cube in self.CUBES:
            if cube.position in cube_positions:
                cube.parent = self.PARENT
                exec(f'self.PARENT.rotation_{rotation_axis} = 90')

    def create_sensors(self):
        '''detectors for each side, for detecting collisions with mouse clicks'''
        create_sensor = lambda name, pos, scale: Entity(name=name, position=pos, model='cube', color=color.dark_gray,
                                                        scale=scale, collider='box', visible=False)
        self.LEFT_sensor = create_sensor(name='LEFT', pos=(-0.99, 0, 0), scale=(1.01, 3.01, 3.01))
        self.FACE_sensor = create_sensor(name='FACE', pos=(0, 0, -0.99), scale=(3.01, 3.01, 1.01))
        self.BACK_sensor = create_sensor(name='BACK', pos=(0, 0, 0.99), scale=(3.01, 3.01, 1.01))
        self.RIGHT_sensor = create_sensor(name='RIGHT', pos=(0.99, 0, 0), scale=(1.01, 3.01, 3.01))
        self.TOP_sensor = create_sensor(name='TOP', pos=(0, 1, 0), scale=(3.01, 1.01, 3.01))
        self.BOTTOM_sensor = create_sensor(name='BOTTOM', pos=(0, -1, 0), scale=(3.01, 1.01, 3.01))

    def toggle_game_mode(self):
        '''switching view mode or interacting with Rubik's cube'''
        self.action_mode = not self.action_mode
        msg = dedent(f"{'ACTION mode ON' if self.action_mode else 'VIEW mode ON'}"
                     f" (to switch - press middle mouse button)").strip()
        self.message.text = msg

    def toggle_animation_trigger(self):
        '''prohibiting side rotation during rotation animation'''
        self.action_trigger = not self.action_trigger

    def rotate_side(self, side_name, inverse=False):
        self.action_trigger = False
        cube_positions = self.cubes_side_positons[side_name]
        rotation_axis = self.rotation_axes[side_name]
        self.reparent_to_scene()
        for cube in self.CUBES:
            if cube.position in cube_positions:
                cube.parent = self.PARENT
                if inverse:
                    eval(f'self.PARENT.animate_rotation_{rotation_axis}(-90, duration=self.animation_time)')
                else:
                    eval(f'self.PARENT.animate_rotation_{rotation_axis}(90, duration=self.animation_time)')
        invoke(self.toggle_animation_trigger, delay=self.animation_time + 0.11)

    def reparent_to_scene(self):
        for cube in self.CUBES:
            if cube.parent == self.PARENT:
                world_pos, world_rot = round(cube.world_position, 1), cube.world_rotation
                cube.parent = scene
                cube.position, cube.rotation = world_pos, world_rot
        self.PARENT.rotation = 0

    def create_cube_positions(self):
        self.LEFT = {Vec3(-1, y, z) for y in range(-1, 2) for z in range(-1, 2)}
        self.BOTTOM = {Vec3(x, -1, z) for x in range(-1, 2) for z in range(-1, 2)}
        self.FACE = {Vec3(x, y, -1) for x in range(-1, 2) for y in range(-1, 2)}
        self.BACK = {Vec3(x, y, 1) for x in range(-1, 2) for y in range(-1, 2)}
        self.RIGHT = {Vec3(1, y, z) for y in range(-1, 2) for z in range(-1, 2)}
        self.TOP = {Vec3(x, 1, z) for x in range(-1, 2) for z in range(-1, 2)}
        self.SIDE_POSITIONS = self.LEFT | self.BOTTOM | self.FACE | self.BACK | self.RIGHT | self.TOP

    def input(self, key, *released):
        if key in 'mouse1 mouse3' and self.action_mode and self.action_trigger:
            for hitinfo in mouse.collisions:
                collider_name = hitinfo.entity.name
                if (key == 'mouse1' and collider_name in 'LEFT RIGHT FACE BACK' or
                        key == 'mouse3' and collider_name in 'TOP BOTTOM'):
                    self.rotate_side(collider_name)
                    break
        elif key in 'shift-mouse1 shift-mouse3' and self.action_mode and self.action_trigger:
            for hitinfo in mouse.collisions:
                collider_name = hitinfo.entity.name
                if (key == 'shift-mouse1' and collider_name in 'LEFT RIGHT FACE BACK' or
                        key == 'shift-mouse3' and collider_name in 'TOP BOTTOM'):
                    self.rotate_side(collider_name, inverse=True)
                    break
        if key == 'mouse2':
            self.toggle_game_mode()
        if key == 'r':
            if self.ignore_key:
                self.ignore_key = False
            else:
                self.setGuideCircle('right')
        elif key == 'shift-r':
            self.ignore_key = True
            self.setGuideCircle('right', inverted=True)
        elif key == 'l':
            if self.ignore_key:
                self.ignore_key = False
            else:
                self.setGuideCircle('left')
        elif key == 'shift-l':
            self.ignore_key = True
            self.setGuideCircle('left', inverted=True)
        elif key == 'u':
            if self.ignore_key:
                self.ignore_key = False
            else:
                self.setGuideCircle('up')
        elif key == 'shift-u':
            self.ignore_key = True
            self.setGuideCircle('up', inverted=True)
        elif key == 'd':
            if self.ignore_key:
                self.ignore_key = False
            else:
                self.setGuideCircle('down')
        elif key == 'shift-d':
            self.ignore_key = True
            self.setGuideCircle('down', inverted=True)
        elif key == 'f':
            # f may come immediately after shift-f, so ignore the key
            if self.ignore_key:
                self.ignore_key = False
            else:
                self.setGuideCircle('front')
        elif key == 'shift-f':
            self.ignore_key = True
            self.setGuideCircle('front', inverted=True)
        elif key == 'b':
            if self.ignore_key:
                self.ignore_key = False
            else:
                self.setGuideCircle('back')
        elif key == 'shift-b':
            self.ignore_key = True
            self.setGuideCircle('back', inverted=True)
        elif key == 'h':
            self.hideGuideCircle()

        super().input(key)

if __name__ == '__main__':
    game = Game()
    game.run()