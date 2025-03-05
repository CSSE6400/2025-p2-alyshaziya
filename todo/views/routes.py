from flask import Blueprint, jsonify, request
from todo.models import db
from todo.models.todo import Todo
from datetime import datetime
from datetime import timedelta

 
api = Blueprint('api', __name__, url_prefix='/api/v1') 

TEST_ITEM = {
    "id": 1,
    "title": "Watch CSSE6400 Lecture",
    "description": "Watch the CSSE6400 lecture on ECHO360 for week 1",
    "completed": True,
    "deadline_at": "2023-02-27T00:00:00",
    "created_at": "2023-02-20T00:00:00",
    "updated_at": "2023-02-20T00:00:00"
}
 
@api.route('/health') 
def health():
    """Return a status of 'ok' if the server is running and listening to request"""
    return jsonify({"status": "ok"})


@api.route('/todos', methods=['GET'])
def get_todos():
    """Return the list of todo items"""

    query = Todo.query

    complete = request.args.get('completed')
    
    #check for completed
    if complete is not None:
        completed_check = complete.lower() == 'true' #case sensitive
        query = query.filter_by(completed=completed_check)


    #check for window
    window = request.args.get('window')
    if window is not None:
        try:
            window_days = int(window)
            deadline_threshold = datetime.now() + timedelta(days=window_days)
            query = query.filter(Todo.deadline_at <= deadline_threshold)
        except ValueError:
            return jsonify({"error": "Invalid window parameter"}), 400
        
    todos = query.all()
    
    return jsonify([todo.to_dict() for todo in todos])


@api.route('/todos/<int:todo_id>', methods=['GET'])
def get_todo(todo_id):
    """Return the details of a todo item"""
    todo = Todo.query.get(todo_id)
    if todo is None:
        return jsonify({'error': 'Todo not found'}), 404
    return jsonify(todo.to_dict())



@api.route('/todos', methods=['POST'])
def create_todo():
    """Create a new todo item and return the created item"""

    # missing title error
    if 'title' not in request.json or not request.json['title']:
        return jsonify({'error': 'Title is required'}), 400

    valid_fields = {'title', 'description', 'completed', 'deadline_at'} # only accept these

    extra_fields = set(request.json.keys()) - valid_fields
    if extra_fields:
        # reject extra fields
        return jsonify({'error': f'Invalid fields: {", ".join(extra_fields)}'}), 400 

    todo = Todo(
        title=request.json.get('title'),
        description=request.json.get('description'),
        completed=request.json.get('completed', False),
    )

    if 'deadline_at' in request.json:
        todo.deadline_at = datetime.fromisoformat(request.json.get('deadline_at'))

    db.session.add(todo)
    db.session.commit()
    return jsonify(todo.to_dict()), 201


@api.route('/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    """Update a todo item and return the updated item"""
    todo = Todo.query.get(todo_id)

    if todo is None:
        return jsonify({'error': 'Todo not found'}), 404

    if 'id' in request.json: # if id in req return error
        return jsonify({'error': 'ID cannot be modified'}), 400  # cant change id

    # same as before, reject extra fields
    valid_fields = {'title', 'description', 'completed', 'deadline_at'}
    extra_fields = set(request.json.keys()) - valid_fields
    if extra_fields:
        return jsonify({'error': f'Invalid fields: {", ".join(extra_fields)}'}), 400
    
    todo.title = request.json.get('title', todo.title)
    todo.description = request.json.get('description', todo.description)
    todo.completed = request.json.get('completed', todo.completed)
    
    if 'deadline_at' in request.json:
        todo.deadline_at = datetime.fromisoformat(request.json.get('deadline_at'))

    db.session.commit()
    return jsonify(todo.to_dict())


@api.route('/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    """Delete a todo item and return the deleted item"""
    todo = Todo.query.get(todo_id)
    if todo is None:
        return jsonify({}), 200
    
    db.session.delete(todo)
    db.session.commit()
    return jsonify(todo.to_dict()), 200

 
