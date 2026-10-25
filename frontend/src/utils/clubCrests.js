const base = `${import.meta.env.BASE_URL}crests/monochrome/`;
const assets = {
  "real madrid": "real-madrid.svg",
  "real madrid cf": "real-madrid.svg",
  "real madrid club de futbol": "real-madrid.svg",
  "manchester united": "manchester-united.svg",
  "manchester united fc": "manchester-united.svg",
  "man united": "manchester-united.svg",
  "man utd": "manchester-united.svg",
  "fc barcelona": "fc-barcelona.svg",
  barcelona: "fc-barcelona.svg",
  arsenal: "arsenal.svg",
  "arsenal fc": "arsenal.svg",
  "manchester city": "manchester-city.svg",
  "manchester city fc": "manchester-city.svg",
  "man city": "manchester-city.svg",
  newcastle: "newcastle-united.svg",
  "newcastle united": "newcastle-united.svg",
  "newcastle united fc": "newcastle-united.svg",
  "fc bayern munchen": "bayern-munich.svg",
  "bayern munich": "bayern-munich.svg",
  "bayern munchen": "bayern-munich.svg",
  juventus: "juventus.svg",
  "juventus fc": "juventus.svg",
};

export function monochromeCrestFor(teamName) {
  const key = String(teamName || "")
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/\./g, "")
    .replace(/\s+/g, " ")
    .trim();
  return assets[key]
    ? `${base}${assets[key].replace(".svg", "-outline.svg")}`
    : null;
}
