import re
import math
import torch
import torch.nn as nn
import torch.optim as optim

torch.manual_seed(5)

file = open("qa_dataset.txt", encoding="utf-8")
text = file.read()
file.close()

tokens = re.findall(r"\w+", text.lower())

vocab = sorted(set(tokens))

# print(tokens)
# print(vocab)

token_to_idx = {}
for i, word in enumerate(vocab):
    token_to_idx[word] = i

idx_to_token = {}
for word, i in token_to_idx.items():
    idx_to_token[i] = word

indices = []
for word in tokens:
    indices.append(token_to_idx[word])

seq_len = 30
inputs = []
targets = []
for i in range(len(indices) - seq_len + 1):
    window = indices[i : i + seq_len]
    inputs.append(window[:-1])
    targets.append(window[-1])

inputs = torch.tensor(inputs, dtype=torch.long)
targets = torch.tensor(targets, dtype=torch.long)

# print(inputs.shape)

class SimpleTransformerLM(nn.Module):
    def __init__(self, vocab_size, d_model, max_len):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, d_model)
        self.query = nn.Linear(d_model, d_model)
        self.key = nn.Linear(d_model, d_model)
        self.value = nn.Linear(d_model, d_model)
        self.fc_out = nn.Linear(d_model, vocab_size)

        self.pos_embedding = nn.Embedding(max_len, d_model)

        self.ffn_1 = nn.Linear(d_model, d_model * 4)
        self.relu = nn.ReLU()
        self.ffn_2 = nn.Linear(d_model * 4, d_model)

    def forward(self, x):
        word_emb = self.embedding(x)

        seq_length = x.shape[1]
        positions = torch.arange(seq_length)
        pos_emb = self.pos_embedding(positions)

        emb = word_emb + pos_emb

        Q = self.query(emb)
        K = self.key(emb)
        V = self.value(emb)

        scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(Q.shape[-1])
        attn_weights = torch.softmax(scores, dim=-1)
        context = torch.matmul(attn_weights, V)

        ffn_hidden = self.ffn_1(context)
        ffn_hidden = self.relu(ffn_hidden)
        ffn_output = self.ffn_2(ffn_hidden)

        context = context + ffn_output

        last_token = context[:, -1, :]
        logits = self.fc_out(last_token)
        return logits

d_model = 64
vocab_size = len(vocab)
model = SimpleTransformerLM(vocab_size, d_model, seq_len)

criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

batch_size = 32
num_samples = inputs.shape[0]
num_epochs = 300

for epoch in range(num_epochs):
    permutation = torch.randperm(num_samples)
    shuffled_inputs = inputs[permutation]
    shuffled_targets = targets[permutation]

    total_loss = 0
    num_batches = 0

    for start in range(0, num_samples, batch_size):
        batch_inputs = shuffled_inputs[start : start + batch_size]
        batch_targets = shuffled_targets[start : start + batch_size]

        optimizer.zero_grad()
        logits = model(batch_inputs)
        loss = criterion(logits, batch_targets)
        loss.backward()
        optimizer.step()

        total_loss = total_loss + loss.item()
        num_batches = num_batches + 1

    average_loss = total_loss / num_batches

    if (epoch + 1) % 20 == 0:
        print(f"Эпоха {epoch+1}/{num_epochs}, средний Loss: {average_loss:.4f}")

def generate_text(model, start_words, length=250):
    generated = [token_to_idx[w] for w in start_words]

    for _ in range(length - len(generated)):
        window = generated[-(seq_len - 1):]

        if len(window) < seq_len - 1:
            how_many_missing = (seq_len - 1) - len(window)
            padding = [window[0]] * how_many_missing
            window = padding + window

        x = torch.tensor([window], dtype=torch.long)
        logits = model(x)
        probs = torch.softmax(logits, dim=-1)
        next_token = torch.multinomial(probs, num_samples=1).item()
        generated.append(next_token)

        word = idx_to_token[next_token]
        if word.startswith("конец"):
            break

    return [idx_to_token[i] for i in generated]

seeds = []

seeds.append(["начало_бизнес_требования", "объект", "страница", "каталога", "курсов",
              "otus", "направление", "программирование", "адрес",
              "otus_ru_catalog_courses_categories_programming", "бт_01"])

seeds.append(["начало_тесткейс", "id", "тк_01", "название", "фильтрация", "каталога",
              "по", "направлению", "тестирование", "требование", "бт_01",
              "предусловия", "открыта", "страница", "каталога", "курсов", "otus", "шаг", "1"])

seeds.append(["начало_чеклист", "название", "чек", "лист", "проверки", "страницы",
              "каталога", "курсов", "otus", "объект", "страница", "каталога",
              "курсов", "otus", "направление", "программирование", "пункт", "1"])

seeds.append(["начало_тестплан", "название", "тестовый", "план", "проверки", "страницы",
              "каталога", "курсов", "otus", "объект", "тестирования", "страница",
              "каталога", "курсов", "otus", "направление", "программирование", "основание"])

seeds.append(["начало_отчет", "название", "отчет", "о", "тестировании", "страницы",
              "каталога", "курсов", "otus", "объект", "тестирования", "страница",
              "каталога", "курсов", "otus", "направление", "программирование", "всего"])

case_seeds = []

case_seeds.append(["начало_тесткейс", "id", "тк_01", "название", "фильтрация", "каталога",
                   "по", "направлению", "тестирование", "требование", "бт_01",
                   "предусловия", "открыта", "страница", "каталога", "курсов", "otus", "шаг", "1"])

case_seeds.append(["начало_тесткейс", "id", "тк_02", "название", "совместная", "работа",
                   "фильтров", "направление", "и", "уровень", "требование", "бт_02",
                   "предусловия", "открыта", "страница", "каталога", "курсов", "otus", "шаг", "1"])

case_seeds.append(["начало_тесткейс", "id", "тк_03", "название", "поиск", "курса",
                   "по", "несуществующему", "названию", "требование", "бт_05",
                   "предусловия", "открыта", "страница", "каталога", "курсов", "otus", "шаг", "1"])

print("")
print("========== БИЗНЕС-ТРЕБОВАНИЯ ==========")
result = generate_text(model, seeds[0], length=250)
print(" ".join(result))

print("")
print("========== ТЕСТ-КЕЙСЫ ==========")
for i in range(3):
    result = generate_text(model, case_seeds[i], length=250)
    print("")
    print(f"--- Тест-кейс {i+1} ---")
    print(" ".join(result))

print("")
print("========== ЧЕК-ЛИСТ ==========")
result = generate_text(model, seeds[2], length=250)
print(" ".join(result))

print("")
print("========== ТЕСТОВЫЙ ПЛАН ==========")
result = generate_text(model, seeds[3], length=250)
print(" ".join(result))

print("")
print("========== ОТЧЁТ О ТЕСТИРОВАНИИ ==========")
result = generate_text(model, seeds[4], length=250)
print(" ".join(result))