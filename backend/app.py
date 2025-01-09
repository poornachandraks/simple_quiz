from flask import Flask, request, jsonify
from flask_cors import CORS
from database import db, Quiz, Question, Option, QuizAttempt
import os

app = Flask(__name__)
CORS(app)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Create tables
with app.app_context():
    db.create_all()

@app.route('/', methods=['GET'])
def home():
    return "Hello World"

def create_quiz():
    data = request.json
    new_quiz = Quiz(title=data['title'])
    db.session.add(new_quiz)
    
    for q_data in data['questions']:
        question = Question(quiz_id=new_quiz.id, question_text=q_data['question'])
        db.session.add(question)
        
        for opt_data in q_data['options']:
            option = Option(
                question_id=question.id,
                option_text=opt_data['text'],
                is_correct=opt_data['isCorrect']
            )
            db.session.add(option)
    
    db.session.commit()
    return jsonify({'message': 'Quiz created successfully', 'quiz_id': new_quiz.id})

@app.route('/api/quizzes', methods=['GET'])
def get_quizzes():
    quizzes = Quiz.query.all()
    return jsonify([{
        'id': quiz.id,
        'title': quiz.title,
        'created_at': quiz.created_at
    } for quiz in quizzes])

@app.route('/api/quiz/<int:quiz_id>', methods=['GET'])
def get_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = []
    
    for question in quiz.questions:
        options = [{
            'id': opt.id,
            'text': opt.option_text,
            'isCorrect': opt.is_correct
        } for opt in question.options]
        
        questions.append({
            'id': question.id,
            'question': question.question_text,
            'options': options
        })
    
    return jsonify({
        'id': quiz.id,
        'title': quiz.title,
        'questions': questions
    })

@app.route('/api/quiz/attempt', methods=['POST'])
def submit_attempt():
    data = request.json
    quiz_id = data['quiz_id']
    answers = data['answers']
    
    quiz = Quiz.query.get_or_404(quiz_id)
    score = 0
    total_questions = len(quiz.questions)
    
    for answer in answers:
        question = Question.query.get(answer['question_id'])
        correct_option = Option.query.filter_by(
            question_id=question.id,
            is_correct=True
        ).first()
        
        if answer['selected_option_id'] == correct_option.id:
            score += 1
    
    attempt = QuizAttempt(quiz_id=quiz_id, score=score)
    db.session.add(attempt)
    db.session.commit()
    
    return jsonify({
        'score': score,
        'total': total_questions,
        'percentage': (score/total_questions) * 100
    })

if __name__ == '__main__':
    app.run(debug=True) 