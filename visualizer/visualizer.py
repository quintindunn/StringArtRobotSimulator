import math
import os
import time

from math import cos, sin, pi
from instructions import Direction

from typing import Iterator

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "True"
import pygame
from pygame.surface import Surface

pygame.init()

SERVO_TIME_PER_60_DEG = 0.17
BASE_STEPS_PER_REVOLUTION: int = 200
MICRO_STEPS: int = 8

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
        self.table_angle = 0

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

    def move_tbl_degrees(self, angle: float):
        self.move_tbl_task = self._move_tbl_degrees(angle)

    @staticmethod
    def calculate_relative_rotation(angle_1: float, angle_2: int) -> tuple[float, int | None]:
        angle_1 %= 360
        angle_2 %= 360

        theta = ((angle_2 - angle_1) + 180) % 360 - 180
        direction = Direction.CCW if theta > 0 else Direction.CW if theta < 0 else None

        return theta, direction

    def step(self, direction: int):
        if direction == Direction.CW:
            self.table_angle += DEG_P_STEP
        else:
            self.table_angle -= DEG_P_STEP

        self.table_angle %= 360

    def _move_tbl_degrees(self, angle: float):
        angle_diff = (angle - self.table_angle) % 360

        if angle_diff > 180:
            steps = (360 - angle_diff) / DEG_P_STEP
            direction = Direction.CCW
        else:
            steps = angle_diff / DEG_P_STEP
            direction = Direction.CW

        for _ in range(round(steps)):
            self.step(direction)
            yield


class Visualizer:
    def __init__(self, width: int, height: int, pin_count: int = 150, scale: int = 1):
        self.running = True

        self.width = width * scale
        self.height = height * scale
        self.center = (int(self.width / 2), int(self.height / 2))

        self.arm_offset = -10
        self.needle_length = 60 * scale
        self.table_radius = 150 * scale
        self.pin_count = pin_count

        self.target_framerate = 0
        self.last_framerate = self.target_framerate

        self._current_command = ""

        self.screen = pygame.display.set_mode([self.width, self.height])
        self.clock = pygame.time.Clock()
        self.arm = Arm(origin=(self.width // 2 - self.table_radius + self.arm_offset, self.height // 2),
                       target_framerate=self.target_framerate, needle_length=self.needle_length, screen=self.screen)
        self.table = Table(table_origin=self.center, table_radius=self.table_radius, screen=self.screen,
                           pin_count=self.pin_count)

    def set_current_command(self, command: str):
        self._current_command = command

    def draw_text(self, origin: tuple[int, int], text: str, size: int = 20, color: tuple[int, int, int] = (0, 0, 0)):
        font = pygame.font.SysFont("Arial", size)
        blit = font.render(text, True, color)
        self.screen.blit(blit, origin)

    def draw_text_centered(self, origin: tuple[int, int], text: str, size: int = 20,
                           color: tuple[int, int, int] = (0, 0, 0)):
        font = pygame.font.SysFont("Arial", size)
        blit = font.render(text, True, color)
        text_rect = blit.get_rect(center=origin)  # Center the text around the origin
        self.screen.blit(blit, text_rect)

    def update_text(self):
        self.draw_text((0, 0), "StringArtBot", size=20)

        command_origin = self.center[0], self.center[1] - self.table_radius - 65
        self.draw_text_centered(command_origin, f"Current Command")
        command_origin = self.center[0], self.center[1] - self.table_radius - 40
        self.draw_text_centered(command_origin, f"{self._current_command}")

        self.draw_text((0, 40), f"FPS: {self.last_framerate:.2f}", size=20)

        self.draw_text((0, 80), f"Table Angle: {self.table.table_angle:.2f}", size=20)
        self.draw_text((0, 100), f"Arm Angle: {self.arm.arm_angle:.2f}", size=20)


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

        self.update_text()

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
