async function fetchJSON(url, token) {
  const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

document.getElementById("loadBtn").addEventListener("click", async () => {
  const token = document.getElementById("token").value.trim();
  const overview = await fetchJSON("/dashboard/overview", token);
  document.getElementById("active").innerText = overview.active_students;
  document.getElementById("cohorts").innerText = overview.cohorts;
  document.getElementById("pnp").innerText = overview.avg_pnp;
  document.getElementById("pubs").innerText = overview.publications;

  const cohortData = await fetchJSON("/dashboard/cohorts", token);
  const labels = cohortData.map(c => c.cohort);
  const pnp = cohortData.map(c => c.pnp);
  new Chart(document.getElementById("cohortChart"), {
    type: "bar",
    data: { labels, datasets: [{ label: "PNP", data: pnp }] }
  });
});
