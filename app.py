from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import os
from datetime import datetime
import random
import math

app = Flask(__name__)

def calculate_1rm(weight, reps):
    return weight * (1 + (reps / 30))

def validate_input(weight_str):
    try:
        weight = float(weight_str)
        if weight <= 0:
            return False, "Please enter a weight greater than 0."
        return True, weight
    except ValueError:
        return False, "Please enter a valid number (e.g., 150)."

def get_movement_1rm(movement, use_feedback=True):
    if use_feedback and movement in movement_1rm_dict:
        return movement_1rm_dict[movement]
    if movement in ["Cable Chest Press", "Cable Incline Press", "Cable Decline Press", "Cable Chest Fly", "Push-up"]:
        return one_rm_dict["Bench Press"] * 1.0
    elif movement in ["Lat Pulldown", "Wide Grip Lat Pulldown", "Straight-Arm Pulldown"]:
        return one_rm_dict["Lat Pulldown"] * 1.0
    elif movement in ["Seated Row", "Single-Arm Row", "Face Pull", "Reverse Fly"]:
        return one_rm_dict["Lat Pulldown"] * 0.85
    elif movement in ["Tricep Pushdown", "Overhead Tricep Extension", "Tricep Kickback", "Dips"]:
        return one_rm_dict["Military Press"] * 0.35
    elif movement in ["Bicep Curl", "Hammer Curl", "Concentration Curl"]:
        return one_rm_dict["Lat Pulldown"] * 0.30
    elif movement in ["Squat", "Front Squat", "Goblet Squat", "Lunge", "Reverse Lunge", "Split Squat", "Bodyweight Squat"]:
        return one_rm_dict["Front Squat"] * 1.0
    elif movement in ["Shoulder Press", "Lateral Raise", "Front Raise", "Upright Row"]:
        return one_rm_dict["Military Press"] * 1.0
    elif movement in ["Cable Deadlift", "Romanian Deadlift"]:
        return one_rm_dict["Front Squat"] * 0.9
    elif movement in ["Cable Crunch", "Woodchopper", "Pallof Press", "Plank"]:
        return one_rm_dict["Front Squat"] * 0.25
    elif movement in ["Hip Abduction", "Hip Adduction", "Glute Kickback"]:
        return one_rm_dict["Front Squat"] * 0.5
    return 0

def is_two_handle_movement(movement):
    two_handle_movements = [
        "Cable Chest Press", "Cable Incline Press", "Cable Decline Press", "Cable Chest Fly",
        "Seated Row", "Single-Arm Row", "Face Pull", "Reverse Fly",
        "Tricep Pushdown", "Overhead Tricep Extension", "Tricep Kickback",
        "Bicep Curl", "Hammer Curl", "Concentration Curl",
        "Shoulder Press", "Lateral Raise", "Front Raise",
        "Hip Abduction", "Hip Adduction", "Glute Kickback"
    ]
    return movement in two_handle_movements

weights_dict = {}
one_rm_dict = {}
movement_1rm_dict = {}
feedback_data = {}
user_options = {"days_per_week": 3, "duration": "30 minutes", "bodyweight": False, "name": "", "gender": "", "height": "", "weight": ""}
workout_plans = {3: {}, 4: {}, 5: {}, 6: {}}
exercises = ["Bench Press", "Lat Pulldown", "Military Press", "Front Squat"]
all_movements = [
    "Cable Chest Press", "Cable Incline Press", "Cable Decline Press", "Cable Chest Fly",
    "Lat Pulldown", "Wide Grip Lat Pulldown", "Straight-Arm Pulldown",
    "Seated Row", "Single-Arm Row", "Face Pull", "Reverse Fly",
    "Tricep Pushdown", "Overhead Tricep Extension", "Tricep Kickback",
    "Bicep Curl", "Hammer Curl", "Concentration Curl",
    "Squat", "Front Squat", "Goblet Squat", "Lunge", "Reverse Lunge", "Split Squat",
    "Shoulder Press", "Lateral Raise", "Front Raise", "Upright Row",
    "Cable Deadlift", "Romanian Deadlift",
    "Cable Crunch", "Woodchopper", "Pallof Press",
    "Hip Abduction", "Hip Adduction", "Glute Kickback"
]
bodyweight_movements = ["Push-up", "Bodyweight Squat", "Dips", "Plank"]
stretches = ["Hamstring Stretch", "Quad Stretch", "Chest Opener", "Cat-Cow Stretch", "Side Bend"]
goal = ""

