import os
import re
import pdfplumber
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
import json

# Заранее подготовленные замены
replacements = {
    "dead_soul_randomly_removed.pdf": [
        {
            "page": 6,
            "line": 16,
            "start_char": 26,
            "end_char": 42,
            "removed_text": "два часа времени",
            "type": "multiple_words"
        }
    ],
    "dead_soul_randomly_removed.pdf": [
        {
            "page": 2,
            "line": 32,
            "start_char": 24,
            "end_char": 26,
            "removed_text": "же",
            "type": "word"
        }
    ],
    "dead_soul_randomly_removed.pdf": [
        {
            "page": 2,
            "line": 38,
            "start_char": 30,
            "end_char": 48,
            "removed_text": "с такими огромными",
            "type": "multiple_words"
        }
    ]
}


def extract_text(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            pages = [page.extract_text() for page in pdf.pages]
        return pages
    except Exception as e:
        print(f"Ошибка при извлечении текста из {pdf_path}: {e}")
        return []


def replace_text(original_text, replacement_info):
    line_num = replacement_info['line'] - 1
    start_char = replacement_info['start_char']
    end_char = replacement_info['end_char']
    replacement = replacement_info['replacement']
    mask_type = replacement_info['type']

    lines = original_text.split('\n')
    if line_num >= len(lines):
        print(f"Линия {replacement_info['line']} отсутствует в документе.")
        return original_text, []

    line = lines[line_num]
    masked_span = line[start_char:end_char]

    new_line = line[:start_char] + replacement + line[end_char:]
    lines[line_num] = new_line
    restored_text = '\n'.join(lines)

    info = {
        "page": replacement_info['page'],
        "line": replacement_info['line'],
        "start_char": start_char,
        "end_char": end_char,
        "type": mask_type
    }

    return restored_text, info


def highlight_replacement(c, x, y, text, underline=True):
    c.setFillColor(colors.black)
    c.drawString(x, y, text)
    if underline:
        text_width = c.stringWidth(text, "Helvetica", 12)
        c.setStrokeColor(colors.red)
        c.setLineWidth(1)
        c.line(x, y - 2, x + text_width, y - 2)


def create_restored_pdf(original_text, replacements_info, output_pdf_path):
    c = canvas.Canvas(output_pdf_path, pagesize=A4)
    width, height = A4
    margin = 20 * mm
    text_object = c.beginText(margin, height - margin)
    text_object.setFont("Helvetica", 12)

    lines = original_text.split('\n')
    for line_num, line in enumerate(lines, start=1):
        line_replacements = [r for r in replacements_info if r['line'] == line_num]
        if line_replacements:
            current_pos = 0
            for rep in line_replacements:
                start = rep['start_char']
                end = rep['end_char']
                replacement = rep['replacement']

                pre_text = line[current_pos:start]
                text_object.textLine(pre_text)

                c.drawText(text_object)
                x = margin + c.stringWidth(pre_text, "Helvetica", 12)
                y = height - margin - (line_num * 14)  # 14 - высота строки
                highlight_replacement(c, x, y, replacement)

                current_pos = end
            post_text = line[current_pos:]
            text_object.textLine(post_text)
        else:
            text_object.textLine(line)

    c.drawText(text_object)
    c.save()


def process_pdf(pdf_filename):
    if pdf_filename not in replacements:
        print(f"Нет замен для {pdf_filename}.")
        return

    pages = extract_text(pdf_filename)
    if not pages:
        print(f"Не удалось извлечь текст из {pdf_filename}.")
        return

    pdf_replacements = replacements[pdf_filename]

    restored_pages = []
    logs = []

    for page_num, page_text in enumerate(pages, start=1):
        page_replacements = [r for r in pdf_replacements if r['page'] == page_num]
        if page_replacements:
            for rep in page_replacements:
                restored_text, info = replace_text(page_text, rep)
                page_text = restored_text
                logs.append(info)
        restored_pages.append(page_text)

    restored_text = '\n'.join(restored_pages)
    output_pdf = pdf_filename.replace(".pdf", "_restored.pdf")
    create_restored_pdf(restored_text, pdf_replacements, output_pdf)

    for log in logs:
        print(
            f"page: {log['page']}, line: {log['line']}, start_char: {log['start_char']}, end_char: {log['end_char']}, type: {log['type']}")


def main():
    pdf_files = ["dead_soul_randomly_removed.pdf"]
    for pdf in pdf_files:
        print(f"\nОбработка файла: {pdf}")
        process_pdf(pdf)
        print(f"Восстановленный PDF сохранён как {pdf.replace('.pdf', '_restored.pdf')}\n")


if __name__ == "__main__":
    main()
