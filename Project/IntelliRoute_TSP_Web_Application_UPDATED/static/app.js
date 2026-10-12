
let cities = [];
const selected = new Set();
const $ = id => document.getElementById(id);

async function init() {
  try {
    const response = await fetch('/api/cities');
    if (!response.ok) throw new Error('Could not load the city list. Refresh the page and try again.');
    cities = await response.json();
    const start = $('start');
    start.replaceChildren(new Option('Choose a starting city', ''));
    cities.forEach(city => start.add(new Option(city, city)));
    start.addEventListener('change', renderCities);
    renderCities();
  } catch (error) {
    $('error').textContent = error.message;
  }
}

function renderCities() {
  const box = $('cities');
  box.replaceChildren();
  const start = $('start').value;
  cities.filter(city => city !== start).forEach(city => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'city' + (selected.has(city) ? ' active' : '');
    button.textContent = city;
    button.setAttribute('aria-pressed', String(selected.has(city)));
    button.onclick = () => {
      if (selected.has(city)) selected.delete(city);
      else selected.add(city);
      renderCities();
    };
    box.appendChild(button);
  });
  $('count').textContent = `${selected.size} selected`;
}
$('planBtn').onclick=async()=>{
  $('error').textContent='';
  const start=$('start').value;
  if (!start) { $('error').textContent = 'Please choose a starting city.'; return; }
  if (selected.size < 1) { $('error').textContent = 'Please select at least one destination city.'; return; }
  $('loading').classList.remove('hidden');$('results').classList.add('hidden');
  try{
    const res=await fetch('/api/plan',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({start,cities:[...selected],mode:$('mode').value})});
    const data=await res.json();
    if(!res.ok) throw new Error(data.error||'Unable to calculate route.');
    showResults(data);
  } catch (e) { $('error').textContent = e.message || 'Unable to calculate the route. Please try again.'; }
  finally{$('loading').classList.add('hidden')}
};
function money(x){return '₹'+Number(x).toLocaleString('en-IN',{maximumFractionDigits:2})}
function showResults(d){
  $('results').classList.remove('hidden');
  $('route').innerHTML=d.route.map((x,i)=>i<d.route.length-1?`<span>${x}</span> <b>→</b> `:`<span>${x}</span>`).join('');
  $('distance').textContent=d.total_distance_km.toLocaleString()+' km';
  $('time').textContent=d.total_travel_time_hours+' h';
  $('score').textContent=d.average_route_score+'/10';
  $('dpstates').textContent=d.dp_states_processed;
  $('cost').textContent=Number(d.minimum_total_route_cost).toLocaleString('en-IN',{maximumFractionDigits:2});
  $('fuel').textContent=money(d.fuel_cost_inr);$('toll').textContent=money(d.toll_cost_inr);
  const labels={
    Distance_KM:'Distance',Travel_Time_Hours:'Travel Time',Average_Speed_KMPH:'Average Speed',
    Fuel_Consumption_Liters:'Fuel Consumption',Fuel_Cost_INR:'Fuel Cost',Toll_Cost_INR:'Toll Cost',
    Total_Travel_Cost_INR:'Total Travel Cost',Traffic_Level:'Traffic Level',Congestion_Index:'Congestion',
    Road_Condition:'Road Condition',Road_Type:'Road Type',Highway_Percentage:'Highway %',
    Number_of_Tolls:'Tolls',Number_of_Stops:'Stops',Weather_Condition:'Weather',
    Accident_Risk:'Accident Risk',Route_Safety_Score:'Safety Score',CO2_Emission_KG:'CO₂ Emission',
    Peak_Hour_Delay_Min:'Peak Delay',Alternative_Routes:'Alternative Routes',Scenic_Score:'Scenic Score',
    Route_Availability:'Availability',Distance_Category:'Distance Category',Time_Category:'Time Category',
    Source_State:'Source State',Destination_State:'Destination State',Overall_Route_Score:'Overall Score'
  };
  $('legs').innerHTML=d.legs.map(l=>`<div class="leg"><div class="leg-head"><span>${l.from}</span><span>→ ${l.to}</span></div><div class="attrs">${
    Object.entries(l.attributes).filter(([k])=>labels[k]).map(([k,v])=>`<div class="attr"><small>${labels[k]}</small><b>${v}</b></div>`).join('')
  }</div></div>`).join('');
  $('states').innerHTML=d.states.map(s=>`<tr><td>${s.mask}</td><td>${s.current}</td><td>${s.cost}</td></tr>`).join('');
  window.scrollTo({top:$('results').offsetTop-70,behavior:'smooth'});
}
init();