def save_user_data():
    with open("user_data.json", "w") as f:
        json.dump({"weights_dict": weights_dict, "movement_1rm_dict": movement_1rm_dict, "goal": goal, "options": user_options}, f)

def load_user_data():
    global weights_dict, one_rm_dict, movement_1rm_dict, goal, user_options
    if os.path.exists("user_data.json"):
        with open("user_data.json", "r") as f:
            data = json.load(f)
            weights_dict = data.get("weights_dict", {})
            movement_1rm_dict = data.get("movement_1rm_dict", {})
            one_rm_dict = {k: calculate_1rm(v, 5) for k, v in weights_dict.items()}
            goal = data.get("goal", "")
            user_options = data.get("options", user_options)
    if "days_per_week" not in user_options or user_options["days_per_week"] not in workout_plans:
        user_options["days_per_week"] = 3

def save_workout_plans():
    clean_plans = {int(k): v for k, v in workout_plans.items()}
    with open("workout_plans.json", "w") as f:
        json.dump(clean_plans, f)
    print("Saved workout_plans:", clean_plans)

def load_workout_plans():
    global workout_plans
    if os.path.exists("workout_plans.json"):
        with open("workout_plans.json", "r") as f:
            loaded = json.load(f)
            workout_plans = {int(k): v for k, v in loaded.items()}
    if not workout_plans.get(user_options["days_per_week"]):
        generate_weekly_plan()
    print("Loaded workout_plans:", workout_plans)

def generate_weekly_plan():
    days_per_week = user_options["days_per_week"]
    movements_per_day = {20: 3, 30: 4, 45: 5, 60: 6}[int(user_options["duration"].split()[0])]
    base_plans = {3: ["Push", "Pull", "Legs/Core"], 4: ["Push", "Pull", "Legs", "Core/Upper"], 5: ["Chest/Triceps", "Back/Biceps", "Legs", "Shoulders", "Core"], 6: ["Chest", "Back", "Legs", "Shoulders", "Arms", "Core"]}
    movement_groups = {
        "Push": ["Cable Chest Press", "Shoulder Press", "Tricep Pushdown", "Cable Incline Press", "Lateral Raise", "Cable Chest Fly"],
        "Pull": ["Lat Pulldown", "Seated Row", "Bicep Curl", "Face Pull", "Straight-Arm Pulldown", "Reverse Fly"],
        "Legs": ["Squat", "Lunge", "Cable Deadlift", "Glute Kickback", "Split Squat", "Front Squat"],
        "Core": ["Cable Crunch", "Woodchopper", "Pallof Press", "Plank"],
        "Chest": ["Cable Chest Press", "Cable Incline Press", "Cable Decline Press", "Cable Chest Fly"],
        "Back": ["Lat Pulldown", "Seated Row", "Single-Arm Row", "Straight-Arm Pulldown"],
        "Shoulders": ["Shoulder Press", "Lateral Raise", "Front Raise", "Upright Row"],
        "Arms": ["Tricep Pushdown", "Bicep Curl", "Overhead Tricep Extension", "Hammer Curl"],
    }
    bodyweight_alts = {"Cable Chest Press": "Push-up", "Lat Pulldown": "Bodyweight Squat", "Squat": "Bodyweight Squat", "Tricep Pushdown": "Dips", "Cable Crunch": "Plank"}
    new_plan = {}
    for i, focus in enumerate(base_plans[days_per_week]):
        day_name = f"Day {i+1} - {focus}"
        focus_areas = focus.split("/")
        available = []
        for area in focus_areas:
            if area in movement_groups:
                available.extend(movement_groups[area])
        available = list(set(available))
        if user_options["bodyweight"]:
            available = [bodyweight_alts.get(m, m) for m in available]
        selected = random.sample(available, min(movements_per_day, len(available)))
        new_plan[day_name] = selected
    workout_plans[days_per_week] = new_plan
    save_workout_plans()

def get_current_day():
    load_workout_plans()
    days = list(workout_plans[user_options["days_per_week"]].keys())
    if os.path.exists("current_day.txt"):
        with open("current_day.txt", "r") as f:
            try:
                day_num = int(f.read().strip())
                if 1 <= day_num <= len(days):
                    return days[day_num - 1]
            except ValueError:
                pass
    return days[0]

