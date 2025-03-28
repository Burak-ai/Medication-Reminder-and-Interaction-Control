from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import threading
import time

app = Flask(__name__)

users_medications = {}


drug_interactions_db = {

    ('Warfarin', 'Aspirin'): {
        'warning': 'Concurrent use may increase the risk of bleeding.',
        'severity': 'high',
        'advice': 'Consult your physician before using both drugs together.'
    },
    ('Lisinopril', 'Ibuprofen'): {
        'warning': 'Ibuprofen may reduce the blood pressure-lowering effect of Lisinopril and increase kidney risks.',
        'severity': 'medium',
        'advice': 'Use with caution and consult your healthcare provider.'
    },
    ('Simvastatin', 'Grapefruit Juice'): {
        'warning': 'Grapefruit juice can increase Simvastatin levels, raising the risk of side effects.',
        'severity': 'medium',
        'advice': 'Avoid grapefruit products while on Simvastatin.'
    },
    ('Metformin', 'Cimetidine'): {
        'warning': 'Cimetidine may increase blood levels of Metformin, potentially raising side effect risks.',
        'severity': 'low',
        'advice': 'Monitor blood sugar levels and consult your doctor if unusual symptoms occur.'
    },
    ('Warfarin', 'Amiodarone'): {
        'warning': 'Amiodarone may increase Warfarin effects, leading to an elevated bleeding risk.',
        'severity': 'high',
        'advice': 'Frequent INR monitoring is recommended if these drugs are used together.'
    },
    ('Digoxin', 'Amiodarone'): {
        'warning': 'Amiodarone may increase Digoxin levels, raising the risk of toxicity.',
        'severity': 'high',
        'advice': 'Monitor Digoxin levels closely and adjust the dose if necessary.'
    },
    ('Sildenafil', 'Nitroglycerin'): {
        'warning': 'Combined use can lead to severe hypotension.',
        'severity': 'high',
        'advice': 'Never use these medications together; seek medical advice for alternatives.'
    },
    ('ACE Inhibitors', 'Potassium Supplements'): {
        'warning': 'ACE inhibitors can increase potassium levels, and together with supplements, this may lead to hyperkalemia.',
        'severity': 'medium',
        'advice': 'Monitor potassium levels regularly.'
    },
    ('Omeprazole', 'Clopidogrel'): {
        'warning': 'Omeprazole may reduce the effectiveness of Clopidogrel.',
        'severity': 'medium',
        'advice': 'Consider alternative proton pump inhibitors if Clopidogrel is essential.'
    },
    # 20 Additional interactions
    ('Acetaminophen', 'Alcohol'): {
        'warning': 'Combined use may increase the risk of liver damage.',
        'severity': 'high',
        'advice': 'Avoid excessive alcohol consumption while taking acetaminophen.'
    },
    ('Fluoxetine', 'Phenelzine'): {
        'warning': 'Concurrent use may cause serotonin syndrome.',
        'severity': 'high',
        'advice': 'Never combine SSRIs with MAO inhibitors; seek alternative treatments.'
    },
    ('Metoprolol', 'Verapamil'): {
        'warning': 'May cause additive effects leading to bradycardia and hypotension.',
        'severity': 'medium',
        'advice': 'Monitor heart rate and blood pressure closely.'
    },
    ('Theophylline', 'Ciprofloxacin'): {
        'warning': 'Ciprofloxacin can increase theophylline levels, risking toxicity.',
        'severity': 'high',
        'advice': 'Monitor theophylline levels if these drugs are co-administered.'
    },
    ('ACE Inhibitors', 'NSAIDs'): {
        'warning': 'NSAIDs may diminish the antihypertensive effects of ACE inhibitors and risk kidney function.',
        'severity': 'medium',
        'advice': 'Use the lowest effective NSAID dose and monitor kidney function.'
    },
    ('Tetracycline', 'Dairy Products'): {
        'warning': 'Dairy products can interfere with the absorption of tetracycline.',
        'severity': 'low',
        'advice': 'Take tetracycline on an empty stomach or avoid dairy around dosing time.'
    },
    ('Ciprofloxacin', 'Tizanidine'): {
        'warning': 'Concomitant use may lead to severe hypotension.',
        'severity': 'high',
        'advice': 'Avoid this combination to prevent dangerous blood pressure drops.'
    },
    ('Valproate', 'Lamotrigine'): {
        'warning': 'Increased risk of rash and toxicity when these anticonvulsants are combined.',
        'severity': 'medium',
        'advice': 'Monitor for signs of skin reactions and adjust dosages carefully.'
    },
    ('Lithium', 'Diuretics'): {
        'warning': 'Diuretics can increase lithium levels, risking toxicity.',
        'severity': 'high',
        'advice': 'Monitor lithium levels frequently if diuretics are prescribed.'
    },
    ('Omeprazole', 'Methotrexate'): {
        'warning': 'Omeprazole may increase methotrexate toxicity by reducing its clearance.',
        'severity': 'medium',
        'advice': 'Consider alternative acid reducers or adjust methotrexate dosing as needed.'
    },
    ('Azithromycin', 'Simvastatin'): {
        'warning': 'Azithromycin may increase simvastatin levels, raising the risk of myopathy.',
        'severity': 'medium',
        'advice': 'Monitor for muscle pain or weakness during therapy.'
    },
    ('Ritonavir', "St. John's Wort"): {
        'warning': "St. John's Wort may reduce ritonavir levels by inducing liver enzymes.",
        'severity': 'medium',
        'advice': 'Avoid herbal supplements that affect liver enzymes when on ritonavir.'
    },
    ('Levothyroxine', 'Calcium Supplements'): {
        'warning': 'Calcium may decrease the absorption of levothyroxine.',
        'severity': 'low',
        'advice': 'Separate the dosing times of levothyroxine and calcium by at least 4 hours.'
    },
    ('Warfarin', 'Cranberry Juice'): {
        'warning': 'Cranberry juice may increase Warfarin effects, raising bleeding risk.',
        'severity': 'medium',
        'advice': 'Monitor INR levels closely if consuming cranberry products.'
    },
    ('Glimepiride', 'Alcohol'): {
        'warning': 'Alcohol may increase the risk of hypoglycemia with Glimepiride.',
        'severity': 'medium',
        'advice': 'Avoid excessive alcohol intake and monitor blood sugar levels.'
    },
    ('Clonazepam', 'Opiates'): {
        'warning': 'Combined use can lead to increased sedation and respiratory depression.',
        'severity': 'high',
        'advice': 'Use with extreme caution and under strict medical supervision.'
    },
    ('Zolpidem', 'Alcohol'): {
        'warning': 'The combination can lead to excessive sedation and impaired motor function.',
        'severity': 'medium',
        'advice': 'Avoid alcohol when taking zolpidem to reduce sedative effects.'
    },
    ('Diazepam', 'Erythromycin'): {
        'warning': 'Erythromycin may increase Diazepam levels, enhancing sedation.',
        'severity': 'medium',
        'advice': 'Monitor for signs of excessive sedation and adjust dosage if necessary.'
    },
    ('Prednisone', 'Non-selective Beta-blockers'): {
        'warning': 'May increase blood sugar levels and reduce beta-blocker efficacy.',
        'severity': 'medium',
        'advice': 'Monitor blood sugar and cardiovascular status closely.'
    },
    ('Bupropion', 'MAO Inhibitors'): {
        'warning': 'Concurrent use may trigger a hypertensive crisis.',
        'severity': 'high',
        'advice': 'Avoid combining these medications and seek alternatives if needed.'
    }
}

