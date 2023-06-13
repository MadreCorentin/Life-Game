# -*- coding: utf-8 -*-

import argparse
import pygame
import sys
import random
import numpy as np
from copy import deepcopy
from numba import njit

ALIVE_COLOR = pygame.Color("forestgreen")
DEAD_COLOR = pygame.Color("black")

class GridLifeGame(object):
    
    def __init__(self, screen_width, screen_height, cell_size, frame_per_second, **kwargs):
        self.width = screen_width
        self.height = screen_height
        
        self.cell_size = cell_size
        self.nb_cells_column = self.width // self.cell_size
        self.nb_cells_row = self.height // self.cell_size
       
        self.grid = np.zeros((self.nb_cells_row, self.nb_cells_column), dtype=bool)
        self.screen = pygame.display.set_mode((self.width, self.height))
        
        for x in range (0, self.width, self.cell_size):
            pygame.draw.line(self.screen, pygame.Color('dimgray'), (x, 0), (x, self.height))
        
        for y in range (0, self.height, self.cell_size):
            pygame.draw.line(self.screen, pygame.Color('dimgray'), (0, y), (self.width, y))
            
        self.is_running = False
        self.frame_per_second = frame_per_second

        self.grid_initialization()

    ####################################################################################

    def play_pause_grid(self):
        self.is_running = not(self.is_running)

    ####################################################################################

    def increase_fps(self):
        self.frame_per_second = min(128, self.frame_per_second * 2)

    ####################################################################################

    def decrease_fps(self):
        self.frame_per_second = max(1, self.frame_per_second // 2)

    ####################################################################################

    def log(self):
        print(f"is_running : {self.is_running}")
        print(f"frame_per_second : {self.frame_per_second}")
        print(f"iteration : {self.iteration}")
        print("#" * 50)

    ####################################################################################
    
    def grid_initialization(self):
        
        self.iteration = 0

        init_pattern = lambda i, j: random.random() < 0.2

        # n = 20
        # init_pattern = lambda i, j, n: (i % n == 0)
        # init_pattern = lambda i, j, n: ((n * i + j) % n == 0)
        # init_pattern = lambda i, j, n: ((i * j) % n) == 0

        for row in range(self.nb_cells_row):
            for column in range(self.nb_cells_column):

                is_alive = init_pattern(column, row)
                # is_alive = init_pattern(column, row, n)
                
                self.grid[row][column] = is_alive
                self.color_grid_cell(row, column, is_alive)

    ####################################################################################            
        
    def clear_grid(self):
        is_alive = False
        for row in range(self.nb_cells_row):
            for column in range(self.nb_cells_column):
                self.grid[row][column] = is_alive
                self.color_grid_cell(row, column, is_alive)

    ####################################################################################          
                
    def color_grid_cell(self, row, column, is_alive):
        rect = pygame.Rect(column * self.cell_size + 2, 
                            row * self.cell_size + 2, 
                            self.cell_size - 2, 
                            self.cell_size - 2)
        color = ALIVE_COLOR if is_alive else DEAD_COLOR
        pygame.draw.rect(self.screen, color, rect) 

    ####################################################################################

    def manually_color_cell(self, x, y, is_alive):
        row = self.nb_cells_row * y // self.height
        column = self.nb_cells_column * x // self.width
        self.grid[row][column] = is_alive
        self.color_grid_cell(row, column, is_alive)

    ####################################################################################

    def update_life_lazy(self, current_grid):
        self.iteration += 1
        
        for row in range(self.nb_cells_row):
            for column in range(self.nb_cells_column):
                min_row = max(0, row-1)
                max_row = min(self.nb_cells_row, row+2)
                min_column = max(0, column-1)
                max_column = min(self.nb_cells_column, column+2)
                
                neighbors_cells = current_grid[min_row:max_row, min_column:max_column]
                current_is_alive = current_grid[row, column]
                sum_cells = np.sum(neighbors_cells) - current_grid[row, column]
                
                if current_is_alive:
                    is_alive = (sum_cells >= 2 and sum_cells <= 3)
                else:
                    is_alive = (sum_cells == 3)
                    
                self.grid[row, column] = is_alive
                self.color_grid_cell(row, column, is_alive)

    ####################################################################################
    ####################################################################################     
                
    def update_life_numba(self, current_grid):
        self.iteration += 1

        self.grid = self.numba_update_life(
            self.nb_cells_row, 
            self.nb_cells_column, 
            self.grid, 
            current_grid
        )
        
        for row in range(self.nb_cells_row):
            for column in range(self.nb_cells_column):
                self.color_grid_cell(row, column, self.grid[row, column])
        

    @staticmethod         
    @njit
    def numba_update_life(rows, columns, new_grid, old_grid):
        for row in range(rows):
            for column in range(columns):
                min_row = max(0, row-1)
                max_row = min(rows, row+2)
                min_column = max(0, column-1)
                max_column = min(columns, column+2)
                
                neighbors_cells = old_grid[min_row:max_row, min_column:max_column]
                current_is_alive = old_grid[row, column]
                sum_cells = np.sum(neighbors_cells) - old_grid[row, column]
                
                if current_is_alive:
                    is_alive = (sum_cells >= 2 and sum_cells <= 3)
                else:
                    is_alive = (sum_cells == 3)
                    
                new_grid[row, column] = is_alive
                
        return new_grid
        
    #################################################################################### 
    ####################################################################################               
               
if __name__ == "__main__":

    caption = "Conway's Game of Life"
    parser = argparse.ArgumentParser(description=caption)
    parser.add_argument('-sw', '--screen_width', type=int, help=f"screen width (default 800)", default=800)
    parser.add_argument('-sh', '--screen_height', type=int, help=f"screen height (default=600)", default=600)
    parser.add_argument('-cs', '--cell_size', type=int, help=f"cell size (default=10)", default=10)
    parser.add_argument('-fps', '--frame_per_second', type=int, help=f"frame per second (default=8)", default=8)
    parser.add_argument('-n', '--numba', type=int, help=f"use numba if value > 0 (default 0)", default=0)

    args = parser.parse_args()

    config_life_game = {
        'screen_width' : args.screen_width + args.cell_size + 1,
        'screen_height' : args.screen_height + args.cell_size + 1,
        'cell_size' : args.cell_size,
        'frame_per_second' : args.frame_per_second,
        "keys" : {
            "PAUSE" : pygame.K_SPACE,
            "CLEAR" : pygame.K_c,
            "RESTART": pygame.K_r,
            "INCREASE_FPS" : pygame.K_RIGHT,
            "DECREASE_FPS" : pygame.K_LEFT,
        }
    }

    keys = config_life_game['keys']
    grid_life = GridLifeGame(**config_life_game)

    if args.numba:
        update_life = grid_life.update_life_numba
    else:
        update_life = grid_life.update_life_lazy

    pygame.init()
    pygame.display.set_caption(caption)
    clock = pygame.time.Clock()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == keys['PAUSE']:
                    grid_life.play_pause_grid()
                if event.key == keys['CLEAR']:
                    grid_life.clear_grid()
                if event.key == keys['RESTART']:
                    grid_life.grid_initialization()
                if event.key == keys['INCREASE_FPS']:
                    grid_life.increase_fps()
                if event.key == keys['DECREASE_FPS']:
                    grid_life.decrease_fps()

                grid_life.log()
                    
        left_click, _, right_click = pygame.mouse.get_pressed()
        
        # click gauche : une cellule aparait
        if left_click:
            x, y = pygame.mouse.get_pos()
            grid_life.manually_color_cell(x, y, True)
            
        # click droit : une cellule disparait
        elif right_click:
            x, y = pygame.mouse.get_pos()
            grid_life.manually_color_cell(x, y, False)
        
        if grid_life.is_running:
            tmp_grid = deepcopy(grid_life.grid)
            update_life(tmp_grid)
            clock.tick(grid_life.frame_per_second)
            
        pygame.display.flip()