def calculate_progress_over_time():
    push_movements = ["Cable Chest Press", "Cable Incline Press", "Cable Decline Press", "Cable Chest Fly", "Shoulder Press", "Tricep Pushdown", "Lateral Raise", "Front Raise", "Upright Row", "Push-up", "Dips"]
    pull_movements = ["Lat Pulldown", "Wide Grip Lat Pulldown", "Straight-Arm Pulldown", "Seated Row", "Single-Arm Row", "Face Pull", "Reverse Fly", "Bicep Curl", "Hammer Curl", "Concentration Curl"]
    leg_movements = ["Squat", "Front Squat", "Goblet Squat", "Lunge", "Reverse Lunge", "Split Squat", "Cable Deadlift", "Romanian Deadlift", "Hip Abduction", "Hip Adduction", "Glute Kickback", "Bodyweight Squat"]
    core_movements = ["Cable Crunch", "Woodchopper", "Pallof Press", "Plank"]
    progress = {"Push": [], "Pull": [], "Legs": [], "Core": []}
    last_values = {"Push": 0, "Pull": 0, "Legs": 0, "Core": 0}
    dates = []
    if os.path.exists("workout_log.json"):
        with open("workout_log.json", "r") as f:
            log_data = json.load(f)
        for entry in log_data:
            date = entry["date"]
            dates.append(date)
            movements = entry["movements"]
            def average_1rm(movement_list):
                valid_1rms = []
                for m in movements:
                    if m in movement_list and "new_1rm" in movements[m]:
                        if movements[m]["new_1rm"] > 0:
                            valid_1rms.append(movements[m]["new_1rm"])
                return sum(valid_1rms) / len(valid_1rms) if valid_1rms else None
            push_avg = average_1rm(push_movements)
            pull_avg = average_1rm(pull_movements)
            legs_avg = average_1rm(leg_movements)
            core_avg = average_1rm(core_movements)
            progress["Push"].append(push_avg if push_avg is not None else last_values["Push"])
            progress["Pull"].append(pull_avg if pull_avg is not None else last_values["Pull"])
            progress["Legs"].append(legs_avg if legs_avg is not None else last_values["Legs"])
            progress["Core"].append(core_avg if core_avg is not None else last_values["Core"])
            if push_avg is not None: last_values["Push"] = push_avg
            if pull_avg is not None: last_values["Pull"] = pull_avg
            if legs_avg is not None: last_values["Legs"] = legs_avg
            if core_avg is not None: last_values["Core"] = core_avg
    else:
        if weights_dict:
            dates.append("Initial")
            progress["Push"].append(get_movement_1rm("Cable Chest Press", False))
            progress["Pull"].append(get_movement_1rm("Lat Pulldown", False))
            progress["Legs"].append(get_movement_1rm("Squat", False))
            progress["Core"].append(get_movement_1rm("Cable Crunch", False))
            last_values["Push"] = progress["Push"][0]
            last_values["Pull"] = progress["Pull"][0]
            last_values["Legs"] = progress["Legs"][0]
            last_values["Core"] = progress["Core"][0]
    return dates, progress

@app.route('/')
def welcome():
    load_user_data()
    load_workout_plans()
    dates, progress = calculate_progress_over_time()
    return render_template('welcome.html', weights_dict=weights_dict, progress=progress, dates=dates)

@app.route('/test', methods=['GET', 'POST'])
def test():
    global weights_dict, one_rm_dict, movement_1rm_dict, goal
    if request.method == 'POST':
        all_valid = True
        for exercise in exercises:
            weight_str = request.form.get(exercise)
            is_valid, result = validate_input(weight_str)
            if not is_valid:
                return render_template('test.html', error=f"{exercise}: {result}", exercises=exercises)
            weights_dict[exercise] = result
            one_rm_dict[exercise] = calculate_1rm(result, 5)
        if all_valid:
            goal = request.form.get('goal')
            user_options["duration"] = request.form.get('duration')
            movement_1rm_dict = {m: get_movement_1rm(m, False) if m in all_movements else 0 for m in all_movements + bodyweight_movements + stretches}
            save_user_data()
            return redirect(url_for('landing'))
    return render_template('test.html', exercises=exercises)

@app.route('/landing')
def landing():
    load_workout_plans()
    current_day = get_current_day()
    print(f"Landing page plans: {workout_plans[user_options['days_per_week']]}")
    return render_template('landing.html', plans=workout_plans[user_options["days_per_week"]], current_day=current_day)

