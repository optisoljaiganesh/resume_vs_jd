import streamlit as st
import openai
from dotenv import load_dotenv
import os
from docx import Document
import fitz
import tempfile
import re
# Load environment variables from .env file
load_dotenv()

# Set up your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_summary(resume_content, jd_skills):
    # Updated prompt to include required skills in a list
    prompt = f"Given the provided resume and job description, summarize why the candidate is a suitable match and provide the skil match score based on the job description:\n\nResume Content:\n{resume_content}\n\nRequired Skills from JD:\n- {', '.join(jd_skills)}\n\nSummary:"
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=1000,  # Adjust as needed
        temperature=0.7,
        seed=123 
    )
    return response.choices[0].text.strip()

def extract_skills(text):
    return [line.strip() for line in text.lower().split("\n")]

# def calculate_matching_score(matching_skills, required_skills):
#     print("matching_skills", matching_skills)
#     print("required_skills", required_skills)
#     return min(len(matching_skills) / len(required_skills), 1) * 10

def extract_text_from_docx(docx_file):
    doc = Document(docx_file)
    full_text = ""
    for para in doc.paragraphs:
        full_text += para.text + "\n"
    return full_text

def find_sentences_with_word(paragraph, word):
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s', paragraph)
    sentences_with_word = []
    for sentence in sentences:
        if re.search(fr'\b{re.escape(word)}\b', sentence, re.IGNORECASE):
            sentences_with_word.append(sentence)
    return sentences_with_word

def extract_text_from_pdf(pdf_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        temp_pdf.write(pdf_file.read())
        temp_pdf_path = temp_pdf.name

    try:
        pdf_document = fitz.open(temp_pdf_path)
        full_text = ""
        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            full_text += page.get_text()

        return full_text
    finally:
        # Close and delete the temporary file after use
        pdf_document.close()
        os.unlink(temp_pdf_path)
    
def remove_sentence_with_word(paragraph, word):
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s', paragraph)
    filtered_sentences = []
    for sentence in sentences:
        if not re.search(fr'\b{re.escape(word)}\b', sentence, re.IGNORECASE):
            filtered_sentences.append(sentence)
    result_paragraph = ' '.join(filtered_sentences)
    return result_paragraph


def find_match_score(sentence):
    pattern = r'\b(\d+)/\d+\b'
    match = re.search(pattern, sentence)
    if match:
        score = match.group(1)
        return score
    return 0


def main():
    st.title("Resume Checker")

    resume_file = st.file_uploader("Upload your resume", type=["txt", "pdf", "docx"])
    jd_text = st.text_area("Enter the job description:")

    if resume_file and st.button("Check Resume"):
        try:
            if resume_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                resume_content = extract_text_from_docx(resume_file)
            elif resume_file.type == "application/pdf":
                resume_content = extract_text_from_pdf(resume_file)     
            else:
                resume_content = resume_file.read().decode("utf-8")

            jd_skills = extract_skills(jd_text)[1:]  # Skip the first line in JD text
            # resume_skills = extract_skills(resume_content)
            # matching_score = calculate_matching_score(resume_skills, jd_skills)
            resume_summary = generate_summary(resume_content, jd_skills)
            find_word = "score"
            match_score_wording = find_sentences_with_word(resume_summary, find_word)
            match_score_sentance = match_score_wording[0]
            filtered_paragraph = remove_sentence_with_word(resume_summary, find_word)
            match_score = int(find_match_score(match_score_sentance))

            st.subheader("Resume Summary:")
            st.write(filtered_paragraph)

            st.subheader("Skill Match Score:")
            st.write(match_score_sentance)  # Display matching score with two decimal places

            if match_score and match_score > 7:
                st.success("The resume closely matches the job description's required skills.")
            
        except UnicodeDecodeError:
            st.error("Error decoding the uploaded resume. Ensure the file is in a compatible format.")

if __name__ == "__main__":
    main()
