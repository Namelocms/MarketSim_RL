import torch.nn as nn

state_dim = 16
action_dim = 3
layers = 16

class Actor(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Sequential(
            nn.Linear(state_dim, layers),
            nn.ReLU(),
            nn.Linear(layers, action_dim),
            nn.ReLU(),
            nn.Linear(action_dim, action_dim),
            nn.Softmax(dim=-1)
        )
    def forward(self, x):
        return self.fc(x)
        
class Critic(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Sequential(
            nn.Linear(state_dim, layers),
            nn.ReLU(),
            nn.Linear(layers, 1)
        )
    def forward(self, x):
        return self.fc(x)