@app.route('/workout/<path:day>', methods=['GET', 'POST'])
def workout(day):
    global feedback_data, movement_1rm_dict
    print(f"Version 1.7 - Entering workout route with day: '{day}'")
    day = day.replace("%20", " ").strip()
    print(f"Processed day: '{day}'")
    print(f"Days per week: {user_options['days_per_week']}")
    print(f"Available plans: {workout_plans[user_options['days_per_week']]}")
    try:
        load_workout_plans()
        if day not in workout_plans[user_options["days_per_week"]]:
            generate_weekly_plan()
            print(f"After regen: {workout_plans[user_options['days_per_week']]}")
            if day not in workout_plans[user_options["days_per_week"]]:
                return f"Workout not found for '{day}'. Available: {list(workout_plans[user_options['days_per_week']].keys())}", 404
        if request.method == 'POST':
            feedback_data = {}
            for movement in workout_plans[user_options["days_per_week"]][day]:
                feedback = request.form.get(f"feedback_{movement}")
                actual_weight = request.form.get(f"weight_{movement}")
                recommended_weight = float(request.form.get(f"rec_{movement}"))
                current_1rm = get_movement_1rm(movement)
                adjustment = {"Way Too Easy": 1.10, "Too Easy": 1.05, "Just Right": 1.0, "Too Hard": 0.95, "Way Too Hard": 0.90}
                new_1rm = current_1rm * adjustment.get(feedback, 1.0)
                if actual_weight:
                    is_valid, actual = validate_input(actual_weight)
                    if is_valid:
                        reps = 10 if goal == "Build Muscle" else 18 if goal == "Increase Endurance" else 12
                        new_1rm = calculate_1rm(actual * (2 if is_two_handle_movement(movement) else 1), reps)
                movement_1rm_dict[movement] = new_1rm
                feedback_data[movement] = {
                    "feedback": feedback,
                    "actual_weight": actual_weight,
                    "recommended_weight": recommended_weight,
                    "new_1rm": new_1rm
                }
            days = list(workout_plans[user_options["days_per_week"]].keys())
            current_day_idx = days.index(day) + 1
            next_day = (current_day_idx % user_options["days_per_week"]) + 1
            log_entry = {
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "day": day,
                "goal": goal,
                "duration": user_options["duration"],
                "movements": feedback_data
            }
            log_file = "workout_log.json"
            log_data = json.load(open(log_file, "r")) if os.path.exists(log_file) else []
            log_data.append(log_entry)
            with open(log_file, "w") as f:
                json.dump(log_data, f, indent=4)
            with open("current_day.txt", "w") as f:
                f.write(str(next_day))
            if current_day_idx == user_options["days_per_week"]:
                workout_plans[user_options["days_per_week"]] = {}
                generate_weekly_plan()
            save_user_data()
            return redirect(url_for('welcome'))
        percentage = 0.75 if goal == "Build Muscle" else 0.55 if goal == "Increase Endurance" else 0.65
        sets = 4 if goal == "Build Muscle" else 3
        reps = 10 if goal == "Build Muscle" else 18 if goal == "Increase Endurance" else 12
        focus = day.split(" - ")[1].split("/")[0].lower()
        warmups = {"push": ["Push-up", "Dips"], "chest": ["Push-up", "Dips"], "shoulders": ["Push-up", "Dips"],
                   "pull": ["Bodyweight Squat", "Plank"], "back": ["Bodyweight Squat", "Plank"],
                   "legs": ["Bodyweight Squat", "Dips"], "core": ["Plank", "Bodyweight Squat"], "arms": ["Push-up", "Dips"]}.get(focus, ["Push-up", "Bodyweight Squat"])
        cooldowns = random.sample(stretches, 2)
        movements = workout_plans[user_options["days_per_week"]][day]
        workout_data = []
        for movement in movements:
            movement_1rm = get_movement_1rm(movement)
            start_weight = math.ceil(movement_1rm * percentage)
            total_weight = start_weight if not is_two_handle_movement(movement) else start_weight * 2
            workout_data.append({"name": movement, "sets": sets, "reps": reps, "weight": total_weight, "two_handle": is_two_handle_movement(movement)})
        return render_template('workout.html', day=day, warmups=warmups, cooldowns=cooldowns, movements=workout_data, goal=goal)
    except Exception as e:
        print(f"Error in workout route: {str(e)}")
        return f"Server error: {str(e)}", 500

@app.route('/debug')
def debug():
    print("Debug route hit")
    return "Debug route working", 200

if __name__ == '__main__':
    print("Starting app.py version 1.7")
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
