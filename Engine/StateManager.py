from Engine.DebugLog import Debug

class StateManager:
    def __init__(self, resourcemanager, window):
        self.window = window
        self.resourcemanager = resourcemanager
        self.newState = "None"
        self.currentState = "None"
        self.states = {}
        self.variables = {}
        self.stateStack = []

    def isQuit(self):
        return self.newState == "None"

    # state: type
    def AddState(self, state):
        if state.statename in self.states:
            Debug.Warn(f'State \"{state.statename}\" already exists')
        else:
            self.states[state.statename] = state(self, self.resourcemanager, self.window)

    def RemoveState(self, state):
        if state.statename in self.states:
            self.states.pop(state.statename, None)
        else:
            Debug.Warn(f'State \"{state.statename}\" does not exist')

    def IsStateChanged(self):
        return self.currentState != self.newState
    
    def LoadNewState(self):
        if self.newState == "None":
            Debug.Warn("State not specified before InitializeState()")
        else:
            self.states[self.newState].Load()
            self.currentState = self.newState

    def UpdateState(self, eventlist, dt):
        state = self.states.get(self.currentState)
        if state:
            state.eventlist = eventlist
            state.Update(dt)
        else:
            Debug.Warn(f'{self.currentState} does not exist')

    def UnloadCurrentState(self):
        if self.currentState == "None":
            Debug.Warn("State not specified before InitializeState()")
        else:
            self.states[self.currentState].Unload()
            if not self.IsStateChanged():
                self.currentState = "None"
                self.newState = "None"
    
    def ChangeState(self, newstate):
        if newstate == "None" or newstate in self.states:
            if newstate != self.currentState:
                self.newState = newstate
                Debug.Log(f'Changing State... {self.currentState} -> {self.newState}')
            else:
                Debug.Warn(f'ChangeState() is the same')
        else:
            Debug.Warn(f'State \"{newstate}\" does not exist')

    def PushState(self, newstate):
        if newstate in self.states:
            Debug.Log(f'Pushing state: {self.currentState} -> {newstate}')
            if self.currentState != "None":
                self.stateStack.append(self.currentState)
                self.states[self.currentState].Unload()
            self.currentState = newstate
            self.states[newstate].Load()
        else:
            Debug.Warn(f'State \"{newstate}\" does not exist')

    def PopState(self):
        if self.stateStack:
            Debug.Log(f'Popping state: {self.currentState}')
            self.states[self.currentState].Unload()
            self.currentState = self.stateStack.pop()
            self.states[self.currentState].Load()
        else:
            Debug.Warn("No states to pop")

    def CleanUp(self):
        while self.stateStack:
            popped_state = self.stateStack.pop()
            self.states[popped_state].Unload()
        self.UnloadCurrentState()
