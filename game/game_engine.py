import pygame
from .bird import Bird
from .pipe import Pipe

# Game Engine

WHITE = (255, 255, 255)
GREEN = (0, 150, 0)
YELLOW = (255, 220, 0)

# Frames to ignore input after dying, so a frantic last flap
# doesn't instantly pick a menu option.
INPUT_DELAY_FRAMES = 30

# Pixel distance between consecutive pipes is kept the same on every
# difficulty: spawn interval (frames) = PIPE_SPACING / speed.
PIPE_SPACING = 360

DIFFICULTIES = {
    "Easy":   {"speed": 3, "gap": 190},
    "Medium": {"speed": 4, "gap": 150},
    "Hard":   {"speed": 6, "gap": 120},
}
DIFFICULTY_KEYS = {
    pygame.K_1: "Easy",
    pygame.K_2: "Medium",
    pygame.K_3: "Hard",
}


class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.font = pygame.font.SysFont("Arial", 30)
        self.big_font = pygame.font.SysFont("Arial", 56, bold=True)

        self.difficulty = "Medium"
        self.reset(self.difficulty)

    def reset(self, difficulty):
        """Start a fresh run at the given difficulty."""
        self.difficulty = difficulty
        cfg = DIFFICULTIES[difficulty]
        self.pipe_speed = cfg["speed"]
        self.pipe_gap = cfg["gap"]
        self.pipe_interval = PIPE_SPACING // self.pipe_speed  # frames between spawns

        self.bird = Bird(self.width // 4, self.height // 2)
        self._spawn_timer = 0
        self.pipes = [self._new_pipe(self.width + 100)]

        self.score = 0
        self.game_over = False
        self.game_over_timer = 0

    def _new_pipe(self, x):
        return Pipe(x, self.height, gap=self.pipe_gap, speed=self.pipe_speed)

    def _end_game(self):
        self.game_over = True

    def handle_event(self, event):
        if self.game_over:
            self._handle_game_over_event(event)
            return

        # Flap is edge-triggered (KEYDOWN / MOUSEBUTTONDOWN), not held.
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self.bird.flap()
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.bird.flap()

    def _handle_game_over_event(self, event):
        if self.game_over_timer < INPUT_DELAY_FRAMES:
            return
        if event.type != pygame.KEYDOWN:
            return
        if event.key in DIFFICULTY_KEYS:
            self.reset(DIFFICULTY_KEYS[event.key])
        elif event.key in (pygame.K_q, pygame.K_ESCAPE):
            # Ask main loop to exit cleanly.
            pygame.event.post(pygame.event.Event(pygame.QUIT))

    def handle_input(self):
        # Reserved for continuously-held-key input; flapping is handled
        # in handle_event instead, so there's nothing to poll here.
        pass

    def update(self):
        if self.game_over:
            self.game_over_timer += 1
            return

        self.bird.update()

        if self.bird.y - self.bird.radius <= 0 or self.bird.y + self.bird.radius >= self.height:
            self._end_game()
            return

        self._spawn_timer += 1
        if self._spawn_timer >= self.pipe_interval:
            self._spawn_timer = 0
            self.pipes.append(self._new_pipe(self.width))

        for pipe in self.pipes:
            pipe.move()

            # Circle-vs-rect test against both pipe halves, so any overlap
            # of the bird's body with a pipe (including edges and corners)
            # counts as a hit regardless of pipe speed.
            if (self.bird.collides_with_rect(pipe.top_rect())
                    or self.bird.collides_with_rect(pipe.bottom_rect())):
                self._end_game()
                return

            if not pipe.scored and pipe.x + pipe.width < self.bird.x:
                pipe.scored = True
                self.score += 1

        self.pipes = [p for p in self.pipes if not p.off_screen()]

    def _draw_centered(self, screen, font, text, y, color=WHITE):
        surf = font.render(text, True, color)
        screen.blit(surf, surf.get_rect(center=(self.width // 2, y)))

    def _render_game_over(self, screen):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        cy = self.height // 2
        self._draw_centered(screen, self.big_font, "GAME OVER", cy - 140)
        self._draw_centered(screen, self.font, f"Final Score: {self.score}", cy - 70)

        if self.game_over_timer >= INPUT_DELAY_FRAMES:
            self._draw_centered(screen, self.font, "Play again? Choose difficulty:", cy, YELLOW)
            self._draw_centered(screen, self.font, "1 - Easy", cy + 50)
            self._draw_centered(screen, self.font, "2 - Medium", cy + 90)
            self._draw_centered(screen, self.font, "3 - Hard", cy + 130)
            self._draw_centered(screen, self.font, "Q / Esc - Exit", cy + 190)

    def render(self, screen):
        for pipe in self.pipes:
            pygame.draw.rect(screen, GREEN, pipe.top_rect())
            pygame.draw.rect(screen, GREEN, pipe.bottom_rect())

        pygame.draw.circle(screen, WHITE, (int(self.bird.x), int(self.bird.y)), self.bird.radius)

        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (10, 10))

        mode_text = self.font.render(self.difficulty, True, WHITE)
        screen.blit(mode_text, (self.width - mode_text.get_width() - 10, 10))

        if self.game_over:
            self._render_game_over(screen)
