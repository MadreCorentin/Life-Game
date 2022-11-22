# -*- coding: utf-8 -*-

import pygame
import sys
import numpy as np
import random
from copy import deepcopy
from numba import njit

ALIVE_COLOR = pygame.Color("forestgreen")
DEAD_COLOR = pygame.Color("black")

GENERATE_RANDOM_CELLS = 0.1
MAX_FPS = 100
PIXEL_SIZE = 10

CONFIG = {
    'screen_width' : 800 + PIXEL_SIZE,
    'screen_height' : 600 + PIXEL_SIZE,
    'cell_pixel_size' : PIXEL_SIZE,
    "keys" : {
        "PAUSE" : ' ',
        "CLEAR" : 'c',
        "RESTART" : 'r'
    },
}


class GridLifeGame(object):
    
    def __init__(self, screen_width, screen_height, cell_pixel_size, **kwargs):
        self.width = screen_width
        self.height = screen_height
        
        self.cell_pixel_size = cell_pixel_size
        self.nb_cells_column = self.width // self.cell_pixel_size
        self.nb_cells_row = self.height // self.cell_pixel_size
       
        self.grid = np.zeros((self.nb_cells_row, self.nb_cells_column), dtype=bool)
        self.screen = pygame.display.set_mode((self.width, self.height))
        
        for x in range (0, self.width, self.cell_pixel_size):
            pygame.draw.line(self.screen, pygame.Color('dimgray'), (x, 0), (x, self.height))
        
        for y in range (0, self.height, self.cell_pixel_size):
            pygame.draw.line(self.screen, pygame.Color('dimgray'), (0, y), (self.width, y))
            
        self.init_grid()
        
    
    def init_grid(self):
        n = 20
        
        init_pattern = lambda i, j, n: random.random() < GENERATE_RANDOM_CELLS
        # init_pattern = lambda i, j, n: (i % n == 0)
        # init_pattern = lambda i, j, n: ((n * i + j) % n == 0)
        # init_pattern = lambda i, j, n: ((i * j) % n) == 0

        for row in range(self.nb_cells_row):
            for column in range(self.nb_cells_column):

                is_alive = init_pattern(column, row, n)
                
                self.grid[row][column] = is_alive
                self.color_grid_cell(row, column, is_alive)
                
        
    def clear(self):
        is_alive = False
        for row in range(self.nb_cells_row):
            for column in range(self.nb_cells_column):
                self.grid[row][column] = is_alive
                self.color_grid_cell(row, column, is_alive)
                
                
    def color_grid_cell(self, row, column, is_alive):
        rect = pygame.Rect(column * self.cell_pixel_size + 2, 
                            row * self.cell_pixel_size + 2, 
                            self.cell_pixel_size - 2, 
                            self.cell_pixel_size - 2)
        color = ALIVE_COLOR if is_alive else DEAD_COLOR
        pygame.draw.rect(self.screen, color, rect) 


    def color_cell(self, x, y, is_alive):
        row = self.nb_cells_row * y // self.height
        column = self.nb_cells_column * x // self.width
        self.grid[row][column] = is_alive
        self.color_grid_cell(row, column, is_alive)
        
        
    def update_life_v1(self, current_grid):
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
                
                
    def update_life_v2(self, current_grid):
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
        
                    
               
if __name__ == "__main__":

    pygame.init()
    pygame.display.set_caption("Conway's Game of Life")
    
    clock = pygame.time.Clock()
    
    keys = CONFIG['keys']
    glg = GridLifeGame(**CONFIG)
    is_running = False
    
    while True:
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == ord(keys['PAUSE']):
                    is_running = not(is_running)
                if event.key == ord(keys['CLEAR']):
                    glg.clear()
                if event.key == ord(keys['RESTART']):
                    glg.init_grid()
                    
        left_click, _, right_click = pygame.mouse.get_pressed()
        
        # click gauche : une cellule aparait
        if left_click:
            x, y = pygame.mouse.get_pos()
            glg.color_cell(x, y, True)
            
        # click droit : une cellule disparait
        elif right_click:
            x, y = pygame.mouse.get_pos()
            glg.color_cell(x, y, False)
        
        if is_running:
            grid_copy = deepcopy(glg.grid)
            glg.update_life_v1(grid_copy)
            # glg.update_life_v2(grid_copy)
            clock.tick(MAX_FPS)
            
        pygame.display.flip()
        
        
        
        