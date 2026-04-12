import pygame
import sys

CONFIG = {
    'rows': 6,
    'cols': 7,
    'cell_size': 100,
    'player_colors': {
        1: (220, 50, 50),     # red
        2: (250, 220, 50)     # yellow
    },
    'bg_color': (30, 80, 180), # blue
    'empty_color': (15, 15, 15) # black
}

# The directions a winning line can take (dx, dy)
WIN_VECTORS = [(0, 1), (1, 0), (1, 1), (1, -1)]

# The Connect4Match class handles the game state and core logic,
# including the board representation, move validation, and win detection.
class Connect4Match:
    # empty game board, current player, and win variables.
    def __init__(self):
        self.grid = [[0 for _ in range(CONFIG['cols'])] for _ in range(CONFIG['rows'])]
        self.active_player = 1
        self.winner = None
        self.is_finished = False

    def get_cell(self, r, c):
        return self.grid[r][c] # return specific row and column

    def can_play_in_column(self, col):
        return self.grid[0][col] == 0 # check if top of col is  empty

    def find_lowest_empty_row(self, col):
        for r in range(CONFIG['rows'] - 1, -1, -1):
            if self.grid[r][col] == 0:
                return r
        return None # finds lowest empty spot in col

    # excute move and checks for win
    def make_play(self, col):
        if self.is_finished or not self.can_play_in_column(col):
            return False

        r = self.find_lowest_empty_row(col)
        self.grid[r][col] = self.active_player
        
        if self._detect_victory(self.active_player):
            self.winner = self.active_player
            self.is_finished = True
        else:
            self.active_player = 3 - self.active_player # Toggle 1 and 2
            
        return True 

    # scans board for a winning move
    def _detect_victory(self, player_id):
        for row in range(CONFIG['rows']):
            for col in range(CONFIG['cols']):
                if self.grid[row][col] == player_id:
                    for dx, dy in WIN_VECTORS:
                        if self._check_line(row, col, dx, dy, player_id):
                            return True
        return False

    # check is 4 in a row
    def _check_line(self, start_r, start_c, dr, dc, player_id):
        r, c = start_r, start_c
        for _ in range(4):
            if r < 0 or r >= CONFIG['rows'] or c < 0 or c >= CONFIG['cols']:
                return False
            if self.grid[r][c] != player_id:
                return False
            r += dr
            c += dc
        return True

# The GameWindow class manages the Pygame graphical interface,
# rendering the board, handling user inputs, and updating the display.
class GameWindow:
    def __init__(self):
        pygame.init()
        self.width = CONFIG['cols'] * CONFIG['cell_size']
        self.height = (CONFIG['rows'] + 1) * CONFIG['cell_size']
        self.display_surface = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Connect 4 - Unique Edition")
        self.game = Connect4Match()
        self.font = pygame.font.SysFont("Verdana", 60, bold=True)

    def run(self):
        self._render()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if not self.game.is_finished:
                    if event.type == pygame.MOUSEMOTION:
                        self._draw_tracker(event.pos[0])
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        col_idx = event.pos[0] // CONFIG['cell_size']
                        if self.game.make_play(col_idx):
                            self._render()
                            if self.game.is_finished:
                                self._show_victory_message()
                                pygame.display.update()
                                pygame.time.wait(3000)

    def _draw_tracker(self, mouse_x):
        pygame.draw.rect(self.display_surface, CONFIG['empty_color'], (0, 0, self.width, CONFIG['cell_size']))
        center_x = min(max(mouse_x, CONFIG['cell_size'] // 2), self.width - CONFIG['cell_size'] // 2)
        radius = int(CONFIG['cell_size'] * 0.45)
        color = CONFIG['player_colors'][self.game.active_player]
        pygame.draw.circle(self.display_surface, color, (center_x, int(CONFIG['cell_size'] / 2)), radius)
        pygame.display.update(pygame.Rect(0, 0, self.width, CONFIG['cell_size']))

    def _render(self):
        self.display_surface.fill(CONFIG['empty_color'])
        
        # Draw the board structure
        for r in range(CONFIG['rows']):
            for c in range(CONFIG['cols']):
                rect_x = c * CONFIG['cell_size']
                rect_y = (r + 1) * CONFIG['cell_size']
                pygame.draw.rect(self.display_surface, CONFIG['bg_color'], 
                                 (rect_x, rect_y, CONFIG['cell_size'], CONFIG['cell_size']))
                
                cell_val = self.game.get_cell(r, c)
                circle_color = CONFIG['player_colors'][cell_val] if cell_val in CONFIG['player_colors'] else CONFIG['empty_color']
                center_x = int(rect_x + CONFIG['cell_size'] / 2)
                center_y = int(rect_y + CONFIG['cell_size'] / 2)
                radius = int(CONFIG['cell_size'] / 2 - 5)
                
                pygame.draw.circle(self.display_surface, circle_color, (center_x, center_y), radius)

        pygame.display.update()

    def _show_victory_message(self):
        text_color = CONFIG['player_colors'][self.game.winner]
        text_surf = self.font.render(f"Player {self.game.winner} Wins!", True, text_color)
        text_rect = text_surf.get_rect(center=(self.width // 2, CONFIG['cell_size'] // 2))
        
        # Clear the top area
        pygame.draw.rect(self.display_surface, CONFIG['empty_color'], (0, 0, self.width, CONFIG['cell_size']))
        self.display_surface.blit(text_surf, text_rect)

if __name__ == '__main__':
    app = GameWindow()
    app.run()