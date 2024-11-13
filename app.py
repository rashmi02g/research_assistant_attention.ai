import streamlit as st
import requests
from xml.etree import ElementTree as ET
from database import Neo4jDatabase
from transformers import pipeline


db = Neo4jDatabase(password="p02022020@") 


summarizer = pipeline("summarization")
qa_pipeline = pipeline("question-answering")

def search_papers(topic, max_results=5):
    base_url = "http://export.arxiv.org/api/query?"
    search_url = f"{base_url}search_query=all:{topic}&start=0&max_results={max_results}"

    response = requests.get(search_url)
    papers = []

    if response.status_code == 200:
       
        root = ET.fromstring(response.text)
        for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
            title = entry.find("{http://www.w3.org/2005/Atom}title").text
            published = entry.find("{http://www.w3.org/2005/Atom}published").text
            year = published[:4] 
            papers.append({"title": title, "year": year})
    else:
        st.error("Error fetching papers. Please try again.")

    return papers if papers else [{"title": "No papers found", "year": "N/A"}]


def summarize_papers(papers):
    summaries = []
    for paper in papers[:3]:
        summary = summarizer(paper['title'], max_length=30, min_length=15, do_sample=False)
        summaries.append({"title": paper['title'], "year": paper['year'], "summary": summary[0]['summary_text']})
    return summaries


def answer_question(context, question):
    response = qa_pipeline(question=question, context=context)
    return response['answer']


if 'summaries' not in st.session_state:
    st.session_state.summaries = []
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []


st.title("Academic Research Paper Assistant")


st.write("### Search for Research Papers")
topic = st.text_input("Enter a Research Topic:")
max_results = st.slider("Select number of papers to display", 1, 10, 5)
if st.button("Search"):
    papers = search_papers(topic, max_results)
    if papers and papers[0]["title"] != "No papers found":
        
        st.session_state.summaries = summarize_papers(papers)
        
        
        st.write("### Summarized Papers")
        for paper in st.session_state.summaries:
            title = paper['title']
            year = paper['year']
            summary = paper['summary']
            st.write(f"**Title:** {title}")
            st.write(f"**Year:** {year}")
            st.write(f"**Summary:** {summary}")

          
            db.add_paper(title, year)

    
        st.session_state.chat_history.append({"role": "bot", "content": f"Found and summarized papers on {topic}."})
    else:
        st.write("No papers found for the given topic.")


st.write("### Chat History")
for message in st.session_state.chat_history:
    role = "User" if message["role"] == "user" else "Assistant"
    st.write(f"**{role}:** {message['content']}")


question = st.text_input("Ask a question about the papers:")
if question:
    
    st.session_state.chat_history.append({"role": "user", "content": question})
    
    
    answers = []
    for paper in st.session_state.summaries:
        answer = answer_question(paper['summary'], question)
        answers.append(f"**{paper['title']}**: {answer}")
    
    
    response = "\n\n".join(answers)
    st.session_state.chat_history.append({"role": "bot", "content": response})

    
    st.write("### Assistant's Answer")
    st.write(response)
