import sys
import docx
import os

def read():
    for f in os.listdir('.'):
        if f.endswith('.docx') and ('Follow up' in f or 'Meeting' in f):
            print('\n===', f, '===')
            try:
                doc = docx.Document(f)
                for para in doc.paragraphs:
                    if para.text.strip(): print(para.text)
            except Exception as e:
                print(e)

if __name__ == '__main__':
    read()
