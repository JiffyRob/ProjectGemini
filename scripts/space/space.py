import numpy
import pygame

from scripts import game_state, util_draw
from scripts.animation import AnimatedSurface
from scripts.space import gui3d, math3d, sprite3d


class Space(game_state.GameState):
    def __init__(self, game):
        super().__init__(game, color="black")
        # self.game.renderer.logical_size = (1920, 1080)
        # in world space y is vertical, and x and z are horizontal
        # on screen with no rotation x is left-right, y is up-down, and z is depth
        self.camera = math3d.Camera(
            pygame.Vector3(),
            math3d.Quaternion(),
            pygame.Vector2(util_draw.RESOLUTION) / 2,
            pygame.Vector2(60, 60),  # TODO : FOV
            400,
            2000,
        )
        ship_rect = pygame.Rect(0, 0, 48, 32)
        ship_rect.center = self.game.screen_rect.center
        self.ship = gui3d.Ship(self, ship_rect)
        self.gui = [self.ship]
        self.sprites = []
        self.ship_overlay = self.game.loader.get_surface_scaled_to(
            "ship-inside.png", util_draw.RESOLUTION
        )
        self.static_sprites = sprite3d.StaticSpriteGroup(self, 10000, 6)
        sizes = ((16, 16), (9, 9), (5, 5), (2, 2))
        blue_textures = {
            size: self.game.loader.get_image("stars", f"blue{i + 1}")
            for i, size in enumerate(sizes)
        }
        blue_textures[(0, 0)] = pygame.Surface((0, 0)).convert()
        self.static_sprites.add_textures(
            "blue",
            blue_textures,
        )
        yellow_textures = {
            size: self.game.loader.get_image("stars", f"yellow{i + 1}")
            for i, size in enumerate(sizes)
        }
        yellow_textures[(0, 0)] = pygame.Surface((0, 0)).convert()
        self.static_sprites.add_textures(
            "yellow",
            yellow_textures,
        )
        self.planet_ids = {}
        planets = (("GeminiII", (0, 0, 1000)), ("Keergan", (0, 0, -1000)))
        for name, position in planets:
            planet_textures = {
                (size, size): AnimatedSurface(
                    self.game.loader.get_spritesheet(
                        f"planets/{name}{size}", (size, size)
                    )
                )
                for size in (6, 16, 32, 64, 128, 192)
            }
            self.static_sprites.add_textures(
                name,
                planet_textures,
            )
            self.planet_ids[name] = self.static_sprites.add_sprite(
                position, name, (128, 128)
            )

        for pos in numpy.random.uniform(
            low=-2000, high=2000, size=(10000 - len(planets), 3)
        ):
            self.static_sprites.add_sprite(
                tuple(pos), numpy.random.choice(["blue", "yellow"])
            )
        self.turn_speeds = {
            "up": 0,
            "down": 0,
            "left": 0,
            "right": 0,
        }
        self.turn_delta = 0.007
        self.max_turn_speed = 0.4
        self.forward_delta = 10
        self.min_forward_speed = 150
        self.max_forward_speed = 1000
        self.forward_speed = self.min_forward_speed

    def update(self, dt):
        pressed = self.game.input_queue.just_pressed
        if "quit" in pressed:
            self.game.quit()
        if "enter" in pressed:
            for name, id in self.planet_ids.items():
                rect = self.static_sprites.get_rect(id)
                if (
                    rect.width > 100
                    and self.screen_rect.contains(rect)
                    and self.static_sprites.screen_positions[id][2] > 0
                ):
                    print(f"entering {name}!")
                    self.game.load_map(name)
        held = self.game.input_queue.held
        if held["up"]:
            self.turn_speeds["up"] += self.turn_delta
            self.ship.up()
        else:
            self.turn_speeds["up"] -= self.turn_delta
        if held["down"]:
            self.turn_speeds["down"] += self.turn_delta
            self.ship.down()
        else:
            self.turn_speeds["down"] -= self.turn_delta
        if held["left"]:
            self.turn_speeds["left"] += self.turn_delta
            self.ship.left()
        else:
            self.turn_speeds["left"] -= self.turn_delta
        if held["right"]:
            self.turn_speeds["right"] += self.turn_delta
            self.ship.right()
        else:
            self.turn_speeds["right"] -= self.turn_delta
        if held["turbo_ship"]:
            self.forward_speed += self.forward_delta
            self.game.play_soundtrack("Lightspeed")
        else:
            self.forward_speed -= self.forward_delta
            self.game.play_soundtrack("SpaceshipMain")
        self.turn_speeds["up"] = pygame.math.clamp(
            self.turn_speeds["up"], 0, self.max_turn_speed
        )
        self.turn_speeds["down"] = pygame.math.clamp(
            self.turn_speeds["down"], 0, self.max_turn_speed
        )
        self.turn_speeds["left"] = pygame.math.clamp(
            self.turn_speeds["left"], 0, self.max_turn_speed
        )
        self.turn_speeds["right"] = pygame.math.clamp(
            self.turn_speeds["right"], 0, self.max_turn_speed
        )
        self.camera.rotation *= math3d.Quaternion(
            dt * self.turn_speeds["up"], (1, 0, 0)
        )
        self.camera.rotation *= math3d.Quaternion(
            -dt * self.turn_speeds["down"], (1, 0, 0)
        )
        self.camera.rotation *= math3d.Quaternion(
            -dt * self.turn_speeds["left"], (0, 1, 0)
        )
        self.camera.rotation *= math3d.Quaternion(
            dt * self.turn_speeds["right"], (0, 1, 0)
        )
        self.forward_speed = pygame.math.clamp(
            self.forward_speed, self.min_forward_speed, self.max_forward_speed
        )
        motion = pygame.Vector3(0, 0, self.forward_speed * dt)
        self.static_sprites.update(dt)
        self.camera.pos += self.camera.rotation * motion
        for sprite in self.gui:
            sprite.update(dt)
        return True

    def draw(self):
        self.static_sprites.dirty_draw(self.camera)
        projection_matrix = numpy.array(
            (
                (self.camera.near_z, 0, 0, 0),
                (0, self.camera.near_z, 0, 0),
                (
                    0,
                    0,
                    self.camera.far_z + self.camera.near_z,
                    -self.camera.far_z * self.camera.near_z,
                ),
                (0, 0, 1, 0),
            ),
            numpy.float64,
        )
        negated_rotation = -self.camera.rotation
        for sprite in self.sprites:
            # TODO: Proper FOV??
            # translate and rotate (relative position * relative rotation)
            relative_pos = negated_rotation * (sprite.pos - self.camera.pos)
            # scale (cheating)
            scale_factor = self.camera.near_z / relative_pos.z
            sprite.rect.width = sprite.width * scale_factor
            sprite.rect.height = sprite.height * scale_factor
            # project
            screen_pos = projection_matrix @ numpy.array(
                (relative_pos.x, relative_pos.y, relative_pos.z, 1)
            )
            screen_pos = (
                pygame.Vector3(screen_pos[0], screen_pos[1], screen_pos[2])
                / screen_pos[3]
            )
            # draw
            if self.camera.near_z <= screen_pos[2] <= self.camera.far_z:
                sprite.rect.center = screen_pos.xy + self.camera.center
                self.game.renderer.blit(sprite.image, sprite.rect)
        # TODO: GUI
        for sprite in self.gui:
            sprite.draw(self.game.window_surface)
