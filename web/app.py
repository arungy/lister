from flask import Flask, render_template, request, redirect, url_for, flash
import json, uuid, tempfile, shutil

app = Flask(__name__)
app.secret_key = "supersecretkey"
STORAGE_FILE = "listerlogs.json"
MAX_TASKS = 3
MAX_TASK_LEN = 120

PRIORITY_LABELS = {1: "High", 2: "Medium", 3: "Low"}

def load_tasks():
    try:
        with open(STORAGE_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("tasks", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_tasks(tasks):
    with tempfile.NamedTemporaryFile('w', delete=False, encoding="utf-8") as tf:
        json.dump({"tasks": tasks}, tf, indent=2)
    shutil.move(tf.name, STORAGE_FILE)

@app.route("/")
def index():
    tasks = sorted(load_tasks(), key=lambda t: t.get("priority", 2))
    active_count = sum(1 for t in tasks if not t["completed"])
    return render_template("index.html", tasks=tasks, max_task_len=MAX_TASK_LEN, max_tasks=MAX_TASKS,
                           active_count=active_count, PRIORITY_LABELS=PRIORITY_LABELS)

@app.route("/add", methods=["POST"])
def add():
    tasks = load_tasks()
    text = request.form.get("text", "").strip()
    priority = request.form.get("priority", "2")
    try:
        priority = int(priority)
        if priority not in PRIORITY_LABELS:
            priority = 2
    except ValueError:
        priority = 2
    if not text:
        flash("Task cannot be empty!", "error")
    elif len(text) > MAX_TASK_LEN:
        flash(f"Task too long! Max {MAX_TASK_LEN} characters.", "error")
    elif sum(not t["completed"] for t in tasks) >= MAX_TASKS:
        flash(f"Cannot add more than {MAX_TASKS} active tasks.", "error")
    elif any(t["text"].lower() == text.lower() and not t["completed"] for t in tasks):
        flash("This task already exists.", "error")
    else:
        tasks.append({"id": str(uuid.uuid4()), "text": text, "completed": False, "priority": priority})
        save_tasks(tasks)
        flash("Task added successfully!", "success")
    return redirect(url_for("index"))

@app.route("/edit/<task_id>", methods=["POST"])
def edit(task_id):
    tasks = load_tasks()
    text = request.form.get("text", "").strip()
    priority = request.form.get("priority", "2")
    try:
        priority = int(priority)
        if priority not in PRIORITY_LABELS:
            priority = 2
    except ValueError:
        priority = 2
    if not text:
        flash("Task cannot be empty!", "error")
    elif len(text) > MAX_TASK_LEN:
        flash(f"Task too long! Max {MAX_TASK_LEN} characters.", "error")
    else:
        for task in tasks:
            if task["id"] == task_id:
                task["text"] = text
                task["priority"] = priority
                save_tasks(tasks)
                flash("Task updated successfully!", "success")
                break
    return redirect(url_for("index"))

@app.route("/toggle/<task_id>", methods=["POST"])
def toggle(task_id):
    tasks = load_tasks()
    for task in tasks:
        if task["id"] == task_id:
            task["completed"] = not task["completed"]
            save_tasks(tasks)
            break
    return redirect(url_for("index"))

@app.route("/delete/<task_id>", methods=["POST"])
def delete(task_id):
    tasks = load_tasks()
    tasks = [t for t in tasks if t["id"] != task_id]
    save_tasks(tasks)
    flash("Task deleted successfully!", "success")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=False)
