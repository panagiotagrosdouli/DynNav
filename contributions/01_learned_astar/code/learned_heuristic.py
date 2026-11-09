import torch
from torch import nn


class HeuristicNet(nn.Module):
    """
    Νευρωνικό δίκτυο για heuristic.
    Συμβατό και με:
      HeuristicNet(input_dim=..., hidden_dim=...)
      HeuristicNet(in_dim=..., hidden=...)
    """
    def __init__(self, input_dim=None, hidden_dim=64, in_dim=None, hidden=None):
        super().__init__()

        # Συμβατότητα με παλιό κώδικα
        if input_dim is None and in_dim is not None:
            input_dim = in_dim
        if hidden is not None:
            if hidden_dim not in (None, 64) and hidden_dim != hidden:
                raise ValueError("Conflicting hidden_dim and hidden arguments.")
            hidden_dim = hidden

        if input_dim is None:
            raise ValueError("You must provide input_dim or in_dim.")
        if hidden_dim is None:
            hidden_dim = 64

        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, x):
        if not isinstance(x, torch.Tensor):
            x = torch.tensor(x, dtype=torch.float32)
        if x.ndim == 1:
            x = x.unsqueeze(0)
        return self.net(x)
