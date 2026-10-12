
from flask import Flask, render_template, request, jsonify
import pandas as pd
import math
import os

app = Flask(__name__)
DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "routes.csv")
df = pd.read_csv(DATA_PATH)

# Columns used as route attributes in the UI
ATTRIBUTES = [
    "Distance_KM","Travel_Time_Hours","Average_Speed_KMPH","Fuel_Consumption_Liters",
    "Fuel_Cost_INR","Toll_Cost_INR","Total_Travel_Cost_INR","Traffic_Level",
    "Congestion_Index","Road_Condition","Road_Type","Highway_Percentage",
    "Number_of_Tolls","Number_of_Stops","Weather_Condition","Accident_Risk",
    "Route_Safety_Score","CO2_Emission_KG","Peak_Hour_Delay_Min","Alternative_Routes",
    "Scenic_Score","Route_Availability","Distance_Category","Time_Category",
    "Source_State","Destination_State","Overall_Route_Score"
]

def clean(v):
    if pd.isna(v):
        return None
    if isinstance(v, (float, int)):
        return float(v) if isinstance(v, float) else int(v)
    return str(v)

def row_to_dict(row):
    return {k: clean(row[k]) for k in ATTRIBUTES if k in row}

def find_route(src, dst):
    # First try exact direction. If absent, try reverse because the sample
    # dataset is synthetic and not every pair is guaranteed in both directions.
    m = df[(df.Source_City == src) & (df.Destination_City == dst)]
    if len(m):
        return m.iloc[0], False
    m = df[(df.Source_City == dst) & (df.Destination_City == src)]
    if len(m):
        r = m.iloc[0].copy()
        # swap directional fields
        r["Source_City"], r["Destination_City"] = src, dst
        r["Source_State"], r["Destination_State"] = state_of(src), state_of(dst)
        return r, True
    return None, False

def state_of(city):
    m = df[(df.Source_City == city) | (df.Destination_City == city)]
    if len(m):
        r=m.iloc[0]
        if r["Source_City"] == city:
            return r["Source_State"]
        return r["Destination_State"]
    return ""

def numeric_cost(row, mode):
    # A normalized weighted cost. Lower is better.
    dist=float(row["Distance_KM"])
    time=float(row["Travel_Time_Hours"])
    fuel=float(row["Fuel_Cost_INR"])
    toll=float(row["Toll_Cost_INR"])
    cong=float(row["Congestion_Index"])
    safety=float(row["Route_Safety_Score"])
    co2=float(row["CO2_Emission_KG"])
    delay=float(row["Peak_Hour_Delay_Min"])
    score=float(row["Overall_Route_Score"])

    if mode == "distance":
        return dist
    if mode == "time":
        return time
    if mode == "cost":
        return fuel + toll
    if mode == "safety":
        return (10.0-safety)*100 + cong*100 + delay
    if mode == "eco":
        return co2 + fuel*0.03
    # Best overall: normalized multi-criteria score. Values are relative,
    # so no single raw attribute dominates.
    return (
        dist/100.0 + time*3.0 + fuel/500.0 + toll/100.0 +
        cong*100.0 + (10.0-safety)*12.0 + co2/20.0 +
        delay/5.0 - score*15.0
    )

def build_matrix(cities, mode):
    n=len(cities)
    matrix=[[math.inf]*n for _ in range(n)]
    details=[[None]*n for _ in range(n)]
    for i in range(n):
        matrix[i][i]=0.0
        for j in range(n):
            if i==j: continue
            row,_=find_route(cities[i],cities[j])
            if row is not None:
                matrix[i][j]=numeric_cost(row,mode)
                details[i][j]=row_to_dict(row)
    return matrix,details

