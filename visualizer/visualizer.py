import math
import os

from math import cos, sin, pi
from instructions import Direction

from typing import Iterator

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "True"
import pygame
from pygame.surface import Surface

SERVO_TIME_PER_60_DEG = 0.17
BASE_STEPS_PER_REVOLUTION: int = 200
MICRO_STEPS: int = 32

STP_P_REV: int = BASE_STEPS_PER_REVOLUTION * MICRO_STEPS
STP_P_DEG: float = STP_P_REV / 360
DEG_P_STEP: float = 360 / STP_P_REV


def generate_gradient(color1: tuple[int, int, int], color2: tuple[int, int, int], n: int) -> (
        Iterator)[tuple[int, int, int]]:
    for i in range(n):
        r = color1[0] + (color2[0] - color1[0]) * i / (n - 1)
        g = color1[1] + (color2[1] - color1[1]) * i / (n - 1)
        b = color1[2] + (color2[2] - color1[2]) * i / (n - 1)
        yield int(r), int(g), int(b)


class Arm:
    def __init__(self, origin, target_framerate: int, needle_length: int, screen: Surface):
        self.screen = screen

        self.origin = origin
        self.target_framerate = target_framerate

        self.needle_length = needle_length
        self.arm_angle = 0

        self.arm_movement_task = None
        self.target_arm_angle = self.arm_angle

    def _arm_to_angle(self, angle):
        self.target_arm_angle = angle
        difference = self.arm_angle - angle
        seconds = abs(difference) * (SERVO_TIME_PER_60_DEG / 60)
        frames = int(self.target_framerate * seconds)

        if frames == 0:
            return

        step_size = difference / frames
        for _ in range(frames):
            self.arm_angle -= step_size
            yield

    def arm_to_angle(self, angle):
        self.arm_movement_task = self._arm_to_angle(angle)

    def update(self):
        if self.arm_movement_task:
            try:
                next(self.arm_movement_task)
            except StopIteration:
                self.arm_movement_task = None

        pygame.draw.circle(self.screen, (0, 0, 0), self.origin, 4)

        offset_length = self.needle_length * math.sin(self.arm_angle * math.pi / 180)

        point_a = self.origin
        point_b = self.origin[0] + offset_length, self.origin[1]
        pygame.draw.line(self.screen, (0, 0, 255), point_a, point_b, width=2)
        pygame.draw.circle(self.screen, (255, 0, 0), point_b, 4)


class Table:
    def __init__(self, table_origin: tuple[int, int], table_radius: int, pin_count: int, screen: Surface):
        self.origin = table_origin
        self.radius = table_radius
        self.screen = screen

        self.pin_count = pin_count
        self.table_angle = 180

        self.error = 0
        self.current_angle = 0

        self.move_tbl_task = None

    def update(self):
        pygame.draw.circle(self.screen, (255, 255, 255), self.origin, self.radius)

        if self.move_tbl_task is not None:
            try:
                next(self.move_tbl_task)
            except StopIteration:
                self.move_tbl_task = None

        # draw the pins:
        theta = self.table_angle
        spacing = 360 / self.pin_count
        gradient = generate_gradient((255, 0, 0), (0, 255, 0), self.pin_count)
        for i in range(0, self.pin_count):
            x1 = self.radius * cos(theta * (pi / 180))
            y1 = self.radius * sin(theta * (pi / 180))
            x, y = map(int, (self.origin[0] + x1, self.origin[1] + y1))

            pygame.draw.circle(self.screen, next(gradient), (x, y), radius=2)

            theta += spacing

    def move_tbl_degrees(self, degrees: int, direction: int):
        self.move_tbl_task = self._move_tbl_degrees(degrees, direction)

    def step(self, direction: int):
        if direction == Direction.CW:
            self.table_angle -= DEG_P_STEP
            return
        self.table_angle += DEG_P_STEP

    def _move_tbl_degrees(self, degrees: int, direction: int):
        step = lambda: self.step(direction)

        adjusted_degrees = degrees - self.error

        target_steps = (adjusted_degrees / 360.0) * STP_P_REV

        steps_to_move = int(target_steps)

        best_steps = steps_to_move
        min_error = float('inf')

        for steps in (steps_to_move, steps_to_move - 1):
            actual_rotation = (steps / STP_P_REV) * 360.0
            error_degrees = adjusted_degrees - actual_rotation

            if direction == Direction.CW:
                cumulative_error = self.error - error_degrees
            else:
                cumulative_error = self.error + error_degrees

            if abs(cumulative_error) < abs(min_error):
                min_error = cumulative_error
                best_steps = steps

        steps_to_move = best_steps
        for _ in range(abs(steps_to_move)):
            dir_val = -1 if Direction.CW else 1
            self.current_angle = (self.current_angle + dir_val * DEG_P_STEP) % 360

            yield step()

        actual_rotation = (steps_to_move / STP_P_REV) * 360.0

        error_degrees = adjusted_degrees - actual_rotation
        if direction == Direction.CW:
            self.error -= error_degrees
        else:
            self.error += error_degrees


class Visualizer:
    def __init__(self, width: int, height: int, pin_count: int = 150, scale: int = 1):
        self.running = True

        self.needle_length = 60 * scale
        self.table_radius = 150 * scale

        self.pin_count = pin_count

        self.target_framerate = 240
        self.last_framerate = self.target_framerate

        self.width = width * scale
        self.height = height * scale
        self.center = (int(self.width / 2), int(self.height / 2))

        self.arm_movement_task = None
        self.arm_angle = 10
        self.arm_offset = -10
        self.target_arm_angle = self.arm_angle

        self.screen = pygame.display.set_mode([self.width, self.height])
        self.clock = pygame.time.Clock()

        arm_origin = (self.width // 2 - self.table_radius, self.height // 2)
        self.arm = Arm(origin=(arm_origin[0] + self.arm_offset, arm_origin[1]), target_framerate=self.target_framerate,
                       needle_length=self.needle_length, screen=self.screen)
        self.table = Table(table_origin=self.center, table_radius=self.table_radius, screen=self.screen,
                           pin_count=self.pin_count)

    def update_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def update_background(self):
        self.screen.fill((200, 200, 200))

    def update(self):
        self.update_events()
        self.update_background()

        self.table.update()
        self.arm.update()

        pygame.display.flip()

    def run(self):
        try:
            while self.running:
                self.update()
                self.last_framerate = self.clock.get_fps()

                self.clock.tick(self.target_framerate)

            pygame.quit()
        except Exception as e:
            print(e)