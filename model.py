# ✅ مسار شات بوت - نسخة محسنة ومرتبة
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import os

# ✅ المسارات
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "masar_model11")
DATASET_FAQ = os.path.join(BASE_DIR, "dataset1.csv")
DATASET_TICKETS = os.path.join(BASE_DIR, "dataset.csv")

# ✅ تحميل النموذج المحفوظ
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR, local_files_only=True)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_DIR, local_files_only=True)

# ✅ تحميل البيانات
faq_df = pd.read_csv(DATASET_FAQ, quotechar='\"', skipinitialspace=True)
if faq_df.shape[1] == 1:
    faq_df = faq_df[faq_df.columns[0]].str.split(",", n=1, expand=True)
    faq_df.columns = ['question', 'answer']

tickets_df = pd.read_csv(DATASET_TICKETS)

# ✅ تنظيف الأسئلة
faq_df['question'] = faq_df['question'].str.lower().str.strip()
faq_df['answer'] = faq_df['answer'].str.strip()

# ✅ إنشاء قاموس الأسئلة والأجوبة
faq_dict = dict(zip(faq_df['question'], faq_df['answer']))

# ✅ دالة للتحقق من وجود تذكرة في السؤال
def check_ticket_and_respond(question):
    for ticket_id in tickets_df['Ticket_ID']:
        if str(ticket_id) in question:
            row = tickets_df[tickets_df['Ticket_ID'] == ticket_id].iloc[0]
            return f"\n🎫 تفاصيل التذكرة رقم {ticket_id}:\n" \
                   f"🏟️ المباراة: {row['Match']}\n📍 الملعب: {row['Stadium']}\n📦 البلوك: {row['Block']}\n" \
                   f"🔢 الصف: {row['Row']} | الكرسي: {row['Seat']}\n🚪 البوابة: {row['Gate']}\n" \
                   f"🅿️ الموقف: {row['Parking_Zone']}\n💰 السعر: {row['Ticket_Price']} | التصنيف: {row['Category']}"
    return None

# ✅ توليد الرد
def generate_response(question):
    question = question.lower().strip()

    if question in faq_dict:
        return faq_dict[question]

    ticket_response = check_ticket_and_respond(question)
    if ticket_response:
        return ticket_response

    inputs = tokenizer(f"question: {question}", return_tensors="pt", truncation=True, max_length=128)
    outputs = model.generate(inputs.input_ids, attention_mask=inputs.attention_mask, max_length=128)
    decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # ✅ طباعة التصحيح فقط أثناء التطوير
    print("🛠️ input:", question)
    print("🛠️ decoded:", decoded)

    return decoded

# ✅ واجهة الاستخدام الطرفية
if __name__ == '__main__':
    print("🤖 مرحبًا بك في مساعد مسار الذكي! أكتب سؤالك أو رقم تذكرتك ✨")
    while True:
        user_input = input("\n💬 أنت: ")
        if user_input.strip().lower() in ['خروج', 'exit', 'quit']:
            print("🫡 إلى اللقاء!")
            break
        response = generate_response(user_input)
        print("🤖 مسار:", response)
