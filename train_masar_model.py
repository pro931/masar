# ✅ تدريب موديل مسار الذكي على بيانات masar_smart_dataset.csv
import pandas as pd
import torch
from torch.utils.data import Dataset
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, Trainer, TrainingArguments

# ✅ تحميل بيانات الأسئلة الذكية
faq_df = pd.read_csv("masar_smart_dataset.csv")
faq_df.dropna(inplace=True)
faq_df['question'] = faq_df['question'].str.lower().str.strip()
faq_df['answer'] = faq_df['answer'].str.strip()

# ✅ إعداد الداتا ككائن Dataset
class MasarDataset(Dataset):
    def __init__(self, dataframe, tokenizer, max_length=128):
        self.questions = dataframe['question'].tolist()
        self.answers = dataframe['answer'].tolist()
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.questions)

    def __getitem__(self, idx):
        q = str(self.questions[idx])
        a = str(self.answers[idx])
        inputs = self.tokenizer(f"question: {q}", max_length=self.max_length, padding="max_length", truncation=True, return_tensors="pt")
        targets = self.tokenizer(a, max_length=self.max_length, padding="max_length", truncation=True, return_tensors="pt")
        return {
            'input_ids': inputs['input_ids'].squeeze(),
            'attention_mask': inputs['attention_mask'].squeeze(),
            'labels': targets['input_ids'].squeeze()
        }

# ✅ تحميل النموذج والمحول
model_name = "t5-small"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

dataset = MasarDataset(faq_df, tokenizer)

# ✅ إعدادات التدريب
training_args = TrainingArguments(
    output_dir="./masar_model",
    num_train_epochs=5,
    per_device_train_batch_size=8,
    save_strategy="epoch",
    logging_dir="./logs",
    logging_steps=10,
    save_total_limit=1,
    evaluation_strategy="no"
)

# ✅ تدريب الموديل
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset
)

trainer.train()

# ✅ حفظ النموذج المدرب
model.save_pretrained("./masar_model11")
tokenizer.save_pretrained("./masar_model11")

print("\n✅ تم تدريب موديل مسار الذكي وحفظه بنجاح!")
