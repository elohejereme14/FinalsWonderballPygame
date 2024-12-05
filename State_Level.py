from pygame.constants import K_DOWN, K_F1, K_F2, K_a, K_d, K_SPACE, K_p
from Engine.BaseState import BaseState
from Engine.LevelMap import LevelMap
from Engine.DebugLog import Debug
from Engine.ResourceManager import ResourceManager
from Engine.StateManager import StateManager
from Engine.Vector2 import Vector2
from Engine.Utilities import MYCOLOR
import Engine.Utilities
import pygame
import os

from State_MainMenu import State_MainMenu

class Camera:
    def __init__(self, size : Vector2):
        self.position = Vector2()
        self.size = size
        self.bufferSize = 64
        self.boundary = (Vector2(), Vector2())
    
    def isWithinView(self, pos):
        buffer = Vector2(self.bufferSize, self.bufferSize)
        return Engine.Utilities.PointAABB(pos, self.position - buffer, self.position + self.size + buffer)

    def clampToBoundary(self):
        if self.position.x < self.boundary[0].x: self.position.x = self.boundary[0].x
        elif self.position.x > self.boundary[1].x: self.position.x = self.boundary[1].x
        if self.position.y < self.boundary[0].y: self.position.y = self.boundary[0].y
        if self.position.y > self.boundary[1].y: self.position.y = self.boundary[1].y

class Player:
    def __init__(self):
        self.position = Vector2(0, 0)
        self.velocity = Vector2(0, 0)
        self.radius = 28
        self.lives = 3
        self.coins = 0
        self.score = 0
        self.jumpForce = -7.6  # Default jump force
        self.speed = 3.3
        self.boostedspeed = 7
        self.boostedJumpForce = -14.0  # Higher jump force during boost
        self.isBoosted = False  # Is jump boost active
        self.boostTimer = 0  # Remaining time for the boost
        self.speeder = False

    def UpdateBoost(self, dt):
        if self.isBoosted:
            self.boostTimer -= dt
            if self.boostTimer <= 0:
                self.isBoosted = False
                self.jumpForce = -7.6  # Reset to default jump force
                
        if self.speeder:
            self.boostTimer -= dt
            if self.boostTimer <= 0:
                self.speeder = False
                self.speed = 3.3
    
    def Died(self, respawnpt : Vector2):
        self.position = respawnpt
        self.velocity.SetZero()
        self.lives -= 1

    def isDead(self):
        return self.lives < 0

    def colliderData(self):
        return (self.position + Vector2(32,32), self.radius)

