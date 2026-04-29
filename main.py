import pygame
import sys
import math
import random
import argparse
import time

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
        self.iterations = 0
        self.totalIterations = 0

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

        #print(f"Board Score from P1 (RED)   : {self.evaluate_board(1)}\n")
        #print(f"Board Score from P2 (YELLOW): {self.evaluate_board(2)}")

            
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
    
    # minimax implementation
    def get_valid_locations(self):
        valid_locations = []
        for col in range(CONFIG['cols']):
            if self.can_play_in_column(col):
                valid_locations.append(col)
        return valid_locations

    def is_terminal_node(self):
        return self._detect_victory(1) or self._detect_victory(2) or len(self.get_valid_locations()) == 0

    def minimax(self, depth, maximizingPlayer, alpha, beta, usePruning=True):
        self.iterations += 1

        valid_locations = self.get_valid_locations()
        is_terminal = self.is_terminal_node()
        if depth == 0 or is_terminal:
            if is_terminal:
                if self._detect_victory(2):
                    return (None, 100000000000000)
                elif self._detect_victory(1):
                    return (None, -10000000000000)
                else: # Game is over, no more valid moves
                    return (None, 0)
            else: # Depth is zero
                return (None, self.evaluate_board(2))
                
        if maximizingPlayer:
            value = -math.inf
            best_col = random.choice(valid_locations)
            for col in valid_locations:
                row = self.find_lowest_empty_row(col)
                # simulate move
                self.grid[row][col] = 2
                new_score = self.minimax(depth-1, False, alpha, beta, usePruning)[1]
                # undo move
                self.grid[row][col] = 0
                if new_score > value:
                    value = new_score
                    best_col = col

                # Alpha-Beta Pruning
                if(usePruning):
                    alpha = max(alpha, value)
                    if alpha >= beta:
                        # Prune branch
                        break

            return best_col, value
        else: # Minimizing player
            value = math.inf
            best_col = random.choice(valid_locations)
            for col in valid_locations:
                row = self.find_lowest_empty_row(col)
                # simulate move
                self.grid[row][col] = 1
                new_score = self.minimax(depth-1, True, alpha, beta, usePruning)[1]
                # undo move
                self.grid[row][col] = 0
                if new_score < value:
                    value = new_score
                    best_col = col

                # Alpha-Beta Pruning
                if(usePruning):
                    beta = min(beta, value)
                    if alpha >= beta:
                        # Prune branch
                        break

            return best_col, value

    # calculating score of each 4 cell wide 'window'
    def calculate_score(self, window, player_id):
        score = 0
        opponent = 3 - player_id
        
        if window.count(player_id) == 4:
            score += 1000000
        elif window.count(player_id) == 3 and window.count(0) == 1:
            score += 50
        elif window.count(player_id) == 2 and window.count(0) == 2:
            score += 10

        if window.count(opponent) == 3 and window.count(0) == 1:
            score-= 80
        
        return score

    # checking board to compute all window scores
    def evaluate_board(self, player_id):
        total = 0
        # dr, dc representing row and column directions
        for dr, dc in WIN_VECTORS:
            for r in range(CONFIG['rows']):
                for c in range(CONFIG['cols']):
                    window = []
                    for i in range(4):
                        nr = r + dr * i
                        nc = c + dc * i 

                        if 0 <= nr < CONFIG['rows'] and 0 <= nc < CONFIG['cols']:
                            window.append(self.grid[nr][nc])
                        if len(window) == 4:
                            total += self.calculate_score(window, player_id)

        return total


# The GameWindow class manages the Pygame graphical interface,
# rendering the board, handling user inputs, and updating the display.
class GameWindow:
    def __init__(self, use_Pruning, depth=4):
        pygame.init()
        self.width = CONFIG['cols'] * CONFIG['cell_size']
        self.height = (CONFIG['rows'] + 1) * CONFIG['cell_size']
        self.display_surface = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Connect 4 - Unique Edition")
        self.game = Connect4Match()
        self.font = pygame.font.SysFont("Verdana", 60, bold=True)
        self.usePruning = use_Pruning
        self.depth = depth
    def run(self):
        self._render()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
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

            if not self.game.is_finished and self.game.active_player == 2:
                self.game.iterations = 0
                start = time.time()
                col, minimax_score = self.game.minimax(self.depth, True, -math.inf, math.inf, usePruning=self.usePruning)
                elapsed = time.time() - start
                print(f"[{elapsed:.4f}] Pruning: {self.usePruning} | Depth: {self.depth} | Iterations: {self.game.iterations}")
                self.game.totalIterations += self.game.iterations
                if col is not None:
                    # Clear top tracker before AI moves
                    pygame.draw.rect(self.display_surface, CONFIG['empty_color'], (0, 0, self.width, CONFIG['cell_size']))
                    pygame.display.update(pygame.Rect(0, 0, self.width, CONFIG['cell_size']))
                    pygame.time.wait(500)
                    
                    self.game.make_play(col)
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
        print(f"Total iterations: {self.game.totalIterations}")
        # Clear the top area
        pygame.draw.rect(self.display_surface, CONFIG['empty_color'], (0, 0, self.width, CONFIG['cell_size']))
        self.display_surface.blit(text_surf, text_rect)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-pruning', action='store_false')
    parser.add_argument('--depth', type=int, default=4)
    args = parser.parse_args()

    usePruning = args.no_pruning
    aiDepth = args.depth

    if(not usePruning):
        print(f"Starting game with Alpha-Beta pruning OFF with Depth = {aiDepth}")
        app = GameWindow(usePruning, depth=aiDepth)
        app.run()
    else:
        print(f"Starting game with Alpha-Beta pruning ON with Depth = {aiDepth}")
        app = GameWindow(True, depth=aiDepth)
        app.run()

    