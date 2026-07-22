import re
import math
import torch
import torch.nn as nn
import torch.optim as optim

torch.manual_seed(5)

text = """собака спит на диване,
кот ест рыбу,
мальчик играет с мячом,
кот спит на окне,
девочка гуляет по улице,
кот пьет молоко,
кот играет с мышкой,
хомяк спит в коробке,
мальчик смотрит в окно,
девочка гуляет в парке
"""

tokens = re.findall(r"\w+", text.lower())

vocab = sorted(set(tokens))

token_to_idx = {}
for i, word in enumerate(vocab):
    token_to_idx[word] = i

idx_to_token = {}
for word, i in token_to_idx.items():
    idx_to_token[i] = word

indices = []
for word in tokens:
    indices.append(token_to_idx[word])

seq_len = 5
inputs = []
targets = []
for i in range(len(indices) - seq_len + 1):
    window = indices[i : i + seq_len]
    inputs.append(window[:-1])
    targets.append(window[-1])

inputs = torch.tensor(inputs, dtype=torch.long)
targets = torch.tensor(targets, dtype=torch.long)

class SimpleTransformerLM(nn.Module):
    def __init__(self, vocab_size, d_model):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, d_model)
        self.query = nn.Linear(d_model, d_model)
        self.key = nn.Linear(d_model, d_model)
        self.value = nn.Linear(d_model, d_model)
        self.fc_out = nn.Linear(d_model, vocab_size)

    def forward(self, x):
        emb = self.embedding(x)

        Q = self.query(emb)
        K = self.key(emb)
        V = self.value(emb)

        scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(Q.shape[-1])
        attn_weights = torch.softmax(scores, dim=-1)
        context = torch.matmul(attn_weights, V)

        last_token = context[:, -1, :]
        logits = self.fc_out(last_token)
        return logits

d_model = 16
vocab_size = len(vocab)
model = SimpleTransformerLM(vocab_size, d_model)

criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.01)

num_epochs = 15

for epoch in range(num_epochs):
    optimizer.zero_grad()
    logits = model(inputs)
    loss = criterion(logits, targets)
    loss.backward()
    optimizer.step()
    print(f"Эпоха {epoch+1}/{num_epochs}, Loss: {loss.item():.4f}")

def generate_text(model, start_words, length=40):
    generated = [token_to_idx[w] for w in start_words]

    for _ in range(length - len(generated)):
        window = generated[-(seq_len - 1):]
        x = torch.tensor([window], dtype=torch.long)
        logits = model(x)
        next_token = torch.argmax(logits, dim=-1).item()
        # print(f"Контекст: {[idx_to_token[i] for i in window]} -> предсказано: {idx_to_token[next_token]}")
        generated.append(next_token)

    return [idx_to_token[i] for i in generated]

start_words = ["собака", "спит", "на", "диване"]
result = generate_text(model, start_words, length=40)

new_tokens = result[len(start_words):]

print("Входная последовательность:", " ".join(start_words))
print("Сгенерированные моделью токены:", " ".join(new_tokens))
print(f"Количество токенов, предсказанных моделью: {len(new_tokens)}")
print(f"Общая длина (вхождение + предсказанное): {len(result)} токенов")