def get_advanced_interaction(drug1, drug2):
    """
    Check for advanced drug interactions between two drugs.
    Searches for the pair in both orders.
    """
    key = (drug1, drug2)
    if key in drug_interactions_db:
        return drug_interactions_db[key]
    key = (drug2, drug1)
    return drug_interactions_db.get(key)

def check_all_interactions(medications):
    """
    Check all pair combinations in a list of medications for potential drug interactions.
    Returns a list of detailed warnings.
    """
    warnings = []
    n = len(medications)
    for i in range(n):
        for j in range(i + 1, n):
            drug1 = medications[i]['drug']
            drug2 = medications[j]['drug']
            interaction = get_advanced_interaction(drug1, drug2)
            if interaction:
                warnings.append({
                    'drugs': (drug1, drug2),
                    'warning': interaction['warning'],
                    'severity': interaction['severity'],
                    'advice': interaction['advice']
                })
    return warnings

def ai_optimize_time(user_routine, drug_time):
    """
    Dummy AI optimization:
    Adjust the reminder time based on user routine.
    In a real application, analyze historical data and user habits.
    """
    return drug_time

def send_reminder(user_id, medication):
    """Simulate sending a reminder to the user."""
    print(f"Reminder for user {user_id}: Time to take {medication['drug']} "
          f"({medication.get('dosage', 'N/A')})")

