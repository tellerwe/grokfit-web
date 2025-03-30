# ... (all previous imports and functions unchanged up to routes) ...

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
    print(f"Version 1.8 - Entering workout route with day: '{day}'")
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
    print("Starting app.py version 1.8")
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
