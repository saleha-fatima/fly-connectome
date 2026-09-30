"""Interactive looming and escape simulation using MaleCNS circuit weights."""

from __future__ import annotations

import random

import pygame

from behavior import BehaviorPhase, BehaviorSnapshot, FlyBehavior
from looming import LoomSample, LoomingTrial
from neural_model import EscapeCircuit, NeuralActivity
from vision import ThreatSignal, sense_swatter_arrival


WIDTH = 1180
HEIGHT = 700
PANEL_WIDTH = 440
ARENA_WIDTH = WIDTH - PANEL_WIDTH
BACKGROUND = (245, 245, 240)
PANEL_BACKGROUND = (230, 234, 232)
TEXT = (35, 40, 42)
MUTED = (115, 122, 120)
RED = (205, 55, 55)
BLUE = (55, 115, 185)
PURPLE = (130, 80, 175)
GREEN = (45, 145, 92)
LEFT_FIELD = (38, 145, 165)
RIGHT_FIELD = (220, 135, 45)


class FlyEscapeGame:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("MaleCNS Fly Escape Experiment")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 22)

        self.fly = pygame.Vector2(ARENA_WIDTH / 2, HEIGHT / 2)
        self.fly_velocity = pygame.Vector2()
        self.swatter = pygame.Vector2(pygame.mouse.get_pos())
        self.signal = ThreatSignal(0.0, 0.0, 0.0, 0.0, 0.0)
        self.circuit = EscapeCircuit()
        self.activity = NeuralActivity()
        self.behavior = FlyBehavior()
        self.behavior_snapshot = BehaviorSnapshot()
        self.trial = LoomingTrial()
        self.loom_sample = self.trial.sample()
        self.trial_origin = self.fly.copy()
        self.mode = "biological"
        self.tumble_angle = 0.0
        self.escapes = 0

    def run(self) -> None:
        running = True
        while running:
            dt = min(self.clock.tick(60) / 1000.0, 0.05)
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
                ):
                    running = False
                elif event.type == pygame.KEYDOWN:
                    self._handle_key(event.key)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if event.pos[0] >= ARENA_WIDTH:
                        self._handle_panel_click(event.pos)
                    elif self.mode == "biological":
                        self._start_trial()

            self._update(dt)
            self._draw()

        pygame.quit()

    def _handle_key(self, key: int) -> None:
        lesions = {
            pygame.K_1: "LC4",
            pygame.K_2: "LPLC2",
            pygame.K_3: "DNp01",
        }
        if key in lesions:
            self.circuit.toggle(lesions[key])
            self.behavior.reset()
        elif key == pygame.K_r:
            self._reset_experiment()
        elif key == pygame.K_SPACE and self.mode == "biological":
            self._start_trial()
        elif key in {pygame.K_a, pygame.K_d}:
            self.trial.configure(side="left" if key == pygame.K_a else "right")
            self._prepare_new_trial()
        elif key in {pygame.K_s, pygame.K_f}:
            self.trial.configure(speed_name="slow" if key == pygame.K_s else "fast")
            self._prepare_new_trial()
        elif key == pygame.K_m:
            self.mode = "debug" if self.mode == "biological" else "biological"
            self._reset_experiment(restore_lesions=False)

    def _handle_panel_click(self, position: tuple[int, int]) -> None:
        for neuron_class, rect in self._control_rects().items():
            if rect.collidepoint(position):
                self.circuit.toggle(neuron_class)
                self.behavior.reset()
                return

    def _prepare_new_trial(self) -> None:
        if self.mode == "biological":
            self.trial.reset()
            self.loom_sample = self.trial.sample()
            self.circuit.reset_activity()
            self.behavior.reset()

    def _start_trial(self) -> None:
        self.fly.update(ARENA_WIDTH / 2, HEIGHT / 2)
        self.fly_velocity.update(0, 0)
        self.tumble_angle = 0.0
        self.circuit.reset_activity()
        self.behavior.reset()
        self.trial_origin = self.fly.copy()
        self.loom_sample = self.trial.start()

    def _reset_experiment(self, restore_lesions: bool = True) -> None:
        if restore_lesions:
            self.circuit.reset_all()
        else:
            self.circuit.reset_activity()
        self.behavior.reset()
        self.behavior_snapshot = self.behavior.snapshot
        self.trial.reset()
        self.loom_sample = self.trial.sample()
        self.fly.update(ARENA_WIDTH / 2, HEIGHT / 2)
        self.fly_velocity.update(0, 0)
        self.tumble_angle = 0.0

    def _update(self, dt: float) -> None:
        if self.mode == "biological":
            self.loom_sample = self.trial.update(dt)
            self.signal = self.loom_sample.signal
            self.swatter = self._loom_swatter_position()
        else:
            self.swatter.update(pygame.mouse.get_pos())
            self.swatter.x = min(self.swatter.x, ARENA_WIDTH)
            self.signal = sense_swatter_arrival(tuple(self.fly), tuple(self.swatter))

        self.activity = self.circuit.update(self.signal, dt)
        self.behavior_snapshot = self.behavior.update(self.activity, self.signal, dt)

        if self.behavior_snapshot.launch:
            direction = pygame.Vector2(
                self.behavior_snapshot.escape_x, self.behavior_snapshot.escape_y
            )
            if direction.length_squared() == 0:
                direction.update(random.choice((-1, 1)), 0)
            direction.normalize_ip()
            self.fly_velocity = direction * self.behavior_snapshot.launch_speed
            self.escapes += 1

        moving_escape = self.behavior_snapshot.phase in {
            BehaviorPhase.JUMPING,
            BehaviorPhase.AIRBORNE,
        }
        if moving_escape:
            damping = 0.995 if self.behavior_snapshot.tumbling else 0.985
            self.fly_velocity *= damping
            speed_limit = 430
        else:
            wander_scale = 5 if self.behavior_snapshot.phase == BehaviorPhase.PREPARING else 30
            wander = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
            self.fly_velocity += wander * wander_scale * dt
            self.fly_velocity *= 0.94
            speed_limit = 90

        if self.fly_velocity.length() > speed_limit:
            self.fly_velocity.scale_to_length(speed_limit)
        self.fly += self.fly_velocity * dt

        if self.behavior_snapshot.tumbling:
            self.tumble_angle = (self.tumble_angle + 720 * dt) % 360
        else:
            self.tumble_angle *= 0.85

        margin = 45
        if self.fly.x < margin or self.fly.x > ARENA_WIDTH - margin:
            self.fly_velocity.x *= -0.55
        if self.fly.y < margin or self.fly.y > HEIGHT - margin:
            self.fly_velocity.y *= -0.55
        self.fly.x = max(margin, min(ARENA_WIDTH - margin, self.fly.x))
        self.fly.y = max(margin, min(HEIGHT - margin, self.fly.y))

    def _loom_swatter_position(self) -> pygame.Vector2:
        offset = 25 + 285 * (1.0 - self.loom_sample.progress)
        return self.trial_origin + pygame.Vector2(self.trial.side_sign * offset, 0)

    def _draw(self) -> None:
        self.screen.fill(BACKGROUND)
        pygame.draw.rect(
            self.screen, PANEL_BACKGROUND, (ARENA_WIDTH, 0, PANEL_WIDTH, HEIGHT)
        )
        pygame.draw.line(
            self.screen, (190, 195, 193), (ARENA_WIDTH, 0), (ARENA_WIDTH, HEIGHT), 2
        )

        self._draw_scene_status()
        self._draw_fly()
        self._draw_swatter()
        self._draw_panel()
        pygame.display.flip()

    def _draw_scene_status(self) -> None:
        if self.mode == "biological":
            instructions = (
                "SPACE or arena click: start trial   A/D: left/right   S/F: slow/fast",
                "M: debug pulse   1/2/3: lesions   R: reset",
            )
            if self.loom_sample.running:
                pygame.draw.line(
                    self.screen, RED, self.swatter, self.trial_origin, 2
                )
                label = self.font.render("EXPANDING LOOM", True, RED)
                self.screen.blit(
                    label,
                    (
                        int(self.trial_origin.x - label.get_width() / 2),
                        int(self.trial_origin.y - 88),
                    ),
                )
        else:
            instructions = (
                "DEBUG PULSE: move the mouse swatter onto the fly",
                "M: biological loom   1/2/3: lesions   R: reset",
            )
            if self.signal.is_dangerous:
                pygame.draw.line(self.screen, RED, self.swatter, self.fly, 2)

        for index, line in enumerate(instructions):
            self.screen.blit(
                self.small_font.render(line, True, MUTED), (18, 16 + index * 22)
            )

    def _draw_fly(self) -> None:
        sprite = pygame.Surface((110, 110), pygame.SRCALPHA)
        cx, cy = 55, 54
        prep = self.behavior_snapshot.preparation_progress
        away = pygame.Vector2(
            self.behavior_snapshot.escape_x, self.behavior_snapshot.escape_y
        )
        draw_center = self.fly + away * (8 * prep if self.behavior_snapshot.phase == BehaviorPhase.PREPARING else 0)

        if self.behavior_snapshot.wings_raised:
            pygame.draw.ellipse(sprite, (175, 205, 220, 220), (15, 12, 34, 45))
            pygame.draw.ellipse(sprite, (175, 205, 220, 220), (61, 12, 34, 45))
        else:
            pygame.draw.ellipse(sprite, (190, 215, 225, 210), (18, 48, 32, 37))
            pygame.draw.ellipse(sprite, (190, 215, 225, 210), (60, 48, 32, 37))

        pygame.draw.ellipse(sprite, (45, 43, 37), (46, 49, 18, 39))
        pygame.draw.circle(sprite, (55, 51, 43), (cx, cy - 9), 15)
        left_eye = (cx - 8, cy - 14)
        right_eye = (cx + 8, cy - 14)
        pygame.draw.circle(sprite, (190, 45, 35), left_eye, 7)
        pygame.draw.circle(sprite, (190, 45, 35), right_eye, 7)
        pygame.draw.circle(sprite, (25, 20, 18), left_eye, 3)
        pygame.draw.circle(sprite, (25, 20, 18), right_eye, 3)

        leg_extension = 12 + int(12 * prep)
        for side in (-1, 1):
            pygame.draw.line(sprite, TEXT, (cx + side * 6, cy + 12), (cx + side * 25, cy + 22), 2)
            pygame.draw.line(
                sprite,
                TEXT,
                (cx + side * 5, cy + 19),
                (cx + side * (22 + leg_extension), cy + 38),
                2,
            )

        if self.behavior_snapshot.tumbling:
            sprite = pygame.transform.rotate(sprite, self.tumble_angle)
        rect = sprite.get_rect(center=(int(draw_center.x), int(draw_center.y)))
        self.screen.blit(sprite, rect)

        if not self.behavior_snapshot.tumbling:
            self.screen.blit(
                self.small_font.render("L", True, LEFT_FIELD),
                (int(draw_center.x - 22), int(draw_center.y - 39)),
            )
            self.screen.blit(
                self.small_font.render("R", True, RIGHT_FIELD),
                (int(draw_center.x + 13), int(draw_center.y - 39)),
            )

        phase_label = self.small_font.render(
            self.behavior_snapshot.phase.value.upper(),
            True,
            RED if self.behavior_snapshot.phase != BehaviorPhase.WANDERING else MUTED,
        )
        self.screen.blit(
            phase_label,
            (int(draw_center.x - phase_label.get_width() / 2), int(draw_center.y + 60)),
        )

    def _draw_swatter(self) -> None:
        if self.mode == "biological":
            size = int(16 + min(64, self.loom_sample.angular_size_deg * 0.48))
        else:
            size = 42
        x, y = map(int, self.swatter)
        half = size // 2
        pygame.draw.line(
            self.screen,
            RED,
            (x + half * 0.75, y + half * 0.75),
            (x + half + 42, y + half + 42),
            max(4, size // 7),
        )
        pygame.draw.rect(
            self.screen,
            RED,
            (x - half, y - half, size, size),
            max(2, size // 11),
            border_radius=4,
        )
        for fraction in (-0.5, 0.0, 0.5):
            offset = int(half * fraction)
            pygame.draw.line(
                self.screen, RED, (x - half + 4, y + offset), (x + half - 4, y + offset), 1
            )
            pygame.draw.line(
                self.screen, RED, (x + offset, y - half + 4), (x + offset, y + half - 4), 1
            )

    def _draw_panel(self) -> None:
        x = ARENA_WIDTH + 24
        title = "BIOLOGICAL LOOM" if self.mode == "biological" else "DEBUG PULSE"
        self.screen.blit(self.font.render(title, True, TEXT), (x, 14))

        if self.mode == "biological":
            if self.loom_sample.running:
                trial_state = "RUNNING"
                state_color = RED
            elif self.loom_sample.completed:
                trial_state = "COMPLETE — press SPACE to repeat"
                state_color = GREEN
            else:
                trial_state = "READY — press SPACE"
                state_color = MUTED
            self.screen.blit(self.small_font.render(trial_state, True, state_color), (x, 43))
            settings = (
                f"{self.trial.side.upper()} attack   {self.trial.speed_name.upper()} "
                f"{self.trial.speed_mm_s:.0f} mm/s   l/v {self.trial.l_over_v_ms:.0f} ms"
            )
            self.screen.blit(self.small_font.render(settings, True, TEXT), (x, 65))
            metrics = (
                f"Angular size {self.loom_sample.angular_size_deg:5.1f}°",
                f"Expansion {self.loom_sample.angular_velocity_deg_s:5.0f}°/s",
                f"Time to collision {self.loom_sample.time_to_collision_s:4.2f}s",
            )
            for index, line in enumerate(metrics):
                self.screen.blit(self.small_font.render(line, True, TEXT), (x, 88 + 20 * index))
        else:
            state = "THREAT PRESENT" if self.signal.is_dangerous else "Move swatter onto fly"
            self.screen.blit(self.small_font.render(state, True, RED if self.signal.is_dangerous else MUTED), (x, 48))

        self._meter(x, 151, "LC4 velocity feature", self.signal.expansion_velocity, BLUE)
        self._meter(x, 192, "LPLC2 size feature", self.signal.angular_size, PURPLE)

        self.screen.blit(self.font.render("NEURAL ACTIVITY", True, TEXT), (x, 242))
        self._neural_meter(x, 274, "LC4", self.activity.lc4_left, self.activity.lc4_right, BLUE)
        self._neural_meter(x, 315, "LPLC2", self.activity.lplc2_left, self.activity.lplc2_right, PURPLE)
        self._neural_meter(x, 356, "DNp01", self.activity.dnp01_left, self.activity.dnp01_right, RED)
        output_status = "SPIKE/ESCAPE" if self.activity.escape_active else "below threshold"
        self.screen.blit(
            self.small_font.render(
                f"DNp01 output {self.activity.escape_output:.2f} — {output_status}",
                True,
                RED if self.activity.escape_active else MUTED,
            ),
            (x, 397),
        )

        self.screen.blit(self.font.render("OBSERVED ACTION", True, TEXT), (x, 428))
        self.screen.blit(
            self.small_font.render(f"Phase: {self.behavior_snapshot.phase.value}", True, TEXT),
            (x, 458),
        )
        self.screen.blit(
            self.small_font.render(f"Program: {self.behavior_snapshot.program}", True, TEXT),
            (x, 480),
        )
        self._meter(
            x,
            505,
            "Postural preparation",
            self.behavior_snapshot.preparation_progress,
            GREEN,
        )

        self.screen.blit(self.font.render("LESION CONTROLS", True, TEXT), (x, 556))
        for neuron_class, rect in self._control_rects().items():
            disabled = neuron_class in self.circuit.disabled
            pygame.draw.rect(self.screen, TEXT, rect, 2, border_radius=2)
            if disabled:
                pygame.draw.line(self.screen, RED, rect.topleft, rect.bottomright, 3)
                pygame.draw.line(self.screen, RED, rect.topright, rect.bottomleft, 3)
            color = RED if disabled else TEXT
            self.screen.blit(
                self.small_font.render(f"Disable {neuron_class}", True, color),
                (rect.right + 10, rect.y - 1),
            )

    def _control_rects(self) -> dict[str, pygame.Rect]:
        x = ARENA_WIDTH + 27
        return {
            "LC4": pygame.Rect(x, 590, 17, 17),
            "LPLC2": pygame.Rect(x, 619, 17, 17),
            "DNp01": pygame.Rect(x, 648, 17, 17),
        }

    def _neural_meter(
        self,
        x: int,
        y: int,
        label: str,
        left: float,
        right: float,
        color: tuple[int, int, int],
    ) -> None:
        disabled = label in self.circuit.disabled
        suffix = " [OFF]" if disabled else f"   L {left:.2f}  R {right:.2f}"
        self._meter(x, y, label + suffix, max(left, right), color, disabled)

    def _meter(
        self,
        x: int,
        y: int,
        label: str,
        value: float,
        color: tuple[int, int, int],
        disabled: bool = False,
    ) -> None:
        bar_width = 380
        label_color = MUTED if disabled else TEXT
        self.screen.blit(self.small_font.render(label, True, label_color), (x, y))
        pygame.draw.rect(
            self.screen, (200, 206, 203), (x, y + 21, bar_width, 13), border_radius=3
        )
        pygame.draw.rect(
            self.screen,
            MUTED if disabled else color,
            (x, y + 21, int(bar_width * max(0.0, min(1.0, value))), 13),
            border_radius=3,
        )
