from Engine.BaseState import BaseState
from Engine.Utilities import MYCOLOR
from Engine.Vector2 import Vector2
import pygame

class State_Pause(BaseState):
    statename = "Pause"

    def __init__(self, sm, rm, window):
        super().__init__(sm, rm, window, State_Pause.statename)
        self.backgroundColor = (50, 50, 50)

    def __handleKeyInput(self):
        for env in self.eventlist:
            if env.type == pygame.KEYDOWN:
                if env.key == pygame.K_p:  # Press 'P' to resume
                    self.sm.PopState()  # Go back to the previous state

    def __drawUI(self):
        self.AddDrawUIFont("Game Paused", Vector2(32, 64), MYCOLOR.WHITE, 72)
        self.AddDrawUIFont("Press [P] to Resume", Vector2(32, 150), MYCOLOR.WHITE, 30)

    def Load(self):
        super().Load()

    def Unload(self):
        super().Unload()

    def Update(self, dt):
        self.__handleKeyInput()
        self.__drawUI()
        super().Update(dt)
        super().Draw()
