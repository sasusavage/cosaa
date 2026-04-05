from app import create_app, db
from app.models import User, Portfolio, Candidate, Vote

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Portfolio': Portfolio, 'Candidate': Candidate, 'Vote': Vote}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