class State_Level(BaseState):
    statename = "Levels"

    def __init__(self, sm : StateManager, rm : ResourceManager, window : pygame.Surface):
        super().__init__(sm, rm, window, State_Level.statename)
        self.backgroundColor = (100, 180, 220)
        self.gravity = 9.8

        self.showDebug = False
        self.camera = Camera(Vector2.fromTuple(window.get_size()))
        
        self.player = Player()
        self.isOnGround = False

        self.levelMap = LevelMap(64) # GridSize = 64x64
        self.numOfLevels = 6
        self.currentLevel = 1

        self.isPaused = False
        self.showChoices = False
        self.selectedChoice = 0  # 0 for none, 1 for choice A, 2 for choice B
            
    def __drawMap(self):
        Tiles = LevelMap.Tiles
        dimension = self.levelMap.mapDim
        map = self.levelMap.map
        for x in range(dimension[0]):
            for y in range(dimension[1]):
                value = map[y * dimension[0] + x]
                if value != 0:
                    position = Vector2(x * 64, y * 64)
                    if self.camera.isWithinView(position):
                        self.AddDrawSprite(Tiles[value], position - self.camera.position)
        # Draw level ?-?
        self.AddDrawFont(f'Level {int((self.currentLevel-1)/3) + 1} - { (self.currentLevel-1)%3 + 1 }', 
                        self.levelMap.GetStartPoint_ScreenPos() - Vector2(0, 64) - self.camera.position, 
                        MYCOLOR.WHITE, 50)
        

    def __drawColliders(self):
        for col in self.levelMap.colliders:
            self.AddDrawDebugRectCall(col.position - self.camera.position, col.size, MYCOLOR.GREEN)
        for trig in self.levelMap.triggers:
            self.AddDrawDebugRectCall(trig.position - self.camera.position, trig.size, MYCOLOR.YELLOW)

        player_collider = self.player.colliderData()
        self.AddDrawDebugCircleCall(player_collider[0] - self.camera.position, player_collider[1], MYCOLOR.GREEN)

    def __drawUI(self):
        self.AddDrawUISprite("Black", Vector2(), 0, Vector2(2.2, 1.9))
        self.AddDrawUISprite("Ball", Vector2(10,3), 0, Vector2(0.6, 0.6))
        self.AddDrawUIFont(f'x{self.player.lives}', Vector2(90, 10), MYCOLOR.WHITE, 30)
        self.AddDrawUISprite("Ring", Vector2(10,43), 0, Vector2(0.6, 0.6))
        self.AddDrawUIFont(f'x{self.player.coins}', Vector2(90, 50), MYCOLOR.WHITE, 30)
        self.AddDrawUIFont("Score", Vector2(10, 90), MYCOLOR.WHITE, 30)
        self.AddDrawUIFont(f'{self.player.score}', Vector2(96, 90), MYCOLOR.WHITE, 30)

        
        self.AddDrawUISprite("Black", Vector2(850, 0), 0, Vector2(1.2, 0.4))
        self.AddDrawUIFont(f'{int(self.sm.variables["TimeTaken"] / 60)}m {int(self.sm.variables["TimeTaken"] % 60)}s', Vector2(860, 4), MYCOLOR.WHITE, 25)

        if self.player.isBoosted:
            self.AddDrawUISprite("Black", Vector2(2, 158), 0, Vector2(3.4, 0.5))
            self.AddDrawUIFont(f'Jump Boost: {int(self.player.boostTimer)}s', Vector2(5, 160), MYCOLOR.YELLOW, 40)
        
        if self.player.speeder:
            self.AddDrawUISprite("Black", Vector2(2, 158), 0, Vector2(3.6, 0.5))
            self.AddDrawUIFont(f'Speed Boost: {int(self.player.boostTimer)}s', Vector2(5, 160), MYCOLOR.YELLOW, 40)

        if self.showChoices:
            self.AddDrawUISprite("Black", Vector2(300, 200), 0, Vector2(4, 2))  # Background for choices
            self.AddDrawUIFont("Choose an option:", Vector2(320, 210), MYCOLOR.WHITE, 40)
            
            # Highlight selection
            color_continue = MYCOLOR.GREEN if self.selectedChoice == 0 else MYCOLOR.WHITE
            color_quit = MYCOLOR.RED if self.selectedChoice == 1 else MYCOLOR.WHITE

            self.AddDrawUIFont("[Continue]", Vector2(320, 260), color_continue, 30)
            self.AddDrawUIFont("[Quit to Main Menu]", Vector2(320, 300), color_quit, 30)

    def __handleCollision(self):
        player_collider = self.player.colliderData()
        # Collision between player and world
        for collider in self.levelMap.colliders:
            collision = Engine.Utilities.CircleAABB(player_collider[0], player_collider[1], collider.position, collider.position + collider.size)
            if collision.hit:
                # Resolve
                resolve_dir = (player_collider[0] - collision.contactPoint).Normalized()
                resolve_dist = self.player.radius - (player_collider[0] - collision.contactPoint).Length()
                self.player.position += resolve_dir * resolve_dist

                if resolve_dir.y <= -0.7:
                    self.player.velocity.y = 0
                    self.isOnGround = True
                if resolve_dir.y >= 0.7:
                    self.player.velocity.y = 0

                # Debug draw contact point
                if self.showDebug:
                    self.AddDrawDebugPointCall(collision.contactPoint - self.camera.position, MYCOLOR.BLUE)

    def __handleTriggers(self):
        player_collider = self.player.colliderData()
        for trigger in self.levelMap.triggers:
            if trigger.active:
                triggered = Engine.Utilities.CircleAABB(player_collider[0], player_collider[1],
                                                        trigger.position, trigger.position + trigger.size)
                if triggered.hit:
                    if trigger.name == "Ring":
                        self.player.coins += 1
                        self.player.score += 2
                        self.levelMap.RemoveRingTrigger(trigger)
                        self.rm.GetAudioClip("PickupCoin").Play()
                        trigger.active = False
                        # Play a special sound when the player reaches 20 coins
                        if self.player.coins == 20:
                            self.rm.GetAudioClip("Checkpoint").Play()
                            self.levelMap.ActivateEndpoint(trigger)
                    elif trigger.name == "Checkpoint_NotActive":
                        self.levelMap.ActivateCheckpointTrigger(trigger)
                        self.rm.GetAudioClip("Checkpoint").Play()
                        trigger.active = False
                    elif trigger.name == "JumpBoost":
                        self.player.isBoosted = True
                        self.player.jumpForce = self.player.boostedJumpForce
                        self.levelMap.RemoveRingTrigger(trigger)
                        self.player.boostTimer = 5.0  # Boost lasts for 5 seconds
                        self.rm.GetAudioClip("Boost").Play()
                        trigger.active = False
                    elif trigger.name == "SpeedBoost":
                        self.player.speeder = True
                        self.player.speed = self.player.boostedspeed
                        self.levelMap.RemoveRingTrigger(trigger)
                        self.player.boostTimer = 5.0  # Boost lasts for 5 seconds
                        self.rm.GetAudioClip("Boost").Play()
                        trigger.active = False
                    elif trigger.name == "Spike":
                        self.player.Died(self.levelMap.GetRespawnPoint_ScreenPos())
                        self.rm.GetAudioClip("Hit").Play()
                        if self.player.isDead():
                            self.__GameOver()
                        break
                    elif trigger.name == "JumpPad":
                        self.player.velocity.y = -20
                        self.rm.GetAudioClip("JumpPad").Play()
                        break
                    elif trigger.name == "Endpoint":
                        if self.player.coins < 20:
                            continue  # Ignore this trigger if coins are less than 20
                    
                        trigger.active = False
                        if self.currentLevel != self.numOfLevels:
                            self.__LoadLevel(self.currentLevel + 1)
                            self.player.coins = 0
                        else:
                            self.__GameOver()
                        break

    def __handlePhysics(self, dt: float):
        # Gravity
        self.player.velocity.y += self.gravity * dt * 2
        # Terminal velocity
        if self.player.velocity.y > 33.0:
            self.player.velocity.y = 33.0

        # Friction
        if self.player.velocity.x > 0.3:
            self.player.velocity.x -= 0.2
        elif self.player.velocity.x < -0.3:
            self.player.velocity.x += 0.2
        else:
            self.player.velocity.x = 0.0

        self.player.position += self.player.velocity * 64.0 * dt # assume 64px = 1metre

    def __handleKeyInput(self):
        # Trigger once
        # Toggle Debug
        for env in self.eventlist:
            if env.type == pygame.KEYDOWN:            
                if env.key == K_F1:
                    self.showDebug = not self.showDebug
                elif env.key == K_F2:
                    if self.currentLevel != self.numOfLevels:
                        self.__LoadLevel(self.currentLevel + 1)
                    else:
                        self.__GameOver()
                if env.key == K_SPACE and self.isOnGround:
                    self.isOnGround = False
                    self.player.velocity.y = self.player.jumpForce
                    self.rm.GetAudioClip("Jump").Play()
                # Pause and show choices
                if env.key == K_p:
                    if not self.isPaused:
                        self.isPaused = True
                        self.showChoices = True
                        self.selectedChoice = 0  # Reset to first option
                    else:
                        self.isPaused = False
                        self.showChoices = False
                
                if self.showChoices:
                    if env.key == pygame.K_DOWN:
                        self.selectedChoice = (self.selectedChoice + 1) % 2  # Toggle between 0 and 1
                    elif env.key == pygame.K_UP:
                        self.selectedChoice = (self.selectedChoice - 1) % 2  # Toggle between 1 and 0
                    elif env.key == pygame.K_RETURN:  # Select the current choice
                        if self.selectedChoice == 0:  # Continue
                            self.isPaused = False
                            self.showChoices = False
                        elif self.selectedChoice == 1:  # Quit to Main Menu
                            self.__MainMenu()
                            self.__ResetStats()

        # Repeated call
        if not self.isPaused:
            keypress = pygame.key.get_pressed()
            if keypress[K_a]:
                if self.player.velocity.x > -self.player.speed:
                    self.player.velocity.x -= 1.1
            elif keypress[K_d]:
                if self.player.velocity.x < self.player.speed:
                    self.player.velocity.x += 1.1

    def __updateCamera(self):
        self.camera.position = self.player.position - Vector2(400, 300)
        self.camera.clampToBoundary()

    def __LoadLevel(self, level):
        self.currentLevel = level
        self.levelMap.LoadMap(os.path.join("Assets", "Level", f'Level{self.currentLevel}.dat'))
        self.levelMap.GenerateColliders()
        # Init camera settings
        self.camera.boundary = (Vector2(), Vector2(self.levelMap.mapDim[0] * 64 - self.camera.size.x,
                                                   self.levelMap.mapDim[1] * 64 - self.camera.size.y))
        # Init player starting position
        self.player.position = self.levelMap.GetStartPoint_ScreenPos() - Vector2(0,64)

    def __ResetStats(self):
        self.player.coins = 0
        self.player.score = 0
        self.player.lives = 5
        self.player.velocity.SetZero()

    def __GameOver(self):
        self.sm.ChangeState("Game Over")
        self.sm.variables["Lives"] = self.player.lives
        self.sm.variables["Coins"] = self.player.coins
        self.sm.variables["totscore"] = self.player.score
        self.sm.variables["CurrentLevel"] = self.currentLevel
        self.sm.variables["NumOfLevels"] = self.numOfLevels
        self.currentLevel = 1

    def StopAllTimers(self):
        self.player.boostTimer = 0
        self.player.speeder = False  # Disable speed boost
        self.player.isBoosted = False  # Disable jump boost

        # If there are other timers to stop, add them here as needed
        self.sm.variables["TimeTaken"] = 0  # Stop any global timer

    def __MainMenu(self):
        self.sm.ChangeState("Main Menu")
        self.currentLevel = 1

    def Load(self):
        super().Load()
        self.rm.GetAudioClip("inGameBGM").source.play(loops=-1)
        self.__LoadLevel(self.currentLevel)
        self.__ResetStats()

    def Unload(self):
        super().Unload()
        self.rm.GetAudioClip("inGameBGM").source.stop()

    def Update(self, dt):
        self.sm.variables["TimeTaken"] += dt
        if dt > 2/60:
            return

        if not self.isPaused:
            self.__handleKeyInput()
            self.__handlePhysics(dt)
            self.__handleCollision()
            self.__handleTriggers()
            self.__updateCamera()
        else:
            self.__handleKeyInput()
        # Update player boost state
        self.player.UpdateBoost(dt)

        self.__drawMap()
        self.__updateCamera()
        self.AddDrawSprite("Ball", self.player.position - self.camera.position)
        self.__drawUI()

        if self.showDebug:
            self.__drawColliders()

        super().Update(dt)
        super().Draw()