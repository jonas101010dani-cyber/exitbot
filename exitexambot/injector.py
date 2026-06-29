import sqlite3
import re
import os
import json

def extract_and_inject_questions():
    print("⏳ የዳታቤዝ ፋይል በመፍጠር ላይ...")
    conn = sqlite3.connect('manual_exam.db')
    cursor = conn.cursor()
    
    # ሰንጠረዥ መፍጠር
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            department TEXT,
            question_text TEXT,
            option_A TEXT,
            option_B TEXT,
            option_C TEXT,
            option_D TEXT,
            correct_option TEXT
        )
    ''')
    
    # የድሮ ዳታ ካለ እንዳይደራረብ ማጽዳት
    cursor.execute("DELETE FROM questions")
    conn.commit()

    files = [
        {"name": "EXIT 2016.html", "year": "2016"},
        {"name": "EXIT 2017.html", "year": "2017"},
        {"name": "EXIT 2018.html", "year": "2018"}
    ]
    
    total_injected = 0

    for f in files:
        if not os.path.exists(f["name"]):
            print(f"❌ ፋይሉ አልተገኘም: {f['name']} (እባክህ በአንድ ፎልደር ውስጥ መሆናቸውን አረጋግጥ)")
            continue
            
        try:
            print(f"⏳ ፋይሉን በማንበብ ላይ: {f['name']}...")
            with open(f["name"], "r", encoding="utf-8") as file:
                content = file.read()
                
                # በጃቫስክሪፕት ውስጥ ያለውን const questionsData = [ ... ]; ክፍል መፈለግ
                match = re.search(r'const\s+questionsData\s*=\s*(\s*\[.*?\])\s*;', content, re.DOTALL)
                
                if match:
                    js_array = match.group(1)
                    
                    # እያንዳንዱን የጥያቄ ብሎክ {id:..., domain:..., text:..., options:[...], answer:...} መለየት
                    blocks = re.findall(r'\{\s*id\s*:\s*\d+.*?\s*text\s*:\s*["\'](.*?)["\']\s*,\s*options\s*:\s*\[(.*?)\]\s*,\s*answer\s*:\s*["\'](.*?)["\']\s*\}', js_array, re.DOTALL)
                    
                    file_questions_count = 0
                    for q_text, opts_text, answer in blocks:
                        # በኮማ የተከፋፈሉትን ምርጫዎች ማውጣት
                        options = re.findall(r'["\'](.*?)["\']', opts_text)
                        
                        if len(options) >= 4:
                            clean_q = f"[{f['year']} Exit Exam] " + q_text.replace('\\"', '"').replace("\\'", "'").strip()
                            opt_a = options[0].replace('\\"', '"').replace("\\'", "'").strip()
                            opt_b = options[1].replace('\\"', '"').replace("\\'", "'").strip()
                            opt_c = options[2].replace('\\"', '"').replace("\\'", "'").strip()
                            opt_d = options[3].replace('\\"', '"').replace("\\'", "'").strip()
                            
                            clean_correct = answer.strip().upper()
                            
                            cursor.execute('''
                                INSERT INTO questions (department, question_text, option_A, option_B, option_C, option_D, correct_option)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            ''', ("Computer Science", clean_q, opt_a, opt_b, opt_c, opt_d, clean_correct))
                            total_injected += 1
                            file_questions_count += 1
                            
                    print(f"✅ ከ {f['name']} ላይ {file_questions_count} ጥያቄዎች ወጥተዋል።")
                else:
                    print(f"❌ በፋይሉ ውስጥ የ questionsData አደራደር አልተገኘም: {f['name']}")
            
        except Exception as e:
            print(f"❌ ስህተት በ {f['name']}: {e}")

    conn.commit()
    conn.close()
    print(f"\n🎉 በተሳካ ሁኔታ {total_injected} ጥያቄዎች ወደ 'manual_exam.db' ገብተዋል!")

if __name__ == "__main__":
    extract_and_inject_questions()