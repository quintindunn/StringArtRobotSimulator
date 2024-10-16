from pygame.font import SysFont
from util import generate_gradient

COLOR = tuple[int,  int, int]

# The title of the PyGame Window
WIN_TITLE: str = "StringArtBot Simulator"

# The Title displayed in the top left
DISP_TITLE: str = "StringArtBot"

# Whether to show the FPS
SHOW_FPS: bool = True

# Whether to show the table and arm angle
SHOW_ANGLES: bool = True

# The color of the text displayed
TEXT_COLOR: COLOR = (0, 0, 0)

# The font size for the text
FONT_SIZE: int = 20

# The font used for the text
FONT_NAME = "Arial"

# The padding from the sides for the text
TEXT_PADDING: int = 10

# The offset from the center for the text displaying the currently executing command.
COMMAND_TEXT_OFFSET: int = -65

# The colors used in the gradient used to distinguish between the pins
PIN_GRADIENT_COLORS: tuple[COLOR, COLOR] = ((255, 0, 0), (0, 255, 0))

# The color of the board/table
BOARD_COLOR: COLOR = (255, 255, 255)

# The background color
BACKGROUND_COLOR: COLOR = (200, 200, 200)

# The color of the circle showing the pivot of the arm
ARM_ORIGIN_COLOR: COLOR = (0, 0, 0)

# The color of the thread represented in the arm.
ARM_THREAD_TRAVEL_COLOR: COLOR = (0, 0, 255)

# The color of the head of the arm (where the arm is pivoted to)
ARM_HEAD_COLOR: COLOR = (255, 0, 0)

# The dimensions of the window
WIN_HEIGHT: int = 500
WIN_WIDTH: int = 500

# The offset of the arm from the edge of the table
ARM_OFFSET: int = -10

# The length of the needle/arm
NEEDLE_LENGTH: int = 60

# The radius of the table
TABLE_RADIUS: int = 150

# The number of pins on the table
PIN_COUNT: int = 150

# The amount of time it takes for the servo to turn 60 degrees.
SERVO_TIME_PER_60_DEG: float = 0.17

# The steps per revolution of the stepper motor
BASE_STEPS_PER_REVOLUTION: int = 200

# The amount of micro-steps per step (min: 1)
MICRO_STEPS: int = 8

# Calculation for the steps per revolution
STP_P_REV: int = BASE_STEPS_PER_REVOLUTION * MICRO_STEPS

# The amount of steps per degree
STP_P_DEG: float = STP_P_REV / 360

# The degrees per step (step angle)
DEG_P_STEP: float = 360 / STP_P_REV

# GENERATORS (DO NOT CHANGE UNLESS YOU KNOW WHAT YOU'RE DOING)

# The font generator
FONT = lambda size: SysFont(FONT_NAME, size=FONT_SIZE)

# The color gradient generator used for coloring the pins
PIN_GRADIENT = lambda pin_count: generate_gradient(PIN_GRADIENT_COLORS[0], PIN_GRADIENT_COLORS[1], pin_count)
