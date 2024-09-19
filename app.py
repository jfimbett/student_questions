# app.py
#%%
from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import json
from datetime import datetime
import openai 

import os
from openai import OpenAI
#%%

def ask_question_llm(prompt, responses, original_question):
    client = OpenAI(
        # This is the default and can be omitted
        api_key=os.environ.get("OPENAI_API_KEY"),
    )

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"""
                My students have answered the following question: {original_question}


                Here are the responses:

                {responses}

                Based on the responses answer this:

                {prompt}
                """,
            }
        ],
        model="gpt-4-turbo",
    )

    return chat_completion.choices[0].message.content

#%%


app = Flask(__name__)

# Create a directory to store responses if it doesn't exist
RESPONSES_DIR = 'responses'
os.makedirs(RESPONSES_DIR, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        name = request.form.get('name')
        last_name = request.form.get('last_name')
        answer = request.form.get('answer')
        date = datetime.now().strftime('%Y-%m-%d')
        
        # Structure to store the response
        response = {
            'name': name,
            'last_name': last_name,
            'answer': answer
        }

        # Save the response as a JSON file
        session_path = os.path.join(RESPONSES_DIR, date)
        os.makedirs(session_path, exist_ok=True)
        with open(os.path.join(session_path, f'{name}_{last_name}.json'), 'w') as f:
            json.dump(response, f)
        
        return redirect(url_for('form'))

    # Render the form template
    return render_template('form.html')

@app.route('/responses/<session_date>', methods=['GET'])
def view_responses(session_date):
    try:
        session_path = os.path.join(RESPONSES_DIR, session_date)
        if not os.path.exists(session_path):
            return f'No responses for this date: {session_date}', 404

        responses = []
        for filename in os.listdir(session_path):
            if filename.endswith('.json'):
                with open(os.path.join(session_path, filename), 'r') as f:
                    data = json.load(f)
                    responses.append({'answer': data['answer']})

        print(responses)
        return render_template('responses.html', responses=responses, session_date=session_date)
    except Exception as e:
        return str(e), 500

@app.route('/query_llm/<session_date>', methods=['GET', 'POST'])
def query_llm(session_date):
    try:
        # Retrieve original question asked to students
        original_question = request.args.get('original_question', default='', type=str)
        
        if request.method == 'POST':
            question = request.form.get('question')
            responses = get_responses_as_string(session_date)
            
            if responses == '':
                return f'No responses found for the session: {session_date}', 404

            # Use the provided ask_question_llm function to get the LLM response
            llm_response = ask_question_llm(prompt=question, responses=responses, original_question=original_question)

            return render_template('query_llm.html', session_date=session_date, question=question, llm_response=llm_response, original_question=original_question)
        
        return render_template('query_llm.html', session_date=session_date, original_question=original_question)
    except Exception as e:
        return str(e), 500

def get_responses_as_string(session_date):
    session_path = os.path.join(RESPONSES_DIR, session_date)
    if not os.path.exists(session_path):
        return ''
    
    all_responses = []
    for filename in os.listdir(session_path):
        if filename.endswith('.json'):
            with open(os.path.join(session_path, filename), 'r') as f:
                data = json.load(f)
                all_responses.append(data['answer'])
    
    return ' '.join(all_responses)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

# %%
