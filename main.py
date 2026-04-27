import pygame
import sys
import math
import random

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

    def get_valid_locations(self):
        """Returns a list of valid columns."""
        valid_locations = []
        for col in range(CONFIG['cols']):
            if self.can_play_in_column(col):
                valid_locations.append(col)
        return valid_locations

    def simulate_move(self, col, player):
        """Temporarily drops a piece into the board for AI simulation, returning row index."""
        r = self.find_lowest_empty_row(col)
        self.grid[r][col] = player
        return r

    def undo_move(self, r, col):
        """Removes a temporarily dropped piece from the board."""
        self.grid[r][col] = 0

    def assess_line_value(self, cell_group, current_player):
        """Quantifies the strategic worth of a group of four cells."""
        val = 0
        enemy_id = 3 - current_player
        
        my_pcs = cell_group.count(current_player)
        empty_pcs = cell_group.count(0)
        enemy_pcs = cell_group.count(enemy_id)
        
        if my_pcs == 4:
            val += 150
        elif my_pcs == 3 and empty_pcs == 1:
            val += 10
        elif my_pcs == 2 and empty_pcs == 2:
            val += 4
            
        if enemy_pcs == 3 and empty_pcs == 1:
            val -= 8
            
        return val

    def get_layout_score(self, current_player):
        """Generates a comprehensive positional evaluation. 
        Uses directional vectors to condense logic and deviate from standard linear sweeps."""
        total_value = 0
        
        # Center column preference
        ctr_col = CONFIG['cols'] // 2
        ctr_pieces = sum(1 for r in range(CONFIG['rows']) if self.grid[r][ctr_col] == current_player)
        total_value += ctr_pieces * 5
        
        # Consolidate all directional line evaluations 
        for r in range(CONFIG['rows']):
            for c in range(CONFIG['cols']):
                for dr, dc in WIN_VECTORS:
                    end_r = r + 3 * dr
                    end_c = c + 3 * dc
                    if 0 <= end_r < CONFIG['rows'] and 0 <= end_c < CONFIG['cols']:
                        segment = [self.grid[r + i*dr][c + i*dc] for i in range(4)]
                        total_value += self.assess_line_value(segment, current_player)

        return total_value

    def find_best_strategy(self, depth_left, alpha_bound, beta_bound, is_ai_turn):
        """A stylized and renamed implementation of alpha-beta search."""
        available_cols = self.get_valid_locations()
        game_ended = self._detect_victory(1) or self._detect_victory(2) or not available_cols
        
        if depth_left == 0 or game_ended:
            if game_ended:
                if self._detect_victory(2):
                    return (None, 999999999)
                elif self._detect_victory(1):
                    return (None, -999999999)
                return (None, 0)
            return (None, self.get_layout_score(2))
                
        if is_ai_turn:
            best_val = -math.inf
            chosen_col = random.choice(available_cols)
            for c in available_cols:
                row_idx = self.simulate_move(c, 2)
                cur_val = self.find_best_strategy(depth_left - 1, alpha_bound, beta_bound, False)[1]
                self.undo_move(row_idx, c)
                
                if cur_val > best_val:
                    best_val = cur_val
                    chosen_col = c
                alpha_bound = max(alpha_bound, best_val)
                if alpha_bound >= beta_bound:
                    break
            return chosen_col, best_val
        else:
            best_val = math.inf
            chosen_col = random.choice(available_cols)
            for c in available_cols:
                row_idx = self.simulate_move(c, 1)
                cur_val = self.find_best_strategy(depth_left - 1, alpha_bound, beta_bound, True)[1]
                self.undo_move(row_idx, c)
                
                if cur_val < best_val:
                    best_val = cur_val
                    chosen_col = c
                beta_bound = min(beta_bound, best_val)
                if alpha_bound >= beta_bound:
                    break
            return chosen_col, best_val

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
        """Starts the main game event loop to listen for mouse actions and quit commands."""
        self._render()
        while True:
            # AI Turn (Player 2)
            if not self.game.is_finished and self.game.active_player == 2:
                pygame.time.wait(200) # Short delay for visual polish
                col, _ = self.game.find_best_strategy(5, -math.inf, math.inf, True)
                if col is not None:
                    if self.game.make_play(col):
                        self._render()
                        if self.game.is_finished:
                            self._show_victory_message()
                            pygame.display.update()
                            pygame.time.wait(3000)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                # Human Turn (Player 1)
                if not self.game.is_finished and self.game.active_player == 1:
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