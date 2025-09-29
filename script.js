document.getElementById("tripForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const origin = document.getElementById("origin").value;
  const destination = document.getElementById("destination").value;
  const days = document.getElementById("days").value;
  const budget = document.getElementById("budget").value;
  const interests = Array.from(document.querySelectorAll("input[type=checkbox]:checked")).map(c => c.value);

  const inputData = { origin, destination, days, budget, interests };

  try {
    const response = await fetch("http://127.0.0.1:5000/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(inputData)
    });
    const result = await response.json();
    const itinerary = result.itinerary;

    // Build HTML output
    let html = `<h3>Trip Summary</h3><p>${itinerary.summary}</p>`;
    html += `<h3>Transport Options</h3><ul>`;
    itinerary.transport.forEach(t => {
      html += `<li>${t.mode}: ${t.cost ? '₹'+t.cost : 'Not available'}</li>`;
    });
    html += `</ul>`;
    itinerary.daily_plan.forEach(day => {
      html += `<h4>Day ${day.day}</h4>`;
      html += `<p>Morning: ${day.morning}</p>`;
      html += `<p>Afternoon: ${day.afternoon}</p>`;
      html += `<p>Evening: ${day.evening}</p>`;
      html += `<p>Cost: ₹${day.cost}</p>`;
    });
    html += `<h3>Total Cost: ₹${itinerary.total_cost}</h3>`;
    html += `<p>${itinerary.notes}</p>`;

    document.getElementById("output").innerHTML = html;

  } catch(err) {
    document.getElementById("output").textContent = "Failed to connect: " + err;
  }
});