def schedule_reminders(user_id):
    """
    A dummy scheduler to simulate reminder notifications.
    In production, consider using a robust scheduling system or push notifications.
    """
    def reminder_loop():
        while True:
            now = datetime.now()
            meds = users_medications.get(user_id, [])
            for med in meds:
                reminder_time = med['time']
                if now <= reminder_time < now + timedelta(minutes=1):
                    send_reminder(user_id, med)
            time.sleep(60)  # Check every minute

    t = threading.Thread(target=reminder_loop, daemon=True)
    t.start()

@app.route('/add_medication', methods=['POST'])
def add_medication():
    """
    Endpoint to add a medication.
    Expects JSON data with:
      - user_id: unique identifier for the user
      - drug: medication name (e.g., "Warfarin")
      - dosage: medication dosage (optional)
      - time: reminder time in ISO format (e.g., "2025-03-28T15:30:00")
      - user_routine: optional data for AI optimization
    """
    data = request.get_json()
    user_id = data.get('user_id')
    drug = data.get('drug')
    dosage = data.get('dosage')
    time_str = data.get('time')
    user_routine = data.get('user_routine', {})

    try:
        reminder_time = datetime.fromisoformat(time_str)
    except Exception:
        return jsonify({"error": "Invalid time format. Use ISO format."}), 400

    optimized_time = ai_optimize_time(user_routine, reminder_time)

    medication = {
        'drug': drug,
        'dosage': dosage,
        'time': optimized_time
    }

    if user_id in users_medications:
        users_medications[user_id].append(medication)
    else:
        users_medications[user_id] = [medication]
        schedule_reminders(user_id)

    interactions = check_all_interactions(users_medications[user_id])
    return jsonify({
        "message": "Medication added successfully.",
        "optimized_time": optimized_time.isoformat(),
        "interaction_warnings": interactions
    })

@app.route('/get_medications', methods=['GET'])
def get_medications():
    """
    Endpoint to retrieve all medications for a given user.
    Query Parameter: user_id
    """
    user_id = request.args.get('user_id')
    meds = users_medications.get(user_id, [])
    for med in meds:
        med['time'] = med['time'].isoformat()
    return jsonify(meds)

@app.route('/check_interactions', methods=['POST'])
def check_interactions():
    """
    Endpoint to check interactions for a list of medications.
    Expects JSON data with key "medications", a list of medication dictionaries.
    """
    data = request.get_json()
    medications = data.get('medications', [])
    interactions = check_all_interactions(medications)
    return jsonify(interactions)

@app.route('/')
def index():
    """Simple index route to verify the server is running."""
    return "Advanced Medication Reminder App is Running!"

if __name__ == '__main__':
    app.run(debug=True)