def bitmask_tsp(matrix):
    n=len(matrix)
    if n==1:
        return [0], 0.0, 0, []
    N=1<<n
    INF=float("inf")
    dp=[[INF]*n for _ in range(N)]
    parent=[[-1]*n for _ in range(N)]
    dp[1][0]=0.0
    states=[]
    for mask in range(N):
        if not (mask & 1): continue
        for u in range(n):
            if not (mask & (1<<u)) or dp[mask][u] == INF:
                continue
            for v in range(n):
                if mask & (1<<v) or matrix[u][v] == INF:
                    continue
                nm=mask | (1<<v)
                new=dp[mask][u]+matrix[u][v]
                if new < dp[nm][v]:
                    dp[nm][v]=new
                    parent[nm][v]=u
                    states.append({
                        "mask": format(nm, f"0{n}b"),
                        "current": v,
                        "cost": round(new,3)
                    })
    full=N-1
    best=INF
    last=-1
    for u in range(1,n):
        if dp[full][u] == INF or matrix[u][0] == INF: continue
        total=dp[full][u]+matrix[u][0]
        if total<best:
            best=total; last=u
    if last==-1:
        return None,None,len(states),states
    path=[]
    mask=full; u=last
    while u!=-1:
        path.append(u)
        p=parent[mask][u]
        mask ^= (1<<u)
        u=p
    path=path[::-1]
    return path+[0],best,len(states),states[-100:]

@app.route("/")
def index():
    cities=sorted(set(df.Source_City.astype(str)) | set(df.Destination_City.astype(str)))
    return render_template("index.html", cities=cities)

@app.get("/api/cities")
def api_cities():
    return jsonify(sorted(set(df.Source_City.astype(str)) | set(df.Destination_City.astype(str))))

@app.post("/api/plan")
def plan():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid request. Please refresh the page and try again."}), 400

    start = data.get("start")
    selected = data.get("cities", [])
    mode = data.get("mode", "overall")
    allowed_modes = {"overall", "distance", "time", "cost", "safety", "eco"}
    available_cities = set(df.Source_City.astype(str)) | set(df.Destination_City.astype(str))

    if not isinstance(start, str) or start not in available_cities:
        return jsonify({"error": "Choose a valid starting city."}), 400
    if not isinstance(selected, list) or not selected:
        return jsonify({"error": "Select at least one destination city."}), 400
    if mode not in allowed_modes:
        return jsonify({"error": "Choose a valid optimization method."}), 400
    if any(not isinstance(city, str) or city not in available_cities for city in selected):
        return jsonify({"error": "One or more destination cities are invalid."}), 400

    # Deduplicate selections and exclude the starting city from destinations.
    cities = [start] + list(dict.fromkeys(c for c in selected if c != start))
    if len(cities)<2:
        return jsonify({"error":"Choose at least one destination."}),400
    if len(cities)>10:
        return jsonify({"error":"For exact Bitmask DP, select at most 9 destinations (10 cities including the start)."}),400

    matrix,details=build_matrix(cities,mode)
    path,cost,state_count,states=bitmask_tsp(matrix)
    if path is None:
        return jsonify({"error":"A complete tour could not be formed from the available route records. Try a different city selection."}),400

    legs=[]
    total_distance=total_time=total_fuel=total_toll=0.0
    scores=[]
    for a,b in zip(path[:-1],path[1:]):
        d=details[a][b]
        if d is None:
            return jsonify({"error":f"Missing route data for {cities[a]} → {cities[b]}."}),400
        legs.append({"from":cities[a],"to":cities[b],"attributes":d})
        total_distance+=float(d["Distance_KM"])
        total_time+=float(d["Travel_Time_Hours"])
        total_fuel+=float(d["Fuel_Cost_INR"])
        total_toll+=float(d["Toll_Cost_INR"])
        scores.append(float(d["Overall_Route_Score"]))

    return jsonify({
        "cities":cities,
        "route":[cities[i] for i in path],
        "objective":mode,
        "minimum_total_route_cost":round(cost,2),
        "total_distance_km":round(total_distance,1),
        "total_travel_time_hours":round(total_time,2),
        "fuel_cost_inr":round(total_fuel,2),
        "toll_cost_inr":round(total_toll,2),
        "average_route_score":round(sum(scores)/len(scores),2),
        "dp_states_processed":state_count,
        "legs":legs,
        "states":states
    })

if __name__ == "__main__":
    app.run(debug=False)
