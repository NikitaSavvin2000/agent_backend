import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from torch.amp import autocast, GradScaler
import pandas as pd


device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Используется устройство: {device}")

batch_size = 512
num_epochs = 30
embedding_dim = 256
num_blocks = 4
learning_rate = 1e-2
patience = 5

X_train = np.array(df_to_train['X_train'].tolist(), dtype=np.float32)
y_train = np.array(df_to_train['y_train'].tolist(), dtype=np.int64)

X_val = np.array(df_to_val['X_train'].tolist(), dtype=np.float32)
y_val = np.array(df_to_val['y_train'].tolist(), dtype=np.int64)

X_test = np.array(df_to_test['X_train'].tolist(), dtype=np.float32)
y_test = np.array(df_to_test['y_train'].tolist(), dtype=np.int64)

print(f"X_train shape: {X_train.shape}")
print(f"y_train shape: {y_train.shape}")
print(f"X_val shape: {X_val.shape}")
print(f"y_val shape: {y_val.shape}")
print(f"X_test shape: {X_test.shape}")
print(f"y_test shape: {y_test.shape}")


input_size = X_train.shape[2]
horizon = int(y_train.max() + 1)

class LSTMTabularModel(nn.Module):
    def __init__(self, input_size, horizon, embedding_dim=128, num_blocks=2):
        super().__init__()
        self.input_proj = nn.Linear(input_size, embedding_dim)
        self.lstm_blocks = nn.ModuleList()
        for i in range(num_blocks):
            in_dim = embedding_dim * 2 if i > 0 else embedding_dim
            self.lstm_blocks.append(nn.LSTM(in_dim, embedding_dim, batch_first=True, bidirectional=True))
        self.fc = nn.Linear(embedding_dim * 2, horizon)

    def forward(self, x):
        x = self.input_proj(x)  # (batch, seq_len, embedding_dim)
        for lstm in self.lstm_blocks:
            x, _ = lstm(x)
        x = x[:, -1, :]
        x = self.fc(x)
        return x

model = LSTMTabularModel(input_size, horizon, embedding_dim, num_blocks).to(device)

# weights = weights[::-1].copy()


# weights_tensor = torch.tensor(weights, dtype=torch.float32, device=device)

# criterion = nn.CrossEntropyLoss(weight=weights_tensor)
criterion = nn.CrossEntropyLoss()


optimizer = optim.Adam(model.parameters())
scaler = GradScaler()

train_losses, val_losses = [], []
best_val_loss = float('inf')
no_improve_epochs = 0

for epoch in range(num_epochs):
    model.train()
    running_loss = 0.0
    for i in range(0, len(X_train), batch_size):
        batch_X = torch.tensor(X_train[i:i+batch_size], device=device)
        batch_y = torch.tensor(y_train[i:i+batch_size], device=device)
        optimizer.zero_grad()
        with autocast(device_type="cuda"):
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()
        running_loss += loss.item() * batch_X.size(0)
    epoch_loss = running_loss / len(X_train)

    model.eval()
    val_loss_total = 0.0
    with torch.no_grad():
        for i in range(0, len(X_val), batch_size):
            val_X = torch.tensor(X_val[i:i+batch_size], device=device)
            val_y = torch.tensor(y_val[i:i+batch_size], device=device)
            with autocast(device_type="cuda"):
                val_outputs = model(val_X)
                val_loss = criterion(val_outputs, val_y)
            val_loss_total += val_loss.item() * val_X.size(0)
    val_loss_epoch = val_loss_total / len(X_val)

    train_losses.append(epoch_loss)
    val_losses.append(val_loss_epoch)
    print(f"Epoch {epoch+1}/{num_epochs}, Train Loss: {epoch_loss:.4f}, Val Loss: {val_loss_epoch:.4f}")

    if val_loss_epoch < best_val_loss:
        best_val_loss = val_loss_epoch
        no_improve_epochs = 0
        best_model_state = model.state_dict()
    else:
        no_improve_epochs += 1
        if no_improve_epochs >= patience:
            print(f"Ранняя остановка на {epoch+1}-й эпохе. Лучшая Val Loss: {best_val_loss:.4f}")
            model.load_state_dict(best_model_state)
            break

model.eval()
y_pred_list, prob_list = [], []
with torch.no_grad():
    for i in range(0, len(X_test), batch_size):
        test_X = torch.tensor(X_test[i:i+batch_size], device=device)
        with autocast(device_type="cuda"):
            logits = model(test_X)
            probs = torch.softmax(logits, dim=1)
            preds = torch.argmax(probs, dim=1)
        y_pred_list.append(preds.cpu().numpy())
        prob_list.append(probs.max(dim=1).values.cpu().numpy())

y_pred = np.concatenate(y_pred_list)
probabilities = np.concatenate(prob_list)
df_preds = pd.DataFrame({'y_true': y_test, 'y_pred': y_pred, 'probability': probabilities})
print(df_preds.head(10))
