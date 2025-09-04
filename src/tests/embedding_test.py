import torch
from transformers import AutoModel, AutoTokenizer

def cal_score(a, b):
    print(f"이게 원본 a.shape: {a.shape}")
    print(f"이게 원본 b.shape: {b.shape}")
    if len(a.shape) == 1: a = a.unsqueeze(0)
    if len(b.shape) == 1: b = b.unsqueeze(0)

    a_norm = a / a.norm(dim=1)[:, None]
    b_norm = b / b.norm(dim=1)[:, None]
    return torch.mm(a_norm, b_norm.transpose(0, 1)) * 100

model = AutoModel.from_pretrained('BM-K/KoSimCSE-roberta-multitask') 
tokenizer = AutoTokenizer.from_pretrained('BM-K/KoSimCSE-roberta-multitask')

sentences = ['치타가 들판을 가로 질러 먹이를 쫓는다.',
             '치타 한 마리가 먹이 뒤에서 달리고 있다.',
             '원숭이 한 마리가 드럼을 연주한다.']

inputs = tokenizer(sentences, padding=True, truncation=True, return_tensors="pt")
print(inputs)
embeddings, _ = model(**inputs, return_dict=False)

score01 = cal_score(embeddings[0][0], embeddings[1][0])
score02 = cal_score(embeddings[0][0], embeddings[2][0])

print(score01)
print(score02)
